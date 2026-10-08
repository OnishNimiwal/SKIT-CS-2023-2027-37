"""Image pre-processing to improve OCR accuracy (fully offline, OpenCV only)."""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def to_cv2(image) -> np.ndarray:
    """Accept a file path, PIL image, or numpy array and return a BGR/gray ndarray."""
    if isinstance(image, (str, bytes)) or hasattr(image, "__fspath__"):
        img = cv2.imread(str(image))
        if img is None:
            raise ValueError(f"Could not read image: {image}")
        return img
    if isinstance(image, Image.Image):
        return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    if isinstance(image, np.ndarray):
        return image
    raise TypeError(f"Unsupported image type: {type(image)}")


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Straighten slightly rotated scans."""
    inverted = cv2.bitwise_not(gray)
    _, bw = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = cv2.findNonZero(bw)
    if coords is None or len(coords) < 50:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    # Normalise OpenCV's angle convention across versions
    if angle > 45:
        angle -= 90
    elif angle < -45:
        angle += 90
    if abs(angle) < 0.3 or abs(angle) > 15:  # ignore noise / implausible skew
        return gray
    h, w = gray.shape
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def preprocess(image, min_height: int = 1000) -> np.ndarray:
    """grayscale -> upscale (if small) -> denoise -> deskew -> adaptive threshold."""
    img = to_cv2(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

    if gray.shape[0] < min_height:  # small images OCR poorly
        scale = min_height / gray.shape[0]
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.fastNlMeansDenoising(gray, None, h=15)
    gray = _deskew(gray)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
