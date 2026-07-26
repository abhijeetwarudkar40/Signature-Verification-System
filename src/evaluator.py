import random
import csv
from .config import RESULTS_DIR

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from .config import (
    DATASET_DIR,
    TOTAL_WRITERS,
    IMPOSTOR_SAMPLES_PER_WRITER,
    RANDOM_STATE,
)
from src.verifier import SignatureVerifier

class SignatureEvaluator:

    def __init__(self):
        RESULTS_DIR.mkdir(exist_ok=True)
        self.verifier = SignatureVerifier()

        self.signature_root = DATASET_DIR / "signatures"

    def calculate_far_frr(self, y_true, y_pred):

        tn, fp, fn, tp = confusion_matrix(
            y_true,
            y_pred
        ).ravel()

        far = fp / (fp + tn) if (fp + tn) else 0

        frr = fn / (fn + tp) if (fn + tp) else 0

        return far, frr 

    def evaluate_writer(self, writer_id):

        self.verifier.load_model(writer_id)

        y_true = []
        y_pred = []

        writer_folder = (
            self.signature_root /
            f"signatures_{writer_id}"
        )

        # Evaluate genuine signatures
        genuine_images = sorted(
            writer_folder.glob(f"original_{writer_id}_*.png")
        )

        for image_path in genuine_images:

            result = self.verifier.predict_label(image_path)

            y_true.append(1)
            y_pred.append(result["label"])

        # Evaluate skilled forgeries
        forged_images = sorted(
            writer_folder.glob(f"forgeries_{writer_id}_*.png")
        )

        for image_path in forged_images:

            result = self.verifier.predict_label(image_path)

            y_true.append(0)
            y_pred.append(result["label"])

        # Evaluate impostor genuine signatures
        rng = random.Random(RANDOM_STATE)

        for other_writer in range(1, TOTAL_WRITERS + 1):

            if other_writer == writer_id:
                continue

            other_folder = (
                self.signature_root /
                f"signatures_{other_writer}"
            )

            other_genuine = sorted(
                other_folder.glob(
                    f"original_{other_writer}_*.png"
                )
            )

            sampled = rng.sample(
                other_genuine,
                IMPOSTOR_SAMPLES_PER_WRITER
            )

            for image_path in sampled:

                result = self.verifier.predict_label(image_path)

                y_true.append(0)
                y_pred.append(result["label"])

        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        far, frr = self.calculate_far_frr(
            y_true,
            y_pred
        )

        return {
    "writer_id": writer_id,
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1_score": f1,
    "far": far,
    "frr": frr,
    "tp": tp,
    "tn": tn,
    "fp": fp,
    "fn": fn,
    "confusion_matrix": cm
}

    def evaluate_all(self):

        results = []

        for writer_id in range(1, TOTAL_WRITERS + 1):

            print(f"[{writer_id}/{TOTAL_WRITERS}] Evaluating Writer {writer_id}...")

            try:
                metrics = self.evaluate_writer(writer_id)
                results.append(metrics)

            except FileNotFoundError:
                print(f"Skipping Writer {writer_id}: Model not found.")

        if results:
            csv_path = self.save_results(results)
            print(f"\nReport saved to: {csv_path}")

        return results

    def save_results(self, results):

        csv_path = RESULTS_DIR / "evaluation_report.csv"

        with open(csv_path, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Writer ID",
                "Accuracy",
                "Precision",
                "Recall",
                "F1 Score",
                "FAR",
                "FRR",
                "TP",
                "TN",
                "FP",
                "FN"
            ])

            for result in results:

                writer.writerow([
                result["writer_id"],
                    round(result["accuracy"], 4),
                    round(result["precision"], 4),
                    round(result["recall"], 4),
                    round(result["f1_score"], 4),
                    round(result["far"], 4),
                    round(result["frr"], 4),
                    result["tp"],
                    result["tn"],
                    result["fp"],
                    result["fn"]
                ])
                writer.writerow([])

                writer.writerow([
                    "Average",
                    round(sum(r["accuracy"] for r in results) / len(results), 4),
                    round(sum(r["precision"] for r in results) / len(results), 4),
                    round(sum(r["recall"] for r in results) / len(results), 4),
                    round(sum(r["f1_score"] for r in results) / len(results), 4),
                    round(sum(r["far"] for r in results) / len(results), 4),
                    round(sum(r["frr"] for r in results) / len(results), 4),
                    round(sum(r["tp"] for r in results) / len(results), 2),
                    round(sum(r["tn"] for r in results) / len(results), 2),
                    round(sum(r["fp"] for r in results) / len(results), 2),
                    round(sum(r["fn"] for r in results) / len(results), 2)
                ])

        return csv_path 

if __name__ == "__main__":

    evaluator = SignatureEvaluator()
    evaluator.evaluate_all()