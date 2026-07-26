import cv2
import matplotlib.pyplot as plt
from skimage.feature import hog

from src.config import (
    HOG_ORIENTATIONS,
    HOG_PIXELS_PER_CELL,
    HOG_CELLS_PER_BLOCK,
    HOG_BLOCK_NORM,
)

class FeatureExtractor:

    def __init__(self, visualize=False):
        self.visualize = visualize

    # Extract HOG Features
    def extract_hog(self, image):

        if self.visualize:

            features, hog_image = hog(
                image,
                orientations=HOG_ORIENTATIONS,
                pixels_per_cell=HOG_PIXELS_PER_CELL,
                cells_per_block=HOG_CELLS_PER_BLOCK,
                block_norm=HOG_BLOCK_NORM,
                visualize=True,
                feature_vector=True
            )

            return features, hog_image

        features = hog(
            image,
            orientations=HOG_ORIENTATIONS,
            pixels_per_cell=HOG_PIXELS_PER_CELL,
            cells_per_block=HOG_CELLS_PER_BLOCK,
            block_norm=HOG_BLOCK_NORM,
            visualize=False,
            feature_vector=True
        )

        return features

    # Display HOG Image
    def show_hog(self, image, hog_image):

        plt.figure(figsize=(10, 4))

        plt.subplot(1, 2, 1)
        plt.imshow(image, cmap="gray")
        plt.title("Processed Image")
        plt.axis("off")

        plt.subplot(1, 2, 2)
        plt.imshow(hog_image, cmap="gray")
        plt.title("HOG Visualization")
        plt.axis("off")

        plt.tight_layout()
        plt.show()


# Testing
if __name__ == "__main__":

    from preprocessing import SignaturePreprocessor

    IMAGE_PATH = (
    "../dataset/cedar/"
    "signatures/"
    "signatures_1/"
    "original_1_1.png"
)

    processor = SignaturePreprocessor(debug=False)

    processed_image, _ = processor.process(IMAGE_PATH)

    extractor = FeatureExtractor(visualize=True)

    features, hog_image = extractor.extract_hog(processed_image)

    print("Feature Vector Shape :", features.shape)
    print("Feature Vector Length:", len(features))

    extractor.show_hog(processed_image, hog_image)