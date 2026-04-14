from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

from .detector import LicensePlateDetector
from .ocr import PlateOCR
from .postprocess import PROVINCE_SET


@dataclass
class RecognitionResult:
    text: str
    bbox: Tuple[int, int, int, int]
    score: float
    ocr_confidence: float
    source: str


class LicensePlateRecognizer:
    def __init__(
        self,
        detector: Optional[LicensePlateDetector] = None,
        ocr: Optional[PlateOCR] = None,
    ) -> None:
        self.detector = detector or LicensePlateDetector()
        self.ocr = ocr or PlateOCR()

    def recognize(self, image: np.ndarray, top_k: int = 3) -> List[RecognitionResult]:
        candidates = self.detector.detect(image, top_k=max(top_k * 3, 6))
        results: List[RecognitionResult] = []

        for candidate in candidates:
            crop = self._crop(image, candidate.bbox)
            if crop.size == 0:
                continue

            ocr_result = self._read_candidate(crop)
            if not ocr_result.text:
                continue

            final_score = min(1.0, candidate.score * 0.35 + ocr_result.score * 0.65)
            results.append(
                RecognitionResult(
                    text=ocr_result.text,
                    bbox=candidate.bbox,
                    score=final_score,
                    ocr_confidence=ocr_result.confidence,
                    source=candidate.source,
                )
            )

        unique_results = self._deduplicate(results)
        if not unique_results:
            fallback = self._fallback_ocr(image)
            if fallback is not None:
                unique_results.append(fallback)
        return sorted(unique_results, key=lambda item: item.score, reverse=True)[:top_k]

    @staticmethod
    def draw_results(
        image: np.ndarray, results: List[RecognitionResult]
    ) -> np.ndarray:
        annotated = image.copy()
        for result in results:
            x, y, w, h = result.bbox
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (36, 255, 12), 2)
            label = f"{result.text} {result.score:.2f}"
            annotated = LicensePlateRecognizer._draw_text(
                annotated,
                label,
                (x, max(20, y - 10)),
            )
        return annotated

    @staticmethod
    def _crop(image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = bbox
        return image[y : y + h, x : x + w]

    def _read_candidate(self, crop: np.ndarray):
        best = self.ocr.read(crop)
        for view in self._build_candidate_views(crop):
            ocr_result = self.ocr.read(view)
            if self._is_better_ocr_result(ocr_result, best):
                best = ocr_result
        return best

    @staticmethod
    def _build_candidate_views(crop: np.ndarray) -> List[np.ndarray]:
        views: List[np.ndarray] = []
        for refined in (
            LicensePlateRecognizer._rectify_by_min_area_rect(crop),
            LicensePlateRecognizer._rectify_by_rotation(crop),
        ):
            if refined is None or refined.size == 0:
                continue
            if min(refined.shape[:2]) < 12:
                continue
            if any(LicensePlateRecognizer._images_similar(refined, saved) for saved in views):
                continue
            views.append(refined)
        return views

    @staticmethod
    def _deduplicate(
        results: List[RecognitionResult],
    ) -> List[RecognitionResult]:
        deduped = {}
        for result in results:
            saved = deduped.get(result.text)
            if saved is None or result.score > saved.score:
                deduped[result.text] = result
        return list(deduped.values())

    @staticmethod
    def _draw_text(
        image: np.ndarray,
        text: str,
        origin: Tuple[int, int],
        color: Tuple[int, int, int] = (0, 255, 0),
    ) -> np.ndarray:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return LicensePlateRecognizer._draw_text_with_opencv(
                image, text, origin, color
            )

        font = LicensePlateRecognizer._load_chinese_font(28)
        if font is None:
            return LicensePlateRecognizer._draw_text_with_opencv(
                image, text, origin, color
            )

        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        left, baseline = origin
        top = max(0, baseline - 28)

        bbox = draw.textbbox((left, top), text, font=font)
        background = (
            max(0, bbox[0] - 4),
            max(0, bbox[1] - 2),
            min(image.shape[1], bbox[2] + 4),
            min(image.shape[0], bbox[3] + 2),
        )
        draw.rectangle(background, fill=(0, 0, 0))
        draw.text((left, top), text, font=font, fill=(color[2], color[1], color[0]))
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _draw_text_with_opencv(
        image: np.ndarray,
        text: str,
        origin: Tuple[int, int],
        color: Tuple[int, int, int] = (0, 255, 0),
    ) -> np.ndarray:
        cv2.putText(
            image,
            text,
            origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )
        return image

    @staticmethod
    def _load_chinese_font(size: int):
        try:
            from PIL import ImageFont
        except ImportError:
            return None

        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
        ]
        for font_path in candidates:
            if not Path(font_path).exists():
                continue
            try:
                return ImageFont.truetype(font_path, size=size)
            except OSError:
                continue
        return None

    def _fallback_ocr(self, image: np.ndarray) -> Optional[RecognitionResult]:
        height, width = image.shape[:2]
        fallback_regions = [
            ((0, 0, width, height), image),
            (
                (0, height // 3, width, height - height // 3),
                image[height // 3 :, :],
            ),
        ]

        best: Optional[RecognitionResult] = None
        for bbox, region in fallback_regions:
            ocr_result = self.ocr.read(region)
            if not ocr_result.text or ocr_result.score < 0.5:
                continue

            candidate = RecognitionResult(
                text=ocr_result.text,
                bbox=bbox,
                score=min(0.75, ocr_result.score),
                ocr_confidence=ocr_result.confidence,
                source="fallback",
            )
            if best is None or candidate.score > best.score:
                best = candidate
        return best

    @staticmethod
    def _images_similar(left: np.ndarray, right: np.ndarray) -> bool:
        if left.shape[:2] == right.shape[:2]:
            diff = cv2.absdiff(left, right)
            return float(diff.mean()) < 2.0
        return False

    @staticmethod
    def _is_better_ocr_result(candidate, current) -> bool:
        if not candidate.text:
            return False
        if not current.text:
            return True

        candidate_has_province = candidate.text[0] in PROVINCE_SET
        current_has_province = current.text[0] in PROVINCE_SET

        if candidate_has_province and not current_has_province:
            return candidate.score >= current.score - 0.02
        if current_has_province and not candidate_has_province:
            return candidate.score >= current.score + 0.15
        return candidate.score > current.score + 0.05

    @staticmethod
    def _rectify_by_rotation(crop: np.ndarray) -> Optional[np.ndarray]:
        contour = LicensePlateRecognizer._find_plate_contour(crop)
        if contour is None:
            return None

        rect = cv2.minAreaRect(contour)
        (_, _), (width, height), angle = rect
        if width <= 0 or height <= 0:
            return None

        if width < height:
            angle += 90.0
        if abs(angle) < 2.0:
            return None

        center = (crop.shape[1] / 2.0, crop.shape[0] / 2.0)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            crop,
            matrix,
            (crop.shape[1], crop.shape[0]),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return LicensePlateRecognizer._tight_crop(rotated)

    @staticmethod
    def _rectify_by_min_area_rect(crop: np.ndarray) -> Optional[np.ndarray]:
        contour = LicensePlateRecognizer._find_plate_contour(crop)
        if contour is None:
            return None

        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.array(box, dtype=np.float32)
        ordered = LicensePlateRecognizer._order_points(box)

        width_top = np.linalg.norm(ordered[1] - ordered[0])
        width_bottom = np.linalg.norm(ordered[2] - ordered[3])
        height_left = np.linalg.norm(ordered[3] - ordered[0])
        height_right = np.linalg.norm(ordered[2] - ordered[1])
        width = int(max(width_top, width_bottom))
        height = int(max(height_left, height_right))

        if width < 24 or height < 10:
            return None

        destination = np.array(
            [
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1],
            ],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(ordered, destination)
        warped = cv2.warpPerspective(
            crop,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return LicensePlateRecognizer._tight_crop(warped)

    @staticmethod
    def _find_plate_contour(crop: np.ndarray) -> Optional[np.ndarray]:
        masks = LicensePlateRecognizer._build_plate_masks(crop)
        crop_area = crop.shape[0] * crop.shape[1]
        best_contour: Optional[np.ndarray] = None
        best_score = 0.0

        for mask in masks:
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < crop_area * 0.08:
                    continue

                rect = cv2.minAreaRect(contour)
                width, height = rect[1]
                if min(width, height) <= 0:
                    continue

                ratio = max(width, height) / float(min(width, height))
                if ratio < 2.0 or ratio > 7.5:
                    continue

                fill_ratio = area / float(width * height)
                score = area / crop_area + fill_ratio * 0.3
                if score > best_score:
                    best_score = score
                    best_contour = contour

        return best_contour

    @staticmethod
    def _build_plate_masks(crop: np.ndarray) -> Sequence[np.ndarray]:
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        masks = [
            cv2.inRange(hsv, (95, 60, 60), (140, 255, 255)),
            cv2.inRange(hsv, (15, 60, 60), (40, 255, 255)),
            cv2.inRange(hsv, (35, 40, 40), (95, 255, 255)),
        ]

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 7, 50, 50)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        masks.extend([thresh, cv2.bitwise_not(thresh)])

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
        refined = [
            cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            for mask in masks
        ]
        return refined

    @staticmethod
    def _tight_crop(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        boxes = []
        for mask in (thresh, cv2.bitwise_not(thresh)):
            ys, xs = np.where(mask > 0)
            if len(xs) == 0 or len(ys) == 0:
                continue
            x1, x2 = int(xs.min()), int(xs.max())
            y1, y2 = int(ys.min()), int(ys.max())
            boxes.append((x1, y1, x2, y2))

        if not boxes:
            return image

        x1 = min(box[0] for box in boxes)
        y1 = min(box[1] for box in boxes)
        x2 = max(box[2] for box in boxes)
        y2 = max(box[3] for box in boxes)

        pad_x = max(2, int((x2 - x1) * 0.04))
        pad_y = max(2, int((y2 - y1) * 0.08))
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(image.shape[1], x2 + pad_x)
        y2 = min(image.shape[0], y2 + pad_y)
        return image[y1:y2, x1:x2]

    @staticmethod
    def _order_points(points: np.ndarray) -> np.ndarray:
        sums = points.sum(axis=1)
        diffs = np.diff(points, axis=1)
        ordered = np.zeros((4, 2), dtype=np.float32)
        ordered[0] = points[np.argmin(sums)]
        ordered[2] = points[np.argmax(sums)]
        ordered[1] = points[np.argmin(diffs)]
        ordered[3] = points[np.argmax(diffs)]
        return ordered
