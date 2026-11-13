"""
exporter.py - save an agent answer as PDF and Word (English only)

Install:  python -m pip install reportlab python-docx
Use:      from exporter import save_answer
          save_answer(question, answer)   # -> {"pdf": path, "docx": path}
"""

import os
import re
from datetime import datetime
from xml.sax.saxutils import escape

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def clean(text):
    """Remove the model's <think>...</think> part if it leaked into the answer."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    return text.split("</think>")[-1].strip()


def plain(text):
    """Turn markdown links into 'label (url)' and drop backticks."""
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        lambda m: m[1] if m[1] == m[2] else f"{m[1]} ({m[2]})",
        text,
    )
    return text.replace("`", "")


def parse(text):
    """Split markdown into [(kind, text)], kind = h1/h2/h3/bullet/text."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"[-*_]{3,}", line):
            continue
        if m := re.match(r"(#{1,3})\s+(.*)", line):
            items.append((f"h{len(m[1])}", m[2]))
        elif m := re.match(r"[-*•]\s+(.*)", line):
            items.append(("bullet", m[1]))
        else:
            items.append(("text", line))
    return items


def save_pdf(path, title, items):
    styles = getSampleStyleSheet()

    def fix(text):
        # the built-in PDF font only knows Latin-1 characters
        text = escape(plain(text)).encode("cp1252", "replace").decode("cp1252")
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    story = [Paragraph(fix(title), styles["Title"])]
    for kind, text in items:
        if kind == "bullet":
            story.append(Paragraph(fix(text), styles["Bullet"], bulletText="•"))
        else:
            style = {"h1": "Heading1", "h2": "Heading2", "h3": "Heading3"}.get(kind, "Normal")
            story.append(Paragraph(fix(text), styles[style]))
        story.append(Spacer(1, 4))
    SimpleDocTemplate(path, pagesize=A4).build(story)


def save_docx(path, title, items):
    doc = Document()
    doc.add_heading(title, 0)
    for kind, text in items:
        text = plain(text)
        if kind.startswith("h"):
            doc.add_heading(text.replace("**", ""), int(kind[1]))
            continue
        p = doc.add_paragraph(style="List Bullet" if kind == "bullet" else None)
        for part in re.split(r"(\*\*.+?\*\*)", text):
            if len(part) > 4 and part.startswith("**") and part.endswith("**"):
                p.add_run(part[2:-2]).bold = True
            elif part:
                p.add_run(part)
    doc.save(path)


def save_answer(question, answer, out_dir="outputs"):
    answer = clean(answer or "")
    if not answer:
        print("           ! Empty answer, nothing saved.")
        return {}

    os.makedirs(out_dir, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "_", question)[:40].strip("_") or "answer"
    base = os.path.join(out_dir, f"{datetime.now():%Y%m%d_%H%M%S}_{slug}")
    items = parse(answer)

    saved = {}
    for ext, writer in (("pdf", save_pdf), ("docx", save_docx)):
        try:
            writer(f"{base}.{ext}", question, items)
            saved[ext] = f"{base}.{ext}"
        except Exception as e:  # noqa: BLE001
            print(f"           ! Could not save {ext}: {type(e).__name__}: {e}")
    return saved
