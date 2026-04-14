import unittest

class RectifyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import cv2  # noqa: F401
            import numpy as np  # noqa: F401
            import pytesseract  # noqa: F401
            from lpr.pipeline import LicensePlateRecognizer  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f"missing runtime dependency: {exc.name}") from exc

        import cv2
        import numpy as np
        from lpr.pipeline import LicensePlateRecognizer

        cls.cv2 = cv2
        cls.np = np
        cls.recognizer_cls = LicensePlateRecognizer

    def test_build_candidate_views_for_rotated_plate(self) -> None:
        canvas = self.np.full((220, 420, 3), 255, dtype=self.np.uint8)
        plate = self.np.zeros((70, 220, 3), dtype=self.np.uint8)
        plate[:, :] = (255, 0, 0)
        self.cv2.putText(
            plate,
            "A12345",
            (22, 48),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (255, 255, 255),
            2,
            self.cv2.LINE_AA,
        )

        matrix = self.cv2.getRotationMatrix2D((110, 35), 18, 1.0)
        rotated = self.cv2.warpAffine(
            plate,
            matrix,
            (220, 70),
            flags=self.cv2.INTER_CUBIC,
            borderMode=self.cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255),
        )
        canvas[75:145, 100:320] = rotated
        crop = canvas[65:155, 90:330]

        views = self.recognizer_cls._build_candidate_views(crop)

        self.assertGreaterEqual(len(views), 1)
        self.assertTrue(any(view.shape[1] > view.shape[0] * 2 for view in views))


if __name__ == "__main__":
    unittest.main()
