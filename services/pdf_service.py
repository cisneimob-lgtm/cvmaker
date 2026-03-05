import os
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

PAGE_W, PAGE_H = A4


def _wrap_lines(c, text, max_width, font="Helvetica", size=10):
    c.setFont(font, size)
    words = (text or "").split()
    lines = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _draw_paragraph(c, x, y, text, max_width, line_height=12, font="Helvetica", size=10):
    lines = _wrap_lines(c, text, max_width, font, size)
    c.setFont(font, size)
    for ln in lines:
        c.drawString(x, y, ln)
        y -= line_height
    return y


def build_pdf(cv: dict) -> str:
    template = cv.get("template", "ats")
    if template == "modern":
        return _build_pdf_modern(cv)
    if template == "minimal":
        return _build_pdf_minimal(cv)
    return _build_pdf_ats(cv)


def _build_pdf_ats(cv: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    c = canvas.Canvas(path, pagesize=A4)
    margin = 48
    x = margin
    y = PAGE_H - margin
    max_width = PAGE_W - 2 * margin

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, cv.get("name", ""))
    y -= 20

    c.setFont("Helvetica", 11)
    if cv.get("title"):
        c.drawString(x, y, cv["title"])
        y -= 16

    contact = " • ".join([v for v in [cv.get("email"), cv.get("phone"), cv.get("city")] if v])
    links = " | ".join([v for v in [cv.get("linkedin"), cv.get("github"), cv.get("portfolio")] if v])

    c.setFont("Helvetica", 10)
    if contact:
        c.drawString(x, y, contact)
        y -= 14
    if links:
        y = _draw_paragraph(c, x, y, links, max_width, 12, "Helvetica", 9)
        y -= 4

    def section(title):
        nonlocal y
        y -= 6
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, title.upper())
        y -= 12

    # Summary
    if cv.get("summary"):
        section("Resumo" if cv.get("lang","pt")=="pt" else "Summary")
        y = _draw_paragraph(c, x, y, cv["summary"], max_width)
        y -= 6

    # Objective
    if cv.get("objective"):
        section("Objetivo" if cv.get("lang","pt")=="pt" else "Objective")
        y = _draw_paragraph(c, x, y, cv["objective"], max_width)
        y -= 6

    # Skills
    skills = cv.get("skills") or []
    if skills:
        section("Habilidades" if cv.get("lang","pt")=="pt" else "Skills")
        y = _draw_paragraph(c, x, y, ", ".join(skills), max_width)
        y -= 6

    # Experience
    exp = cv.get("experience") or []
    if exp:
        section("Experiência" if cv.get("lang","pt")=="pt" else "Experience")
        for line in exp:
            if line.startswith("•"):
                c.setFont("Helvetica", 10)
                y = _draw_paragraph(c, x + 12, y, line, max_width - 12)
            else:
                c.setFont("Helvetica-Bold", 10)
                y = _draw_paragraph(c, x, y, line, max_width)
            y -= 2
        y -= 6

    # Education
    edu = cv.get("education") or []
    if edu:
        section("Formação" if cv.get("lang","pt")=="pt" else "Education")
        for line in edu:
            y = _draw_paragraph(c, x, y, line, max_width)
            y -= 2
        y -= 6

    # Certs
    certs = cv.get("certs") or []
    if certs:
        section("Certificações" if cv.get("lang","pt")=="pt" else "Certifications")
        for line in certs:
            y = _draw_paragraph(c, x, y, line, max_width)
            y -= 2
        y -= 6

    # Languages
    langs = cv.get("languages") or []
    if langs:
        section("Idiomas" if cv.get("lang","pt")=="pt" else "Languages")
        for line in langs:
            y = _draw_paragraph(c, x, y, line, max_width)
            y -= 2

    c.showPage()
    c.save()
    return path


def _build_pdf_modern(cv: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    c = canvas.Canvas(path, pagesize=A4)
    margin = 48
    max_width = PAGE_W - 2 * margin

    # Header bar
    c.setFillGray(0.12)
    c.rect(0, PAGE_H - 120, PAGE_W, 120, fill=1, stroke=0)
    c.setFillGray(1)

    x = margin
    y = PAGE_H - 48
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, cv.get("name", ""))
    y -= 22
    c.setFont("Helvetica", 11)
    c.drawString(x, y, cv.get("title", ""))
    y -= 18

    # Photo right (optional)
    photo = cv.get("photo_path")
    if photo:
        try:
            img = ImageReader(photo)
            size = 72
            px = PAGE_W - margin - size
            py = PAGE_H - 48 - size + 8
            c.drawImage(img, px, py, size, size, mask="auto", preserveAspectRatio=True, anchor="c")
        except Exception:
            pass

    c.setFont("Helvetica", 9)
    contact = " • ".join([v for v in [cv.get("email"), cv.get("phone"), cv.get("city")] if v])
    links = " | ".join([v for v in [cv.get("linkedin"), cv.get("github"), cv.get("portfolio")] if v])
    if contact:
        c.drawString(x, PAGE_H - 110, contact)
    if links:
        c.drawString(x, PAGE_H - 124, links)

    y = PAGE_H - 150
    c.setFillGray(0)
    c.setStrokeGray(0.85)

    def section(title):
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, title)
        y -= 8
        c.line(margin, y, PAGE_W - margin, y)
        y -= 14

    def para(text, size=10):
        nonlocal y
        y = _draw_paragraph(c, margin, y, text, max_width, 12, "Helvetica", size)
        y -= 6

    lang = cv.get("lang", "pt")
    L = {
        "Resumo": "Resumo" if lang=="pt" else "Summary",
        "Habilidades": "Habilidades" if lang=="pt" else "Skills",
        "Experiência": "Experiência" if lang=="pt" else "Experience",
        "Formação": "Formação" if lang=="pt" else "Education",
        "Certificações": "Certificações" if lang=="pt" else "Certifications",
        "Idiomas": "Idiomas" if lang=="pt" else "Languages",
        "Objetivo": "Objetivo" if lang=="pt" else "Objective",
    }

    if cv.get("summary"):
        section(L["Resumo"])
        para(cv["summary"], 10)

    if cv.get("objective"):
        section(L["Objetivo"])
        para(cv["objective"], 10)

    skills = cv.get("skills") or []
    if skills:
        section(L["Habilidades"])
        para(" • ".join(skills), 10)

    exp = cv.get("experience") or []
    if exp:
        section(L["Experiência"])
        for line in exp:
            if line.startswith("•"):
                para(line, 10)
            else:
                c.setFont("Helvetica-Bold", 10)
                y = _draw_paragraph(c, margin, y, line, max_width, 12, "Helvetica-Bold", 10)
                y -= 2
        y -= 6

    edu = cv.get("education") or []
    if edu:
        section(L["Formação"])
        for line in edu:
            para(line, 10)

    certs = cv.get("certs") or []
    if certs:
        section(L["Certificações"])
        for line in certs:
            para(line, 10)

    langs = cv.get("languages") or []
    if langs:
        section(L["Idiomas"])
        for line in langs:
            para(line, 10)

    c.showPage()
    c.save()
    return path


def _build_pdf_minimal(cv: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    c = canvas.Canvas(path, pagesize=A4)
    margin = 56
    x = margin
    y = PAGE_H - margin
    max_width = PAGE_W - 2 * margin

    c.setFont("Helvetica-Bold", 20)
    c.drawString(x, y, cv.get("name", ""))
    y -= 22
    c.setFont("Helvetica", 11)
    c.drawString(x, y, cv.get("title", ""))
    y -= 16
    c.setFont("Helvetica", 9)

    contact = " • ".join([v for v in [cv.get("email"), cv.get("phone"), cv.get("city")] if v])
    if contact:
        c.drawString(x, y, contact)
        y -= 12

    links = " | ".join([v for v in [cv.get("linkedin"), cv.get("github"), cv.get("portfolio")] if v])
    if links:
        y = _draw_paragraph(c, x, y, links, max_width, 11, "Helvetica", 9)
        y -= 4

    def section(title):
        nonlocal y
        y -= 8
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, title.upper())
        y -= 14
        c.setFont("Helvetica", 10)

    lang = cv.get("lang", "pt")
    L = {
        "Resumo": "Resumo" if lang=="pt" else "Summary",
        "Habilidades": "Habilidades" if lang=="pt" else "Skills",
        "Experiência": "Experiência" if lang=="pt" else "Experience",
        "Formação": "Formação" if lang=="pt" else "Education",
        "Certificações": "Certificações" if lang=="pt" else "Certifications",
        "Idiomas": "Idiomas" if lang=="pt" else "Languages",
        "Objetivo": "Objetivo" if lang=="pt" else "Objective",
    }

    if cv.get("summary"):
        section(L["Resumo"])
        y = _draw_paragraph(c, x, y, cv["summary"], max_width)
        y -= 4

    if cv.get("objective"):
        section(L["Objetivo"])
        y = _draw_paragraph(c, x, y, cv["objective"], max_width)
        y -= 4

    skills = cv.get("skills") or []
    if skills:
        section(L["Habilidades"])
        y = _draw_paragraph(c, x, y, ", ".join(skills), max_width)
        y -= 4

    exp = cv.get("experience") or []
    if exp:
        section(L["Experiência"])
        for line in exp:
            if line.startswith("•"):
                y = _draw_paragraph(c, x + 10, y, line, max_width - 10)
            else:
                c.setFont("Helvetica-Bold", 10)
                y = _draw_paragraph(c, x, y, line, max_width, 12, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
            y -= 1
        y -= 4

    edu = cv.get("education") or []
    if edu:
        section(L["Formação"])
        for line in edu:
            y = _draw_paragraph(c, x, y, line, max_width)
            y -= 1
        y -= 4

    certs = cv.get("certs") or []
    if certs:
        section(L["Certificações"])
        for line in certs:
            y = _draw_paragraph(c, x, y, line, max_width)
            y -= 1
        y -= 4

    langs = cv.get("languages") or []
    if langs:
        section(L["Idiomas"])
        for line in langs:
            y = _draw_paragraph(c, x, y, line, max_width)
            y -= 1

    c.showPage()
    c.save()
    return path