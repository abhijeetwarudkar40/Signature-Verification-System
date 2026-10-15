import tempfile
from pathlib import Path
from src.user_manager import UserManager
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
        "Register User",
        "Train CEDAR Model",
        "Train User Model",
        "Verify CEDAR Signature",
        "Verify User Signature"
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


# ---------------- REGISTER USER ---------------- #

elif page == "Register User":

    st.header("Register New User")

    username = st.text_input("Username")

    full_name = st.text_input("Full Name")

    uploaded_files = st.file_uploader(
        "Upload Genuine Signatures",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.caption("Upload at least 10 genuine signatures.")

    if st.button("Register"):

        try:

            manager = UserManager()

            folder = manager.register_user(
                username,
                full_name,
                uploaded_files
            )

            st.success("User registered successfully.")

            st.write("Images saved to:")

            st.code(folder)

        except Exception as e:

            st.error(str(e))

# ---------------- TRAIN ---------------- #

elif page == "Train CEDAR Model":

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

elif page == "Verify CEDAR Signature":
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

            verifier.load_cedar_model(writer_id)

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

# ---------------- TRAIN USER MODEL ---------------- #

elif page == "Train User Model":

    st.header("Train Registered User Model")

    manager = UserManager()

    users = manager.get_users()

    if not users:
        st.warning("No registered users found.")

    else:

        usernames = [user[1] for user in users]

        username = st.selectbox(
            "Select User",
            usernames
        )

        if st.button("Train User Model"):

            with st.spinner("Training model..."):

                trainer = SignatureTrainer()

                result = trainer.train_user(username)
                manager.database.update_model_path(
                    username,
                    result["model_path"]
                )
                
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

elif page == "Verify User Signature":

    st.header("Verify Registered User Signature")

    manager = UserManager()

    users = manager.get_users()

    if not users:

        st.warning("No registered users found.")

    else:

        usernames = [user[1] for user in users]

        username = st.selectbox(
            "Select User",
            usernames
        )

        uploaded_file = st.file_uploader(
            "Upload Signature",
            type=["png", "jpg", "jpeg"]
        )

        if uploaded_file is not None:

            if st.button("Verify User Signature"):

                suffix = Path(uploaded_file.name).suffix

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix
                ) as tmp:

                    tmp.write(uploaded_file.read())

                    temp_path = tmp.name

                verifier = SignatureVerifier()

                verifier.load_user_model(username)

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