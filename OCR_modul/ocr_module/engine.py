"""Tesseract-based OCR engine. Runs 100% offline once Tesseract is installed."""
from __future__ import annotations

from dataclasses import dataclass

import pytesseract
from pytesseract import Output

from .preprocess import preprocess, to_cv2


@dataclass
class OCRResult:
    text: str
    confidence: float  # mean word confidence, 0-100
    word_count: int


class OCREngine:
    def __init__(
        self,
        lang: str = "eng",
        psm: int = 3,
        use_preprocessing: bool = True,
        min_word_conf: float = 30.0,
        tesseract_cmd: str | None = None,
    ):
        """
        lang:  Tesseract language code(s), e.g. "eng" or "eng+hin".
        psm:   Page segmentation mode (3 = auto, 6 = single block, 11 = sparse text).
        """
        if tesseract_cmd:  # e.g. r"C:\Program Files\Tesseract-OCR\tesseract.exe" on Windows
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.lang = lang
        self.config = f"--oem 3 --psm {psm}"
        self.use_preprocessing = use_preprocessing
        self.min_word_conf = min_word_conf

    def image_to_result(self, image) -> OCRResult:
        """OCR a path / PIL image / numpy array."""
        processed = preprocess(image) if self.use_preprocessing else to_cv2(image)

        text = pytesseract.image_to_string(processed, lang=self.lang, config=self.config)
        data = pytesseract.image_to_data(
            processed, lang=self.lang, config=self.config, output_type=Output.DICT
        )

        confs = [
            float(c)
            for c, w in zip(data["conf"], data["text"])
            if w.strip() and float(c) >= 0
        ]
        confidence = sum(confs) / len(confs) if confs else 0.0
        return OCRResult(text=self._clean(text), confidence=round(confidence, 2),
                         word_count=len(confs))

    def image_to_text(self, image) -> str:
        return self.image_to_result(image).text

    @staticmethod
    def _clean(text: str) -> str:
        lines = [ln.rstrip() for ln in text.splitlines()]
        cleaned, blank = [], 0
        for ln in lines:  # collapse runs of blank lines
            blank = blank + 1 if not ln.strip() else 0
            if blank <= 1:
                cleaned.append(ln)
        return "\n".join(cleaned).strip()
