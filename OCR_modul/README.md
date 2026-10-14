# Offline OCR Module — Multimodal RAG

OCR component of the **Offline Multimodal RAG** final-year project. It extracts text from
**images** and **scanned PDFs** using Tesseract (no internet needed) and outputs
**LangChain `Document`s** ready for embedding and storage in a vector DB.

## How it fits in the pipeline

```
Image / scanned PDF -> preprocess (OpenCV) -> Tesseract OCR -> LangChain Document
                                                                   |
                                    (teammates) embeddings -> Chroma/FAISS -> local LLM
```

## Install

1. Install the Tesseract engine (one-time; the language data works offline afterwards):
   - Ubuntu/Debian: `sudo apt install tesseract-ocr` (extra languages: `tesseract-ocr-hin`, etc.)
   - Windows: installer from https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
2. Python packages:
   ```bash
   python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Usage

CLI:
```bash
python -m ocr_module.cli path/to/image.png
python -m ocr_module.cli path/to/scan.pdf --out output.json
python -m ocr_module.cli ./uploads --lang eng+hin
```

Python / LangChain:
```python
from ocr_module import OCRDocumentLoader, load_documents

docs = OCRDocumentLoader("uploads/invoice.jpg").load()   # list[Document]
print(docs[0].page_content, docs[0].metadata)

all_docs = load_documents("uploads/")                    # whole folder
```

Hand `docs` to the embedding step, e.g.:
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
chunks = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100).split_documents(docs)
# vectorstore = Chroma.from_documents(chunks, embedding=<local HF embeddings>)
```

## Metadata on each Document
`source`, `modality` (image/pdf), `page`, `ocr_confidence`, and for PDFs `extraction_method`
(`text-layer` or `ocr`).

## Windows tip
Pass the executable path if Tesseract isn't on PATH:
`--tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"`

## Tests
```bash
pytest
```
