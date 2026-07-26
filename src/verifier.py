import joblib
import numpy as np

from src.config import MODEL_DIR
from src.preprocessing import SignaturePreprocessor
from src.feature_extractor import FeatureExtractor

class SignatureVerifier:
    """Verify signatures using a trained writer-specific model."""

    def __init__(self):

        self.preprocessor = SignaturePreprocessor(debug=False)
        self.extractor = FeatureExtractor()

        self.model = None
        self.writer_id = None

    def load_model(self, writer_id):

        model_path = MODEL_DIR / f"writer_{writer_id}.pkl"

        if not model_path.exists():
            raise FileNotFoundError(
                f"No trained model found for writer {writer_id}."
            )

        self.model = joblib.load(model_path)
        self.writer_id = writer_id

    def extract_features(self, image_path):

        image, _ = self.preprocessor.process(str(image_path))

        features = self.extractor.extract_hog(image)

        return features.reshape(1, -1)
    def predict_label(self, image_path):

        if self.model is None:
            raise RuntimeError("Model not loaded.")

        features = self.extract_features(image_path)

        prediction = int(self.model.predict(features)[0])

        probabilities = self.model.predict_proba(features)[0]

        confidence = float(np.max(probabilities))

        return {
            "label": prediction,
            "confidence": confidence,
            "probabilities": probabilities
        }
    def predict(self, image_path):

        result = self.predict_label(image_path)

        return {
            "prediction": (
                "Genuine"
                if result["label"] == 1
             else "Forged"
            ),
            "confidence": result["confidence"],
            "probabilities": {
                "forged": float(result["probabilities"][0]),
                "genuine": float(result["probabilities"][1])
            }
        }


if __name__ == "__main__":

    verifier = SignatureVerifier()

    verifier.load_model(1)

    result = verifier.predict(
        "../dataset/cedar/signatures/signatures_1/original_1_20.png"
    )

    print(result)