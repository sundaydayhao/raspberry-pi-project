from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np


@dataclass
class PlateCandidate:
    bbox: Tuple[int, int, int, int]
    score: float
    source: str


class LicensePlateDetector:
    def __init__(self, max_processing_width: int = 960) -> None:
        self.max_processing_width = max_processing_width
        self._cascade = self._load_cascade()

    def detect(self, image: np.ndarray, top_k: int = 10) -> List[PlateCandidate]:
        if image is None or image.size == 0:
            return []

        resized, scale = self._resize_for_detection(image)
        color_candidates = self._detect_by_color(resized)
        contour_candidates = self._detect_by_contours(resized)
        cascade_candidates = self._detect_by_cascade(resized)
        merged = self._merge_candidates(
            color_candidates + contour_candidates + cascade_candidates
        )

        results: List[PlateCandidate] = []
        for candidate in merged[:top_k]:
            x, y, w, h = candidate.bbox
            bbox = (
                int(x / scale),
                int(y / scale),
                int(w / scale),
                int(h / scale),
            )
            results.append(
                PlateCandidate(
                    bbox=self._clip_bbox(bbox, image.shape[1], image.shape[0]),
                    score=candidate.score,
                    source=candidate.source,
                )
            )
        return results

    def _resize_for_detection(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        height, width = image.shape[:2]
        if width <= self.max_processing_width:
            return image.copy(), 1.0

        scale = self.max_processing_width / float(width)
        resized = cv2.resize(
            image,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
        return resized, scale

    def _detect_by_contours(self, image: np.ndarray) -> List[PlateCandidate]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
        square_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kernel)
        grad_x = cv2.Sobel(blackhat, cv2.CV_32F, 1, 0, ksize=3)
        grad_x = np.absolute(grad_x)
        grad_x = self._normalize_to_uint8(grad_x)
        grad_x = cv2.GaussianBlur(grad_x, (5, 5), 0)
        grad_x = cv2.morphologyEx(grad_x, cv2.MORPH_CLOSE, rect_kernel)

        thresh = cv2.threshold(
            grad_x, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )[1]
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, square_kernel)
        thresh = cv2.erode(thresh, None, iterations=1)
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        image_area = image.shape[0] * image.shape[1]
        candidates: List[PlateCandidate] = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if area < image_area * 0.001 or h == 0:
                continue

            ratio = w / float(h)
            if ratio < 2.0 or ratio > 6.5:
                continue

            rect_area = cv2.contourArea(contour)
            fill_ratio = rect_area / float(area)
            if fill_ratio < 0.35:
                continue

            score = min(1.0, 0.45 + fill_ratio * 0.35 + min(ratio, 5.5) / 10.0)
            candidates.append(
                PlateCandidate(
                    bbox=self._expand_bbox((x, y, w, h), image.shape[1], image.shape[0]),
                    score=score,
                    source="contour",
                )
            )

        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def _detect_by_color(self, image: np.ndarray) -> List[PlateCandidate]:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        masks = [
            cv2.inRange(hsv, (95, 70, 70), (140, 255, 255)),
            cv2.inRange(hsv, (15, 70, 70), (40, 255, 255)),
            cv2.inRange(hsv, (35, 45, 45), (95, 255, 255)),
        ]

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
        image_area = image.shape[0] * image.shape[1]
        candidates: List[PlateCandidate] = []

        for mask in masks:
            refined = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            refined = cv2.dilate(refined, kernel, iterations=1)
            contours, _ = cv2.findContours(
                refined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                if area < image_area * 0.0008 or h == 0:
                    continue

                ratio = w / float(h)
                if ratio < 2.0 or ratio > 6.8:
                    continue

                fill_ratio = cv2.contourArea(contour) / float(area)
                if fill_ratio < 0.45:
                    continue

                score = min(1.0, 0.55 + fill_ratio * 0.25 + min(ratio, 5.5) / 10.0)
                candidates.append(
                    PlateCandidate(
                        bbox=self._expand_bbox(
                            (x, y, w, h), image.shape[1], image.shape[0], pad_ratio=0.05
                        ),
                        score=score,
                        source="color",
                    )
                )

        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def _detect_by_cascade(self, image: np.ndarray) -> List[PlateCandidate]:
        if self._cascade is None:
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detections = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=3,
            minSize=(60, 20),
        )

        candidates: List[PlateCandidate] = []
        for x, y, w, h in detections:
            ratio = w / float(max(h, 1))
            if ratio < 2.0 or ratio > 6.5:
                continue
            candidates.append(
                PlateCandidate(
                    bbox=self._expand_bbox((x, y, w, h), image.shape[1], image.shape[0]),
                    score=0.9,
                    source="cascade",
                )
            )
        return candidates

    def _merge_candidates(
        self, candidates: Sequence[PlateCandidate]
    ) -> List[PlateCandidate]:
        merged: List[PlateCandidate] = []
        for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
            if any(self._iou(candidate.bbox, saved.bbox) > 0.4 for saved in merged):
                continue
            merged.append(candidate)
        return merged

    @staticmethod
    def _normalize_to_uint8(image: np.ndarray) -> np.ndarray:
        min_val = float(image.min())
        max_val = float(image.max())
        if max_val - min_val < 1e-6:
            return np.zeros_like(image, dtype=np.uint8)
        normalized = ((image - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
        return normalized

    @staticmethod
    def _expand_bbox(
        bbox: Tuple[int, int, int, int], width: int, height: int, pad_ratio: float = 0.08
    ) -> Tuple[int, int, int, int]:
        x, y, w, h = bbox
        pad_x = int(w * pad_ratio)
        pad_y = int(h * pad_ratio)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(width, x + w + pad_x)
        y2 = min(height, y + h + pad_y)
        return x1, y1, x2 - x1, y2 - y1

    @staticmethod
    def _clip_bbox(
        bbox: Tuple[int, int, int, int], width: int, height: int
    ) -> Tuple[int, int, int, int]:
        x, y, w, h = bbox
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        return x, y, w, h

    @staticmethod
    def _iou(
        left: Tuple[int, int, int, int], right: Tuple[int, int, int, int]
    ) -> float:
        lx, ly, lw, lh = left
        rx, ry, rw, rh = right
        left_x2 = lx + lw
        left_y2 = ly + lh
        right_x2 = rx + rw
        right_y2 = ry + rh

        inter_x1 = max(lx, rx)
        inter_y1 = max(ly, ry)
        inter_x2 = min(left_x2, right_x2)
        inter_y2 = min(left_y2, right_y2)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        if inter_area == 0:
            return 0.0

        union_area = lw * lh + rw * rh - inter_area
        return inter_area / float(max(union_area, 1))

    @staticmethod
    def _load_cascade() -> Optional[cv2.CascadeClassifier]:
        candidates = []
        cv2_data = getattr(cv2, "data", None)
        haarcascades = getattr(cv2_data, "haarcascades", None)
        if haarcascades:
            candidates.append(
                Path(haarcascades) / "haarcascade_russian_plate_number.xml"
            )

        candidates.extend(
            [
                Path("/usr/share/opencv4/haarcascades/haarcascade_russian_plate_number.xml"),
                Path("/usr/share/opencv/haarcascades/haarcascade_russian_plate_number.xml"),
            ]
        )

        for path in candidates:
            if not path.exists():
                continue
            cascade = cv2.CascadeClassifier(str(path))
            if not cascade.empty():
                return cascade
        return None
