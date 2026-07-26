import joblib
import numpy as np
import random
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
    MODEL_DIR,
    RANDOM_STATE,
    SVM_C,
    SVM_GAMMA,
    SVM_KERNEL,
    SVM_PROBABILITY,
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
                    SVC(kernel=SVM_KERNEL,
                        C=SVM_C,
                        gamma=SVM_GAMMA,
                        probability=SVM_PROBABILITY,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )

    def load_images(self, writer_id):

        writer_folder = DATASET_DIR / "signatures" / f"signatures_{writer_id}"

        if not writer_folder.exists():
            raise FileNotFoundError(f"Folder not found:\n{writer_folder}")

        genuine = sorted(writer_folder.glob(f"original_{writer_id}_*.png"))
        forged = sorted(writer_folder.glob(f"forgeries_{writer_id}_*.png"))

        if not genuine:
            raise ValueError("No genuine signatures found.")

        if not forged:
            raise ValueError("No forged signatures found.")

        impostors = []

        for other_writer in range(1, 56):

            if other_writer == writer_id:
                continue

            other_folder = DATASET_DIR / "signatures" / f"signatures_{other_writer}"

            other_genuine = sorted(
                other_folder.glob(f"original_{other_writer}_*.png")
            )

            impostors.extend(random.sample(other_genuine, 5))

        return genuine, forged, impostors

    def prepare_dataset(self, writer_id):

        genuine, forged, impostors = self.load_images(writer_id)

        X = []
        y = []

        print(f"\nProcessing Writer {writer_id}...\n")

        for image_path in genuine:

            image, _ = self.preprocessor.process(str(image_path))
            features = self.extractor.extract_hog(image)

            X.append(features)
            y.append(1)

        for image_path in forged:

            image, _ = self.preprocessor.process(str(image_path))
            features = self.extractor.extract_hog(image)

            X.append(features)
            y.append(0)
        for image_path in impostors:

            image, _ = self.preprocessor.process(str(image_path))
            features = self.extractor.extract_hog(image)

            X.append(features)
            y.append(0)
        X = np.array(X)
        y = np.array(y)

        print(f"Samples  : {len(X)}")
        print(f"Features : {X.shape[1]}")

        return X, y

    def split_dataset(self, X, y):

        return train_test_split(
            X,
            y,
            test_size=0.2,
            stratify=y,
            random_state=RANDOM_STATE,
        )

    def cross_validate(self, X, y):

        cv = StratifiedKFold(
            n_splits=5,
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
            print(f"Fold {i} : {score:.4f}")

        print(f"\nMean Accuracy : {scores.mean():.4f}")
        print(f"Std Deviation : {scores.std():.4f}")

        return scores

    def tune_model(self, X_train, y_train):

        parameter_grid = {
            "svm__kernel": ["linear", "rbf"],
            "svm__C": [0.1, 1, 10, 50, 100],
            "svm__gamma": ["scale", 0.01, 0.001],
        }

        search = GridSearchCV(
            estimator=self.model,
            param_grid=parameter_grid,
            cv=5,
            scoring="accuracy",
            n_jobs=-1,
            verbose=1,
        )

        print("\nSearching for best parameters...\n")

        search.fit(X_train, y_train)

        print("\nBest Parameters")
        print(search.best_params_)

        print(f"\nBest CV Accuracy : {search.best_score_:.4f}")

        self.model = search.best_estimator_

        return self.model

    def evaluate(self, X_test, y_test):

        predictions = self.model.predict(X_test)

        report = classification_report(
            y_test,
            predictions,
            output_dict=True
        )

        return {
            "accuracy": accuracy_score(y_test, predictions),
            "precision": report["weighted avg"]["precision"],
            "recall": report["weighted avg"]["recall"],
            "f1_score": report["weighted avg"]["f1-score"],
            "confusion_matrix": confusion_matrix(
                y_test,
                predictions
            )
        }

    def save_model(self, writer_id):

        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        model_path = MODEL_DIR / f"writer_{writer_id}.pkl"

        joblib.dump(self.model, model_path)

        return model_path   

    def train(self, writer_id):

        X, y = self.prepare_dataset(writer_id)

        X_train, X_test, y_train, y_test = self.split_dataset(X, y)

        self.tune_model(X_train, y_train)

        self.model.fit(X_train, y_train)

        metrics = self.evaluate(X_test, y_test)

        model_path = self.save_model(writer_id)

        return {
            "writer_id": writer_id,
            "model_path": str(model_path),
            "metrics": metrics
        }  

if __name__ == "__main__":

    trainer = SignatureTrainer()

    result = trainer.train(1)

    print(result)