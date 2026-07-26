import cv2
import numpy as np
import matplotlib.pyplot as plt

from src.config import (
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID_SIZE,
    GAUSSIAN_KERNEL,
    MIN_COMPONENT_AREA,
)

class SignaturePreprocessor:

    def __init__(
        self,
        debug=False,
        canvas_size=(IMAGE_WIDTH, IMAGE_HEIGHT),
        remove_noise=True,
    ):

        self.debug = debug
        self.canvas_width, self.canvas_height = canvas_size
        self.remove_noise = remove_noise

        self.debug_images = []
        self.debug_titles = []

    ##############################################################
    # Utility Functions
    ##############################################################

    def _store(self, image, title):

        if self.debug:
            self.debug_images.append(image.copy())
            self.debug_titles.append(title)

    ##############################################################
    # Step 1
    ##############################################################

    def load_image(self, image_path):

        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise FileNotFoundError(
                f"Unable to load image:\n{image_path}"
            )

        self._store(image, "Original")

        return image

    ##############################################################
    # Step 2
    ##############################################################

    def enhance_contrast(self, image):

        clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=CLAHE_TILE_GRID_SIZE
        )

        image = clahe.apply(image)

        self._store(image, "CLAHE")

        return image

    ##############################################################
    # Step 3
    ##############################################################

    def gaussian_blur(self, image):

        image = cv2.GaussianBlur(
            image,
            GAUSSIAN_KERNEL,
            0
        )

        self._store(image, "Gaussian Blur")

        return image

    ##############################################################
    # Step 4
    ##############################################################

    def threshold(self, image):

        _, image = cv2.threshold(
            image,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        self._store(image, "Threshold")

        return image

    ##############################################################
    # Step 5
    ##############################################################

    def invert(self, image):

        image = cv2.bitwise_not(image)

        self._store(image, "Invert")

        return image

    ##############################################################
    # Step 6
    ##############################################################

    def remove_small_components(self, image):

        if not self.remove_noise:
            return image

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            image,
            connectivity=8
        )

        cleaned = np.zeros_like(image)

        for i in range(1, num_labels):

            area = stats[i, cv2.CC_STAT_AREA]

            if area >= MIN_COMPONENT_AREA:

                cleaned[labels == i] = 255

        self._store(cleaned, "Noise Removed")

        return cleaned

    ##############################################################
    # Step 7
    ##############################################################

    def crop_signature(self, image):

        points = cv2.findNonZero(image)

        if points is None:
            raise ValueError("No signature detected.")

        x, y, w, h = cv2.boundingRect(points)

        padding = 10

        x = max(0, x - padding)
        y = max(0, y - padding)

        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)

        if w <= 0 or h <= 0:
            raise ValueError("Invalid cropped image.")

        cropped = image[y:y + h, x:x + w]

        metadata = {
            "bounding_box": (x, y, w, h),
            "signature_area": int(np.count_nonzero(cropped)),
            "aspect_ratio": round(w / h, 3)
        }

        self._store(cropped, "Cropped")

        return cropped, metadata

    ##############################################################
    # Step 8
    ##############################################################

    def resize_preserving_aspect_ratio(self, image):

        h, w = image.shape
        if w <= 0 or h <= 0:
            raise ValueError("Invalid image dimensions.")
        scale = min(
            self.canvas_width / w,
            self.canvas_height / h
        )

        new_width = int(w * scale)
        new_height = int(h * scale)

        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )

        self._store(resized, "Resized")

        return resized

    ##############################################################
    # Step 9
    ##############################################################

    def center_on_canvas(self, image):

        # Create white canvas
        canvas = np.full(
            (self.canvas_height, self.canvas_width),
            255,
            dtype=np.uint8
        )

        h, w = image.shape

        x_offset = (self.canvas_width - w) // 2
        y_offset = (self.canvas_height - h) // 2

        # Convert signature back to black on white
        image = 255 - image

        canvas[
            y_offset:y_offset + h,
            x_offset:x_offset + w
        ] = image

        self._store(canvas, "Centered")

        return canvas

    ##############################################################
    # Step 10
    ##############################################################

    def quality_check(self, image, metadata):

        h, w = image.shape

        signature_pixels = np.sum(image == 0)

        coverage = (
            signature_pixels /
            float(h * w)
        ) * 100

        metadata["coverage_percent"] = round(coverage, 2)

        if coverage < 0.5:
            metadata["quality"] = "Poor"

        elif coverage < 2:
            metadata["quality"] = "Fair"

        else:
            metadata["quality"] = "Good"

        return metadata

    ##############################################################
    # Debug Visualization
    ##############################################################

    def show_debug_images(self):

        if not self.debug:
            return

        cols = 3
        rows = int(np.ceil(len(self.debug_images) / cols))

        plt.figure(figsize=(15, rows * 4))

        for i, (img, title) in enumerate(
            zip(self.debug_images, self.debug_titles)
        ):

            plt.subplot(rows, cols, i + 1)

            plt.imshow(img, cmap="gray")

            plt.title(title)

            plt.axis("off")

        plt.tight_layout()

        plt.show()

    ##############################################################
    # Complete Pipeline
    ##############################################################

    def process(self, image_path):

        self.debug_images.clear()
        self.debug_titles.clear()

        image = self.load_image(image_path)

        image = self.enhance_contrast(image)

        image = self.gaussian_blur(image)

        image = self.threshold(image)

        image = self.invert(image)

        image = self.remove_small_components(image)

        image, metadata = self.crop_signature(image)

        image = self.resize_preserving_aspect_ratio(image)

        image = self.center_on_canvas(image)

        metadata = self.quality_check(
            image,
            metadata
        )

        self._store(image, "Final Output")

        if self.debug:
            self.show_debug_images()

        return image, metadata


##############################################################
# Testing
##############################################################

if __name__ == "__main__":

    IMAGE_PATH = (
        "../dataset/signatures/"
        "signatures_1/"
        "original_1_1.png"
    )

    processor = SignaturePreprocessor(
        debug=True
    )

    processed_image, info = processor.process(
        IMAGE_PATH
    )

    print("\nMetadata\n")

    for key, value in info.items():
        print(f"{key}: {value}")

    cv2.imshow(
        "Processed Signature",
        processed_image
    )

    cv2.waitKey(0)

    cv2.destroyAllWindows()