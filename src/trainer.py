
import joblib
import numpy as np
import random

from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.config import (
    DATASET_DIR,
    RANDOM_STATE,
    SVM_C,
    SVM_GAMMA,
    SVM_KERNEL,
    SVM_PROBABILITY,
    TOTAL_WRITERS,
    CEDAR_MODELS_DIR,
    USER_MODELS_DIR,
    USER_DATA_DIR,
)

from src.preprocessing import SignaturePreprocessor
from src.feature_extractor import FeatureExtractor


class SignatureTrainer:
    """Train a writer-dependent signature verification model."""

    def __init__(self):
        self.preprocessor = SignaturePreprocessor(debug=False)
        self.extractor = FeatureExtractor()

        self.model = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "svm",
                    SVC(
                        kernel=SVM_KERNEL,
                        C=SVM_C,
                        gamma=SVM_GAMMA,
                        probability=SVM_PROBABILITY,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )

    # ---------------------------------------------------------
    # Helper: collect genuine CEDAR images for one writer
    # ---------------------------------------------------------
    def _get_cedar_genuine_images(self, writer_id):
        writer_folder = (
            DATASET_DIR / "signatures" / f"signatures_{writer_id}"
        )

        if not writer_folder.is_dir():
            return []

        return sorted(
            writer_folder.glob(f"original_{writer_id}_*.png")
        )

    # ---------------------------------------------------------
    # Load CEDAR images for a writer
    # ---------------------------------------------------------
    def load_cedar_images(self, writer_id):
        if not 1 <= writer_id <= TOTAL_WRITERS:
            raise ValueError(
                f"Writer ID must be between 1 and {TOTAL_WRITERS}."
            )

        writer_folder = (
            DATASET_DIR / "signatures" / f"signatures_{writer_id}"
        )

        if not writer_folder.is_dir():
            raise FileNotFoundError(
                f"Writer folder not found: {writer_folder}"
            )

        genuine = sorted(
            writer_folder.glob(f"original_{writer_id}_*.png")
        )

        forged = sorted(
            writer_folder.glob(f"forgeries_{writer_id}_*.png")
        )

        if len(genuine) < 2:
            raise ValueError(
                f"Writer {writer_id} needs at least 2 genuine "
                "signatures for training and testing."
            )

        if not forged:
            raise ValueError(
                f"No forged signatures found for writer {writer_id}."
            )

        impostors = []
        rng = random.Random(RANDOM_STATE)

        for other_writer in range(1, TOTAL_WRITERS + 1):
            if other_writer == writer_id:
                continue

            other_genuine = self._get_cedar_genuine_images(
                other_writer
            )

            # Avoid random.sample errors for small or missing folders.
            if len(other_genuine) < 5:
                continue

            impostors.extend(
                rng.sample(other_genuine, 5)
            )

        if not impostors:
            raise ValueError(
                "No impostor samples could be collected from CEDAR. "
                "Check the dataset folders and genuine image files."
            )

        return genuine, forged, impostors

    # ---------------------------------------------------------
    # Load images for a registered user
    # ---------------------------------------------------------
    def load_user_images(self, username):
        username = username.strip().lower()

        genuine_folder = USER_DATA_DIR / username / "genuine"

        if not genuine_folder.is_dir():
            raise FileNotFoundError(
                f"No signatures found for user '{username}'."
            )

        genuine = []

        for pattern in ("*.png", "*.jpg", "*.jpeg"):
            genuine.extend(genuine_folder.glob(pattern))

        genuine = sorted(genuine)

        if len(genuine) < 2:
            raise ValueError(
                "At least 2 genuine signatures are required "
                "to split data into training and testing sets."
            )

        impostors = []
        rng = random.Random(RANDOM_STATE)

        for writer in range(1, TOTAL_WRITERS + 1):
            images = self._get_cedar_genuine_images(writer)

            # Skip writers that do not have enough images.
            if len(images) < 5:
                continue

            impostors.extend(
                rng.sample(images, 5)
            )

        if not impostors:
            raise ValueError(
                "No impostor samples could be collected from CEDAR. "
                "Check the CEDAR dataset before training a user model."
            )

        # Registered users do not have their own forged samples.
        return genuine, [], impostors

    # ---------------------------------------------------------
    # Extract HOG features and prepare labels
    # 1 = genuine, 0 = forged or impostor
    # ---------------------------------------------------------
    def prepare_dataset(self, genuine, forged, impostors):
        if not genuine:
            raise ValueError("No genuine signatures were provided.")

        if not forged and not impostors:
            raise ValueError(
                "At least one negative sample is required."
            )

        X = []
        y = []

        print("\nExtracting features...\n")

        def add_images(image_paths, label, category):
            for image_path in image_paths:
                try:
                    image, _ = self.preprocessor.process(
                        str(image_path)
                    )

                    features = self.extractor.extract_hog(image)

                    X.append(features)
                    y.append(label)

                except (ValueError, FileNotFoundError) as exc:
                    print(
                        f"Skipping invalid {category} image "
                        f"{image_path}: {exc}"
                    )

        add_images(genuine, 1, "genuine")
        add_images(forged, 0, "forged")
        add_images(impostors, 0, "impostor")

        if not X:
            raise ValueError(
                "No valid signature features could be extracted."
            )

        X = np.asarray(X)
        y = np.asarray(y)

        classes, counts = np.unique(y, return_counts=True)

        if len(classes) != 2:
            raise ValueError(
                "Training requires both genuine and negative samples."
            )

        if np.min(counts) < 2:
            raise ValueError(
                "At least 2 valid samples per class are required "
                "for stratified training and testing."
            )

        print(f"Samples  : {len(X)}")
        print(f"Features : {X.shape[1]}")
        print(f"Genuine  : {int(np.sum(y == 1))}")
        print(f"Negative : {int(np.sum(y == 0))}")

        return X, y

    # ---------------------------------------------------------
    # Split dataset into training and testing sets
    # ---------------------------------------------------------
    def split_dataset(self, X, y):
        return train_test_split(
            X,
            y,
            test_size=0.2,
            stratify=y,
            random_state=RANDOM_STATE,
        )

    # ---------------------------------------------------------
    # Cross-validation
    # ---------------------------------------------------------
    def cross_validate(self, X, y):
        _, counts = np.unique(y, return_counts=True)

        n_splits = min(5, int(np.min(counts)))

        if n_splits < 2:
            raise ValueError(
                "Not enough samples per class for cross-validation."
            )

        cv = StratifiedKFold(
            n_splits=n_splits,
            shuffle=True,
            random_state=RANDOM_STATE,
        )

        scores = cross_val_score(
            self.model,
            X,
            y,
            cv=cv,
            scoring="accuracy",
        )

        print("\nCross Validation Accuracy")

        for i, score in enumerate(scores, start=1):
            print(f"Fold {i}: {score:.4f}")

        print(f"\nMean Accuracy: {scores.mean():.4f}")
        print(f"Std Deviation: {scores.std():.4f}")

        return scores

    # ---------------------------------------------------------
    # Hyperparameter tuning
    # ---------------------------------------------------------
    def tune_model(self, X_train, y_train):
        _, counts = np.unique(y_train, return_counts=True)

        cv_folds = min(5, int(np.min(counts)))

        if cv_folds < 2:
            raise ValueError(
                "Not enough training samples per class "
                "for hyperparameter tuning."
            )

        parameter_grid = {
            "svm__kernel": ["linear", "rbf"],
            "svm__C": [0.1, 1, 10, 50, 100],
            "svm__gamma": ["scale", 0.01, 0.001],
        }

        cv = StratifiedKFold(
            n_splits=cv_folds,
            shuffle=True,
            random_state=RANDOM_STATE,
        )

        search = GridSearchCV(
            estimator=self.model,
            param_grid=parameter_grid,
            cv=cv,
            scoring="accuracy",
            n_jobs=-1,
            verbose=1,
        )

        print("\nSearching for best parameters...\n")

        search.fit(X_train, y_train)

        print("\nBest Parameters")
        print(search.best_params_)

        print(
            f"\nBest CV Accuracy: {search.best_score_:.4f}"
        )

        self.model = search.best_estimator_

        return self.model

    # ---------------------------------------------------------
    # Evaluate trained model
    # ---------------------------------------------------------
    def evaluate(self, X_test, y_test):
        predictions = self.model.predict(X_test)

        report = classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        )

        return {
            "accuracy": float(
                accuracy_score(y_test, predictions)
            ),
            "precision": float(
                report["weighted avg"]["precision"]
            ),
            "recall": float(
                report["weighted avg"]["recall"]
            ),
            "f1_score": float(
                report["weighted avg"]["f1-score"]
            ),
            "confusion_matrix": confusion_matrix(
                y_test,
                predictions,
                labels=[0, 1],
            ),
        }

    # ---------------------------------------------------------
    # Save trained model
    # ---------------------------------------------------------
    def save_model(self, model_name, user_model=False):
        if user_model:
            USER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
            model_path = USER_MODELS_DIR / f"{model_name}.pkl"
        else:
            CEDAR_MODELS_DIR.mkdir(parents=True, exist_ok=True)
            model_path = CEDAR_MODELS_DIR / f"{model_name}.pkl"

        joblib.dump(self.model, model_path)

        print(f"\nModel saved to: {model_path}")

        return model_path

    # ---------------------------------------------------------
    # Train a CEDAR writer model
    # ---------------------------------------------------------
    def train(self, writer_id):
        genuine, forged, impostors = self.load_cedar_images(
            writer_id
        )

        X, y = self.prepare_dataset(
            genuine,
            forged,
            impostors,
        )

        X_train, X_test, y_train, y_test = self.split_dataset(
            X, y
        )

        self.tune_model(X_train, y_train)

        self.model.fit(X_train, y_train)

        metrics = self.evaluate(X_test, y_test)

        model_path = self.save_model(
            f"writer_{writer_id}"
        )

        return {
            "writer_id": writer_id,
            "model_path": str(model_path),
            "metrics": metrics,
        }

    # ---------------------------------------------------------
    # Train a registered user's model
    # ---------------------------------------------------------
    def train_user(self, username):
        username = username.strip().lower()

        genuine, forged, impostors = self.load_user_images(
            username
        )

        X, y = self.prepare_dataset(
            genuine,
            forged,
            impostors,
        )

        X_train, X_test, y_train, y_test = self.split_dataset(
            X, y
        )

        self.tune_model(X_train, y_train)

        self.model.fit(X_train, y_train)

        metrics = self.evaluate(X_test, y_test)

        model_path = self.save_model(
            username,
            user_model=True,
        )

        return {
            "username": username,
            "model_path": str(model_path),
            "metrics": metrics,
        }


if __name__ == "__main__":
    trainer = SignatureTrainer()

    result = trainer.train(1)

    print("\nTraining Result:")
    print(result)
