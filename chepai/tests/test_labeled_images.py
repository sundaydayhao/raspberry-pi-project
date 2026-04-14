import os
import unittest
from pathlib import Path


PIC_DIR = Path(__file__).resolve().parent.parent / "pic"


def normalize_plate_label(label: str) -> str:
    return label.replace("-", "").upper()


class LabeledImageMetadataTestCase(unittest.TestCase):
    def test_pic_directory_contains_labeled_images(self) -> None:
        self.assertTrue(PIC_DIR.exists(), f"missing pic directory: {PIC_DIR}")
        images = sorted(PIC_DIR.glob("*.jpg"))
        self.assertTrue(images, "no labeled jpg images found in pic directory")

        for image_path in images:
            with self.subTest(image=image_path.name):
                expected_plate = normalize_plate_label(image_path.stem)
                self.assertTrue(expected_plate, "image filename must contain a plate label")


@unittest.skipUnless(
    os.environ.get("CHEPAI_RUN_IMAGE_TESTS") == "1",
    "set CHEPAI_RUN_IMAGE_TESTS=1 to run OCR image regression tests",
)
class LabeledImageRecognitionTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import cv2  # noqa: F401
            import pytesseract  # noqa: F401
            from lpr.pipeline import LicensePlateRecognizer  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f"missing runtime dependency: {exc.name}") from exc

        import cv2
        from lpr.pipeline import LicensePlateRecognizer

        cls.cv2 = cv2
        cls.recognizer = LicensePlateRecognizer()

    def test_recognizes_plate_from_filename(self) -> None:
        images = sorted(PIC_DIR.glob("*.jpg"))
        self.assertTrue(images, "no labeled jpg images found in pic directory")

        for image_path in images:
            with self.subTest(image=image_path.name):
                expected_plate = normalize_plate_label(image_path.stem)
                image = self.cv2.imread(str(image_path))
                self.assertIsNotNone(image, f"failed to read image: {image_path}")

                results = self.recognizer.recognize(image, top_k=3)
                actual_plates = [normalize_plate_label(item.text) for item in results]
                self.assertIn(expected_plate, actual_plates)


if __name__ == "__main__":
    unittest.main()
