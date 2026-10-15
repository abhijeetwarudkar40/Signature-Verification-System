import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.config import (
    CEDAR_MODELS_DIR,
    DATASET_DIR,
    DATABASE_PATH,
    MIN_SIGNATURES,
    TOTAL_WRITERS,
    USER_DATA_DIR,
    USER_MODELS_DIR,
)
from src.database import Database
from src.trainer import SignatureTrainer
from src.user_manager import UserManager
from src.verifier import SignatureVerifier


# --------------------------------------------------
# Flask application and configuration
# --------------------------------------------------

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# Allow requests from the frontend development origins.


CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://10.129.87.218:8080",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    },
)



executor = ThreadPoolExecutor(max_workers=1)
jobs = {}
jobs_lock = threading.Lock()

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
HISTORY_DB = DATABASE_PATH


# --------------------------------------------------
# Database initialization
# --------------------------------------------------

def init_history():
    HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(HISTORY_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                target TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


# --------------------------------------------------
# Common helper functions
# --------------------------------------------------

def json_error(message, status=400):
    return jsonify({"error": str(message)}), status


def model_available(kind, target):
    if kind == "cedar":
        path = CEDAR_MODELS_DIR / f"writer_{target}.pkl"
    else:
        path = USER_MODELS_DIR / f"{target}.pkl"

    return path.is_file()


def sample_count(username):
    folder = USER_DATA_DIR / username / "genuine"

    if not folder.is_dir():
        return 0

    return sum(
        1
        for path in folder.iterdir()
        if path.is_file()
        and path.suffix.lower() in ALLOWED_EXTENSIONS
    )


def user_to_json(row):
    if row is None:
        return None

    user_id, username, full_name, model_path, created_at = row

    return {
        "username": username,
        "full_name": full_name,
        "model_path": model_path,
        "model_available": model_available("user", username),
        "sample_count": sample_count(username),
        "created_at": str(created_at),
    }


def get_users():
    manager = UserManager()

    try:
        return [
            user_to_json(row)
            for row in manager.get_users()
        ]
    finally:
        manager.database.close()


# --------------------------------------------------
# Model training
# --------------------------------------------------

def run_training(job_id, kind, target):
    with jobs_lock:
        jobs[job_id]["status"] = "running"

    try:
        trainer = SignatureTrainer()

        if kind == "cedar":
            result = trainer.train(int(target))
        else:
            result = trainer.train_user(target)

        # Save the trained model path in the user record.
        if kind == "user":
            db = Database()

            try:
                db.update_model_path(
                    target,
                    result["model_path"],
                )
            finally:
                db.close()

        metrics = result["metrics"]

        confusion_matrix = metrics["confusion_matrix"]

        if hasattr(confusion_matrix, "tolist"):
            confusion_matrix = confusion_matrix.tolist()

        payload = {
            "writer_id": result.get("writer_id"),
            "username": result.get("username"),
            "model_file": result["model_path"],
            "metrics": {
                "accuracy": float(metrics["accuracy"]),
                "precision": float(metrics["precision"]),
                "recall": float(metrics["recall"]),
                "f1_score": float(metrics["f1_score"]),
                "confusion_matrix": confusion_matrix,
            },
        }

        with jobs_lock:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = payload

    except Exception as exc:
        app.logger.exception(
            "Training job %s failed",
            job_id,
        )

        with jobs_lock:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(exc)


def start_training(kind, target):
    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "kind": kind,
        "target": str(target),
        "status": "queued",
    }

    with jobs_lock:
        jobs[job_id] = job

    executor.submit(
        run_training,
        job_id,
        kind,
        str(target),
    )

    return jsonify(job), 202


# --------------------------------------------------
# Signature verification helper
# --------------------------------------------------

def verify_signature(kind, target):
    uploaded = request.files.get("signature")

    if not uploaded or not uploaded.filename:
        return json_error("Upload a signature image.")

    extension = Path(
        secure_filename(uploaded.filename)
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return json_error(
            "Only PNG and JPEG images are accepted."
        )

    temp_dir = USER_DATA_DIR / "_verification_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_path = temp_dir / (
        f"{uuid.uuid4().hex}{extension}"
    )

    try:
        uploaded.save(temp_path)

        verifier = SignatureVerifier()

        if kind == "cedar":
            verifier.load_cedar_model(int(target))
        else:
            verifier.load_user_model(target)

        result = verifier.predict(str(temp_path))

        prediction = result["prediction"]
        confidence = float(result["confidence"])

        with sqlite3.connect(HISTORY_DB) as conn:
            conn.execute(
                """
                INSERT INTO verifications
                    (
                        kind,
                        target,
                        prediction,
                        confidence,
                        created_at
                    )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    kind,
                    str(target),
                    prediction,
                    confidence,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        return jsonify(
            {
                "prediction": prediction,
                "confidence": confidence,
                "probabilities": {
                    "genuine": float(
                        result["probabilities"]["genuine"]
                    ),
                    "forged": float(
                        result["probabilities"]["forged"]
                    ),
                },
            }
        )

    except FileNotFoundError as exc:
        return json_error(str(exc), 404)

    except Exception:
        app.logger.exception(
            "Signature verification failed"
        )

        return json_error(
            "Verification failed. Check the backend logs for details.",
            500,
        )

    finally:
        temp_path.unlink(missing_ok=True)


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/api/health")
def health():
    dataset_available = (
        DATASET_DIR / "signatures"
    ).is_dir()

    return jsonify(
        {
            "status": "ok",
            "dataset_available": dataset_available,
            "total_writers": TOTAL_WRITERS,
            "min_signatures": MIN_SIGNATURES,
        }
    )


# --------------------------------------------------
# Dashboard statistics
# --------------------------------------------------

@app.get("/api/stats")
def stats():
    try:
        users = get_users()

        with sqlite3.connect(HISTORY_DB) as conn:
            rows = conn.execute(
                """
                SELECT prediction, COUNT(*)
                FROM verifications
                GROUP BY prediction
                """
            ).fetchall()

            total = conn.execute(
                "SELECT COUNT(*) FROM verifications"
            ).fetchone()[0]

        counts = dict(rows)

        return jsonify(
            {
                "registered_users": len(users),
                "verifications": total,
                "genuine": counts.get("Genuine", 0),
                "forged": counts.get("Forged", 0),
            }
        )

    except Exception:
        app.logger.exception(
            "Could not load dashboard statistics"
        )

        return json_error(
            "Could not load dashboard statistics.",
            500,
        )


# --------------------------------------------------
# User registration and listing
# --------------------------------------------------

@app.get("/api/users")
def list_users():
    try:
        return jsonify(get_users())

    except Exception:
        app.logger.exception("Could not load users")

        return json_error(
            "Could not load users.",
            500,
        )


@app.post("/api/users")
def register_user():
    username = request.form.get(
        "username", ""
    ).strip().lower()

    full_name = request.form.get(
        "full_name", ""
    ).strip()

    files = request.files.getlist("signatures")

    if not username or not full_name:
        return json_error(
            "Full name and username are required."
        )

    if not username.replace("_", "").replace("-", "").isalnum():
        return json_error(
            "Username may contain letters, numbers, _ and - only."
        )

    if not files or any(not file.filename for file in files):
        return json_error(
            "Upload at least one signature image."
        )

    for file in files:
        extension = Path(
            secure_filename(file.filename)
        ).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            return json_error(
                "Only PNG and JPEG images are accepted."
            )

    manager = UserManager()

    try:
        manager.register_user(
            username,
            full_name,
            files,
        )

        row = manager.database.get_user(username)

        return jsonify(user_to_json(row)), 201

    except ValueError as exc:
        return json_error(str(exc), 409)

    except Exception:
        app.logger.exception("Registration failed")

        return json_error(
            "Registration failed.",
            500,
        )

    finally:
        manager.database.close()


# --------------------------------------------------
# Train a registered user's model
# --------------------------------------------------

@app.post("/api/users/<username>/train")
def train_user(username):
    username = username.strip().lower()

    db = Database()

    try:
        if not db.get_user(username):
            return json_error("User not found.", 404)

    finally:
        db.close()

    if sample_count(username) < MIN_SIGNATURES:
        return json_error(
            f"At least {MIN_SIGNATURES} genuine signature samples are required."
        )

    if not (DATASET_DIR / "signatures").is_dir():
        return json_error(
            "CEDAR dataset is not available.",
            503,
        )

    return start_training("user", username)


# --------------------------------------------------
# Train a CEDAR writer model
# --------------------------------------------------

@app.post("/api/cedar/<int:writer_id>/train")
def train_cedar(writer_id):
    if not 1 <= writer_id <= TOTAL_WRITERS:
        return json_error("Invalid CEDAR writer ID.")

    folder = (
        DATASET_DIR
        / "signatures"
        / f"signatures_{writer_id}"
    )

    if not folder.is_dir():
        return json_error(
            "CEDAR writer dataset not found.",
            404,
        )

    return start_training("cedar", writer_id)


# --------------------------------------------------
# Training job status
# --------------------------------------------------

@app.get("/api/jobs/<job_id>")
def job_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if not job:
            return json_error(
                "Training job not found.",
                404,
            )

        return jsonify(dict(job))


# --------------------------------------------------
# Verify a registered user's signature
# --------------------------------------------------

@app.post("/api/users/<username>/verify")
def verify_user(username):
    username = username.strip().lower()

    db = Database()

    try:
        if not db.get_user(username):
            return json_error("User not found.", 404)

    finally:
        db.close()

    return verify_signature("user", username)


# --------------------------------------------------
# Verify a CEDAR writer's signature
# --------------------------------------------------

@app.post("/api/cedar/<int:writer_id>/verify")
def verify_cedar(writer_id):
    if not 1 <= writer_id <= TOTAL_WRITERS:
        return json_error("Invalid CEDAR writer ID.")

    return verify_signature("cedar", writer_id)


# --------------------------------------------------
# Available models
# --------------------------------------------------

@app.get("/api/models")
def models():
    try:
        return jsonify(
            {
                "cedar": [
                    {
                        "writer_id": writer_id,
                        "available": model_available(
                            "cedar",
                            writer_id,
                        ),
                    }
                    for writer_id in range(
                        1,
                        TOTAL_WRITERS + 1,
                    )
                ],
                "users": [
                    {
                        "username": user["username"],
                        "available": user["model_available"],
                    }
                    for user in get_users()
                ],
            }
        )

    except Exception:
        app.logger.exception(
            "Could not load available models"
        )

        return json_error(
            "Could not load available models.",
            500,
        )


# --------------------------------------------------
# Verification history
# --------------------------------------------------

@app.get("/api/verifications")
def verifications():
    try:
        limit = min(
            max(int(request.args.get("limit", 10)), 1),
            100,
        )

    except ValueError:
        return json_error(
            "Limit must be an integer."
        )

    with sqlite3.connect(HISTORY_DB) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                kind,
                target,
                prediction,
                confidence,
                created_at
            FROM verifications
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return jsonify([dict(row) for row in rows])


# --------------------------------------------------
# Error handlers
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(_error):
    return json_error(
        "Upload exceeds the 5 MB limit.",
        413,
    )


@app.errorhandler(500)
def internal_error(_error):
    return json_error(
        "Internal server error.",
        500,
    )


# --------------------------------------------------
# Start application
# --------------------------------------------------

init_history()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
