from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
import pytesseract

from .postprocess import (
    PROVINCE_CHARS,
    PROVINCE_SET,
    extract_plate_suffix,
    normalize_plate_text,
    normalize_province_char,
    repair_plate_text,
    score_plate_text,
)


@dataclass
class OCRResult:
    text: str
    confidence: float
    score: float


class PlateOCR:
    def __init__(self, lang: str = "chi_sim+eng") -> None:
        self.lang = lang
        whitelist = PROVINCE_CHARS + "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
        self.configs = (
            f"--oem 1 --psm 7 -c tessedit_char_whitelist={whitelist}",
            f"--oem 1 --psm 8 -c tessedit_char_whitelist={whitelist}",
            "--oem 1 --psm 7",
            "--oem 1 --psm 8",
        )

    def read(self, image: np.ndarray) -> OCRResult:
        variants = self._build_variants(image)
        best = OCRResult(text="", confidence=0.0, score=0.0)
        attempts: List[Tuple[str, float, OCRResult]] = []

        for variant in variants:
            for config in self.configs:
                try:
                    raw_text, confidence = self._run_tesseract(variant, config)
                except pytesseract.TesseractNotFoundError as exc:
                    raise RuntimeError(
                        "tesseract is not installed. Run install.sh or install "
                        "tesseract-ocr and tesseract-ocr-chi-sim."
                    ) from exc

                repaired = repair_plate_text(raw_text)
                score = score_plate_text(repaired, confidence)
                candidate = OCRResult(text=repaired, confidence=confidence, score=score)
                attempts.append((raw_text, confidence, candidate))
                if score > best.score:
                    best = candidate

        fused = self._fuse_attempts(attempts)
        if fused is not None and fused.score > best.score:
            best = fused

        return best

    def _build_variants(self, image: np.ndarray) -> List[np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        scale = max(2, int(160 / max(gray.shape[0], 1)))
        enlarged = cv2.resize(
            gray,
            (gray.shape[1] * scale, gray.shape[0] * scale),
            interpolation=cv2.INTER_CUBIC,
        )
        blurred = cv2.bilateralFilter(enlarged, 7, 50, 50)
        global_thresh = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )[1]
        adaptive_thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            9,
        )
        inverted = cv2.bitwise_not(global_thresh)
        return [enlarged, global_thresh, adaptive_thresh, inverted]

    def _run_tesseract(self, image: np.ndarray, config: str) -> tuple[str, float]:
        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            config=config,
            output_type=pytesseract.Output.DICT,
        )
        texts: List[str] = []
        confidences: List[float] = []

        for text, conf in zip(data["text"], data["conf"]):
            text = str(text).strip()
            try:
                conf_value = float(conf)
            except (TypeError, ValueError):
                conf_value = -1.0

            if text:
                texts.append(text)
            if conf_value >= 0:
                confidences.append(conf_value)

        joined = "".join(texts)
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return joined, average_confidence

    def _fuse_attempts(
        self, attempts: List[Tuple[str, float, OCRResult]]
    ) -> Optional[OCRResult]:
        best_province: Optional[Tuple[str, float]] = None
        best_suffix: Optional[Tuple[str, float, Tuple[int, int, int, float]]] = None

        for raw_text, confidence, _ in attempts:
            province = self._extract_province_prefix(raw_text)
            if province is not None:
                if best_province is None or confidence > best_province[1]:
                    best_province = (province, confidence)

            suffix = extract_plate_suffix(raw_text)
            if suffix and suffix[0].isalpha():
                suffix_rank = (
                    1 if len(suffix) == 6 else 0,
                    sum(ch.isdigit() for ch in suffix[1:]),
                    -sum(ch.isalpha() for ch in suffix[1:]),
                    confidence,
                )
                if best_suffix is None or suffix_rank > best_suffix[2]:
                    best_suffix = (suffix, confidence, suffix_rank)

        if best_province is None or best_suffix is None:
            return None

        plate = best_province[0] + best_suffix[0]
        confidence = max(best_province[1], best_suffix[1])
        score = min(1.0, score_plate_text(plate, confidence) + 0.08)
        return OCRResult(text=plate, confidence=confidence, score=score)

    @staticmethod
    def _extract_province_prefix(raw_text: str) -> Optional[str]:
        normalized = normalize_plate_text(raw_text)
        if not normalized:
            return None

        province = normalize_province_char(normalized[0])
        if province in PROVINCE_SET:
            return province
        return None
