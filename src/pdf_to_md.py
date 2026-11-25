"""Convert PDFs to Markdown, keeping tables and page markers.

Usage:
    pip install pymupdf4llm
    python pdf_to_md.py report.pdf                 # one file
    python pdf_to_md.py docs/ -o markdown/         # every PDF in a folder

Each page is marked with <!-- page N --> so passages can be traced back
to the page of the original PDF. OCR is switched off: these reports have
a real text layer. If the converter returns nothing for a page, the plain
text of that page is used instead and the page is counted as a fallback.
"""
import argparse
import pathlib
import sys

import pymupdf
import pymupdf4llm


def to_page_chunks(pdf: pathlib.Path) -> list[dict]:
    try:
        return pymupdf4llm.to_markdown(str(pdf), page_chunks=True, use_ocr=False)
    except TypeError:  # older pymupdf4llm without the use_ocr option
        return pymupdf4llm.to_markdown(str(pdf), page_chunks=True)


def convert(pdf: pathlib.Path, out_dir: pathlib.Path) -> tuple[pathlib.Path, int, int]:
    chunks = to_page_chunks(pdf)
    doc = pymupdf.open(str(pdf))
    parts = [f"<!-- source: {pdf.name} -->"]
    fallbacks = 0
    empty = 0
    for index, page in enumerate(doc):
        text = chunks[index]["text"].strip() if index < len(chunks) else ""
        if not text:
            text = page.get_text().strip()
            if text:
                fallbacks += 1
            else:
                empty += 1
        parts.append(f"\n\n<!-- page {index + 1} -->\n\n{text}")
    out = out_dir / f"{pdf.stem}.md"
    out.write_text("".join(parts) + "\n", encoding="utf-8")
    return out, fallbacks, empty


def collect(inputs: list[pathlib.Path]) -> list[pathlib.Path]:
    pdfs: list[pathlib.Path] = []
    for item in inputs:
        if not item.exists():
            sys.exit(f"Path not found: {str(item.resolve())!r}  (check for hidden spaces in the name)")
        if item.is_dir():
            pdfs.extend(sorted(p for p in item.iterdir() if p.suffix.lower() == ".pdf"))
        else:
            pdfs.append(item)
    return pdfs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", type=pathlib.Path, help="PDF files or folders of PDFs")
    parser.add_argument("-o", "--out", type=pathlib.Path, default=None,
                        help="output folder (default: next to each PDF)")
    args = parser.parse_args()

    pdfs = collect(args.inputs)
    if not pdfs:
        sys.exit("No PDFs found.")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)

    failed = 0
    for pdf in pdfs:
        try:
            out, fallbacks, empty = convert(pdf, args.out or pdf.parent)
            note = ""
            if fallbacks:
                note += f"  ({fallbacks} pages used plain-text fallback)"
            if empty:
                note += f"  ({empty} pages have no text at all - probably images)"
            print(f"ok    {pdf.name} -> {out}{note}")
        except Exception as error:  # keep going if one file is broken
            failed += 1
            print(f"FAIL  {pdf.name}: {error}", file=sys.stderr)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()