import tempfile
from pathlib import Path

import streamlit as st

from src.trainer import SignatureTrainer
from src.verifier import SignatureVerifier

st.set_page_config(
    page_title="Signature Verification",
    page_icon="🛡️",
    layout="wide"
)

st.title("Offline Signature Verification")
st.caption("HOG + SVM | CEDAR Dataset")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Train Model",
        "Verify Signature"
    ]
)

# ---------------- HOME ---------------- #

if page == "Home":

    st.header("Project Overview")

    st.write("""
    This application verifies offline handwritten signatures using
    Histogram of Oriented Gradients (HOG) features and a Support Vector
    Machine (SVM) classifier.

    Current Dataset:
    - CEDAR Signature Dataset

    Current Workflow:
    1. Select a writer
    2. Train a model
    3. Upload a signature
    4. Predict Genuine / Forged
    """)

# ---------------- TRAIN ---------------- #

elif page == "Train Model":

    st.header("Train Writer Model")

    writer_id = st.selectbox(
        "Select Writer",
        list(range(1, 56))
    )

    if st.button("Train"):

        with st.spinner("Training model..."):

            trainer = SignatureTrainer()

            result = trainer.train(writer_id)

        metrics = result["metrics"]

        st.success("Training completed successfully.")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Accuracy",
                f"{metrics['accuracy']:.2%}"
            )

            st.metric(
                "Precision",
                f"{metrics['precision']:.2%}"
            )

        with col2:
            st.metric(
                "Recall",
                f"{metrics['recall']:.2%}"
            )

            st.metric(
                "F1 Score",
                f"{metrics['f1_score']:.2%}"
            )

        st.write("Model Saved")

        st.code(result["model_path"])

        st.write("Confusion Matrix")

        st.dataframe(metrics["confusion_matrix"])

# ---------------- VERIFY ---------------- #

elif page == "Verify Signature":

    st.header("Verify Signature")

    writer_id = st.selectbox(
        "Writer",
        list(range(1, 56))
    )

    uploaded_file = st.file_uploader(
        "Upload Signature",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:

        if st.button("Verify"):

            suffix = Path(uploaded_file.name).suffix

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as tmp:

                tmp.write(uploaded_file.read())

                temp_path = tmp.name

            verifier = SignatureVerifier()

            verifier.load_model(writer_id)

            result = verifier.predict(temp_path)

            prediction = result["prediction"]
            confidence = result["confidence"]

            if prediction == "Genuine":

                st.success(
                    f"Prediction: {prediction}"
                )

            else:

                st.error(
                    f"Prediction: {prediction}"
                )

            st.metric(
                "Confidence",
                f"{confidence:.2%}"
            )

            st.write("Class Probabilities")

            st.json(result["probabilities"])