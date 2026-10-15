# SignaVerify — Signature Verification System

A web-based signature verification prototype combining image processing, machine learning, and a React frontend with a Python/Flask API.

> **Important:** Predictions are model-based estimates, not legal or forensic proof of authenticity.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [API Overview](#api-overview)
- [Machine-Learning Pipeline](#machine-learning-pipeline)
- [Dataset and Models](#dataset-and-models)
- [Configuration](#configuration)
- [Privacy and Security](#privacy-and-security)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [License](#license)

## Overview

SignaVerify provides a web interface for assessing whether a submitted signature resembles a genuine or forged signature. It supports workflows for CEDAR dataset writers and user-specific signature models trained from uploaded genuine samples.

The project includes a Flask API, Python image-processing and model-training modules, SQLite persistence, and a React/TypeScript frontend.

## Features

- Train models for supported writers in the CEDAR dataset.
- Register users and upload genuine signature samples.
- Train user-specific signature models.
- Submit signature images for model-based verification.
- Return predictions and confidence/probability information where available.
- Process images and extract Histogram of Oriented Gradients (HOG) features.
- Use Support Vector Machine (SVM) classification.
- Store registered-user information and verification records locally with SQLite.
- Check the status of training jobs through the API.

Available functionality depends on the current configuration, dataset files, and trained models.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, Flask, Flask-CORS |
| Machine learning | scikit-learn, SVM, HOG features |
| Image processing | OpenCV, Pillow, NumPy |
| Data storage | SQLite |
| Model persistence | Joblib / serialized model files |

See the dependency files in the repository for the exact package versions.

## Architecture

```text
React / TypeScript Frontend
          |
          | HTTP requests (JSON / multipart form data)
          v
       Flask API
          |
          +--> User management and SQLite
          +--> Signature image preprocessing
          +--> HOG feature extraction
          +--> SVM training and verification
          +--> Saved models and verification records
```

## Project Structure

```text
SignatureVerification/
├── api.py                     # Flask API for frontend requests
├── app.py                     # Python application entry point
├── requirements.txt           # Backend dependencies, if present
├── src/
│   ├── config.py              # Paths and model configuration
│   ├── database.py            # SQLite database operations
│   ├── preprocessing.py       # Image preprocessing
│   ├── feature_extractor.py   # Feature extraction
│   ├── trainer.py             # Model training
│   ├── verifier.py            # Signature prediction
│   └── user_manager.py        # Registered-user management
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── lib/               # API client and utilities
│   │   └── routes/            # Application pages
│   ├── package.json
│   └── vite.config.ts
├── dataset/                   # Local dataset files (not necessarily tracked)
├── models/                    # Saved models, depending on configuration
└── user_data/                 # User uploads/models, depending on configuration
```

Actual model, database, and user-data paths are controlled by `src/config.py` and may differ from this illustrative tree.

## Prerequisites

- Python version compatible with the installed backend dependencies.
- Node.js and npm.
- CEDAR dataset files if using the CEDAR training and verification workflow.

Check your installed tools:

```powershell
python --version
node --version
npm --version
```

## Installation

### 1. Get the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SignatureVerification
```

Alternatively, open your existing project directory in a terminal.

### 2. Set up Python

From the project root, create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies from the root dependency file if present:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the root `requirements.txt` is missing, create or use a backend dependency file listing the packages imported by the Python application. Use `frontend/requirements.txt` only if that file is intentionally meant for the backend.

### 3. Install frontend dependencies

Open a second terminal:

```powershell
cd frontend
npm install
```

When `package-lock.json` is in sync with `package.json`, `npm ci` can be used for a reproducible install.

### 4. Configure the frontend API URL

Create `frontend/.env` if needed:

```env
VITE_API_BASE_URL=http://localhost:5000
```

This tells the frontend where the Flask API is running. Do not commit local `.env` files.

### 5. Check configuration and dataset paths

Review `src/config.py`. Confirm the dataset, model, database, and user-data paths match your machine. Make sure required files are present before starting training.

## Running the Application

Run the backend and frontend in separate terminals.

### Terminal 1 — Flask backend

From the project root, activate the virtual environment and run:

```powershell
python api.py
```

The API is expected to be available at `http://localhost:5000`.

Check its health endpoint:

```text
http://localhost:5000/api/health
```

The response should be JSON indicating backend status. Dataset availability and supported writer counts depend on local configuration.

### Terminal 2 — Frontend

From the frontend directory:

```powershell
cd frontend
npm run dev
```

Open the local URL printed by the development server. Use the actual port shown in the terminal rather than assuming a specific port.

### CORS configuration

If the browser reports a CORS error, configure Flask-CORS in `api.py` to allow the exact frontend origin shown in the address bar. Keep the allowlist limited to trusted origins and restart Flask after changes.

## Usage

### CEDAR writer verification

1. Confirm the CEDAR dataset exists at the configured path.
2. Open the CEDAR training page.
3. Select a supported writer and start training.
4. Wait for the training job to complete.
5. Open CEDAR verification and select the same writer.
6. Upload a signature image and review the prediction and available confidence/probability values.

### User-specific verification

1. Open the registration page.
2. Enter the user's details and upload genuine signature samples.
3. Register the user.
4. Start training for that user and wait for it to complete.
5. Open user verification, select the registered user, and upload the signature to assess.
6. Review the model output.

Use clear images and follow the sample-count requirements shown by the current configuration or interface. Training quality and sample diversity affect performance.

## API Overview

The frontend API client uses these endpoint patterns in the current project:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check backend availability |
| `GET` | `/api/stats` | Retrieve dashboard statistics |
| `GET` | `/api/users` | List registered users |
| `POST` | `/api/users` | Register a user with signature uploads |
| `POST` | `/api/users/<username>/train` | Start user-specific training |
| `POST` | `/api/cedar/<writer_id>/train` | Start CEDAR writer training |
| `GET` | `/api/jobs/<job_id>` | Check training job status |
| `POST` | `/api/users/<username>/verify` | Verify against a user's model |
| `POST` | `/api/cedar/<writer_id>/verify` | Verify against a CEDAR writer model |
| `GET` | `/api/models` | List available models |
| `GET` | `/api/verifications?limit=<n>` | Retrieve recent verification records |

Check `api.py` for the exact request fields, response formats, and current implementation details.

## Machine-Learning Pipeline

The current approach uses image preprocessing, HOG features, and an SVM classifier.

1. **Preprocessing:** Load and prepare the signature image using configured image-processing steps.
2. **Feature extraction:** Convert the image into a numerical HOG feature vector.
3. **Training:** Fit the configured SVM pipeline using labeled signature samples.
4. **Persistence:** Save the trained model for later use.
5. **Verification:** Apply the same preprocessing and feature extraction to a submitted image, then obtain a prediction and any available confidence/probability output.

Results depend on dataset quality, writer separation, training/test split design, and model parameters. High accuracy on a small test set does not guarantee performance on unseen writers or real-world signatures.

## Dataset and Models

The project is designed to work with the CEDAR signature dataset and user-provided genuine signature samples.

- Obtain datasets only from sources whose terms permit your intended use.
- Place dataset files in the path configured in `src/config.py`.
- Do not commit private user signature samples to a public repository.
- Model files may be large or tied to a particular configuration. Consider Git LFS or external artifact storage for large files.
- Use a writer-specific model with the corresponding writer; do not assume it will reliably verify signatures from other writers.

## Configuration

Review `src/config.py` for settings such as:

- Dataset, database, model, and user-data paths.
- Signature image dimensions and preprocessing parameters.
- HOG feature-extraction parameters.
- SVM and training settings.
- Minimum sample requirements and supported writer count.

Avoid hardcoding personal absolute paths in code intended for public distribution.

## Privacy and Security

Signatures are sensitive personal data and should be handled carefully.

- Keep private uploads, user databases, credentials, and local environment files out of public version control.
- Restrict CORS to trusted frontend origins.
- Validate uploaded file types and size limits.
- Do not expose the development server publicly without authentication, authorization, transport security, and deployment hardening.
- Explain to users how uploaded signatures and verification records are stored and deleted.
- Back up important local data before deleting records or resetting the database.

## Troubleshooting

### Frontend says the backend is offline

1. Confirm Flask is running.
2. Open `http://localhost:5000/api/health`.
3. Check `VITE_API_BASE_URL` in `frontend/.env`.
4. Restart the frontend after changing environment variables.

### Browser reports a CORS error

Add the exact frontend origin to the Flask-CORS allowlist in `api.py`, then restart Flask. An origin includes the scheme, hostname, and port.

### Dataset or model not found

Check paths in `src/config.py` and confirm the required files exist in those locations.

### Training fails

Read the traceback in the backend terminal. Confirm that the dataset structure and labels match the trainer's expectations and that enough valid samples are available.

### Verification gives unexpected results

Confirm that the correct writer or registered user is selected. Test on a representative, independent dataset and do not rely on confidence values alone as proof of authenticity.

## Future Improvements

- Evaluate using writer-independent test sets.
- Improve handling of class imbalance and limited training samples.
- Calibrate decision thresholds and report false acceptance and false rejection rates.
- Add model version management and clearer evaluation reports.
- Expand automated tests for registration, training, verification, and database operations.
- Add authentication, authorization, and deployment hardening.

## License

No license is specified in this README. Add a `LICENSE` file before public distribution and verify the redistribution terms of any datasets or third-party assets.

---

**SignaVerify** — a signature verification prototype combining image processing, machine learning, and a web interface.
