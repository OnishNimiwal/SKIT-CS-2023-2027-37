import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont

from ocr_module import OCREngine, load_documents

pytestmark = pytest.mark.skipif(shutil.which("tesseract") is None,
                                reason="Tesseract not installed")


def _make_image(path, text="Offline Multimodal RAG"):
    img = Image.new("RGB", (900, 200), "white")
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(img).text((30, 60), text, fill="black", font=font)
    img.save(path)


def test_image_ocr(tmp_path):
    p = tmp_path / "sample.png"
    _make_image(p)
    result = OCREngine().image_to_result(str(p))
    assert "RAG" in result.text
    assert result.confidence > 50


def test_loader_returns_documents(tmp_path):
    p = tmp_path / "sample.png"
    _make_image(p)
    docs = load_documents(str(p))
    assert len(docs) == 1
    assert docs[0].metadata["modality"] == "image"
