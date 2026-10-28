"""Command line: python -m ocr_module.cli <image|pdf|folder> [--lang eng] [--out out.json]"""
import argparse
import json

from .engine import OCREngine
from .loader import load_documents


def main():
    ap = argparse.ArgumentParser(description="Offline OCR for images and scanned PDFs")
    ap.add_argument("path", help="image, PDF, or folder")
    ap.add_argument("--lang", default="eng", help="Tesseract language(s), e.g. eng+hin")
    ap.add_argument("--psm", type=int, default=3)
    ap.add_argument("--no-preprocess", action="store_true")
    ap.add_argument("--tesseract-cmd", default=None, help="Path to tesseract executable")
    ap.add_argument("--out", help="Save extracted documents as JSON")
    args = ap.parse_args()

    engine = OCREngine(lang=args.lang, psm=args.psm,
                       use_preprocessing=not args.no_preprocess,
                       tesseract_cmd=args.tesseract_cmd)
    docs = load_documents(args.path, engine)

    for d in docs:
        m = d.metadata
        print(f"\n=== {m['source']} (page {m.get('page')}, "
              f"confidence {m.get('ocr_confidence')}) ===")
        print(d.page_content)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump([{"text": d.page_content, "metadata": d.metadata} for d in docs],
                      f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(docs)} document(s) to {args.out}")


if __name__ == "__main__":
    main()
