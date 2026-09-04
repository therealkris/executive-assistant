#!/usr/bin/env python3
"""Render receipt text into a plain PDF. Stdlib only — no dependencies.

Used by the receipt-forward skill when a vendor's receipt lives only in the email
body (no PDF attachment). Expense tools like Expensify SmartScan read attachments,
not forwarded email text, so the receipt has to become a file.

Usage:
    python3 receipt_to_pdf.py --out /tmp/acme-2026-08-25.pdf --title "Acme SaaS — Receipt" <<'EOF'
    Vendor: Acme SaaS
    Amount: $298.51 USD
    Date: Aug 25, 2026
    Billing period: Aug 25, 2026 - Sep 25, 2026
    Invoice ID: in_1U8MYUIvcqWR3dFDBlmLLJVk
    Plan: Professional team (monthly)
    EOF

Reads the receipt body from stdin (or --text-file). Writes a single PDF, paginating
if the text is long. Exit 0 on success; the path is echoed to stdout.
"""

import argparse
import sys

PAGE_W, PAGE_H = 612, 792          # US Letter, 72 dpi
MARGIN_X, MARGIN_TOP = 60, 72
TITLE_SIZE, BODY_SIZE, LEADING = 16, 11, 16
MAX_CHARS = 92                      # conservative wrap for Helvetica 11pt
BOTTOM = 60


def esc(text):
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def wrap(line, width=MAX_CHARS):
    if len(line) <= width:
        return [line]
    out, cur = [], ""
    for word in line.split(" "):
        while len(word) > width:                 # break pathological tokens (IDs, URLs)
            if cur:
                out.append(cur)
                cur = ""
            out.append(word[:width])
            word = word[width:]
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def paginate(lines, title):
    """Split wrapped lines into pages. The title only appears on page 1."""
    pages, cur = [], []
    y = MARGIN_TOP + (TITLE_SIZE + LEADING if title else 0)
    for line in lines:
        if y + LEADING > PAGE_H - BOTTOM:
            pages.append(cur)
            cur, y = [], MARGIN_TOP
        cur.append(line)
        y += LEADING
    pages.append(cur)
    return pages


def page_stream(lines, title, first_page):
    parts = ["BT"]
    y = PAGE_H - MARGIN_TOP
    if title and first_page:
        parts.append(f"/F2 {TITLE_SIZE} Tf 1 0 0 1 {MARGIN_X} {y} Tm ({esc(title)}) Tj")
        y -= TITLE_SIZE + LEADING
    parts.append(f"/F1 {BODY_SIZE} Tf 1 0 0 1 {MARGIN_X} {y} Tm {LEADING} TL")
    for i, line in enumerate(lines):
        if i:
            parts.append("T*")
        parts.append(f"({esc(line)}) Tj")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", "replace")


def build_pdf(text, title):
    lines = []
    for raw in text.splitlines():
        lines.extend(wrap(raw.rstrip()) if raw.strip() else [""])
    pages = paginate(lines, title)

    objects = []                                  # 1-indexed on output
    n_pages = len(pages)
    font_regular = 3 + 2 * n_pages
    font_bold = font_regular + 1

    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n_pages))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(
        f"<< /Type /Pages /Count {n_pages} /Kids [{kids}] >>".encode()
    )
    for i, page_lines in enumerate(pages):
        content = page_stream(page_lines, title, i == 0)
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 {font_regular} 0 R /F2 {font_bold} 0 R >> >> "
                f"/Contents {4 + 2 * i} 0 R >>"
            ).encode()
        )
        objects.append(
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    ).encode()
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description="Render receipt text to a PDF (stdlib only).")
    ap.add_argument("--out", required=True, help="output PDF path")
    ap.add_argument("--title", default="", help="heading line for page 1")
    ap.add_argument("--text-file", help="read body from this file instead of stdin")
    args = ap.parse_args()

    text = open(args.text_file, encoding="utf-8").read() if args.text_file else sys.stdin.read()
    if not text.strip():
        sys.exit("receipt_to_pdf: refusing to write an empty PDF — no receipt text supplied")

    with open(args.out, "wb") as fh:
        fh.write(build_pdf(text, args.title))
    print(args.out)


if __name__ == "__main__":
    main()
