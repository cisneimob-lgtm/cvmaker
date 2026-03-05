import os
import tempfile
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from services.pdf_service import build_pdf
from services.docx_service import build_docx
from services.ai_service import improve_text_optional, translate_cv_optional
from services.score_service import score_cv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-change-me")

ALLOWED_EXT = {"png", "jpg", "jpeg"}


def sanitize_lines(text):
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_form(form):
    data = {
        "name": (form.get("name", "") or "").strip(),
        "title": (form.get("title", "") or "").strip(),
        "email": (form.get("email", "") or "").strip(),
        "phone": (form.get("phone", "") or "").strip(),
        "city": (form.get("city", "") or "").strip(),
        "linkedin": (form.get("linkedin", "") or "").strip(),
        "github": (form.get("github", "") or "").strip(),
        "portfolio": (form.get("portfolio", "") or "").strip(),
        "summary": (form.get("summary", "") or "").strip(),
        "objective": (form.get("objective", "") or "").strip(),
        "skills": [s.strip() for s in (form.get("skills", "") or "").split(",") if s.strip()],
        "experience": sanitize_lines(form.get("experience", "")),
        "education": sanitize_lines(form.get("education", "")),
        "certs": sanitize_lines(form.get("certs", "")),
        "languages": sanitize_lines(form.get("languages", "")),
        "template": (form.get("template", "ats") or "ats").strip(),
        "lang": (form.get("lang", "pt") or "pt").strip(),  # pt | en
    }

    if not data["name"]:
        raise ValueError("Nome é obrigatório.")
    if data["template"] not in {"ats", "modern", "minimal"}:
        data["template"] = "ats"
    if data["lang"] not in {"pt", "en"}:
        data["lang"] = "pt"

    return data


def save_photo(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        return None

    fd, path = tempfile.mkstemp(suffix=f".{ext}")
    os.close(fd)
    file_storage.save(path)
    return path


@app.get("/landing")
def landing():
    return render_template("landing.html")


@app.get("/")
def index():
    demo = {
        "name": "Gabriel Santos",
        "title": "Desenvolvedor Python",
        "email": "gabriel@email.com",
        "phone": "(19) 99999-9999",
        "city": "Campinas/SP",
        "linkedin": "linkedin.com/in/seu-perfil",
        "github": "github.com/seuuser",
        "portfolio": "",
        "summary": "Desenvolvedor focado em automação e aplicações web em Python. Entrego soluções simples, rápidas e escaláveis para pequenos negócios.",
        "objective": "Atuar como Desenvolvedor Python / Automação / Web.",
        "skills": "Python, Flask, SQLite, APIs, Git, HTML, CSS",
        "experience": "Freelancer — Automação e sites\n• Criei apps web em Flask para geração de PDFs\n• Integrei formulários com banco SQLite e relatórios\n\nAssistente Administrativo\n• Atendimento ao cliente e organização de demandas\n• Atualização de planilhas e relatórios",
        "education": "Curso Superior (exemplo)\n• Instituição X — 2020–2023",
        "certs": "Python básico (exemplo)\nGit e GitHub (exemplo)",
        "languages": "Português — Nativo\nInglês — Intermediário",
        "template": "ats",
        "lang": "pt",
    }
    return render_template("index.html", demo=demo)


@app.post("/preview")
def preview():
    try:
        data = parse_form(request.form)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("index"))

    # Foto (opcional)
    photo_path = save_photo(request.files.get("photo"))
    data["photo_path"] = photo_path

    # IA: melhorar resumo/objetivo (opcional)
    if request.form.get("use_ai") == "on":
        data["summary"] = improve_text_optional(
            kind="summary",
            raw=data.get("summary", ""),
            context=f"Cargo: {data.get('title','')}. Skills: {', '.join(data.get('skills', []))}."
        )
        data["objective"] = improve_text_optional(
            kind="objective",
            raw=data.get("objective", ""),
            context=f"Cargo desejado: {data.get('title','')}."
        )

    # IA: versão em inglês (opcional)
    if request.form.get("make_english") == "on":
        translated = translate_cv_optional(data)
        # se a tradução falhar (sem key), mantém PT e avisa
        if translated.get("_translated_ok"):
            data = translated
            data["lang"] = "en"
        else:
            flash("IA não configurada (sem OPENAI_API_KEY). Mantive em PT-BR.", "error")

    # Score ATS
    s = score_cv(data)
    data["_score"] = s["score"]
    data["_tips"] = s["tips"]

    session["cv_data"] = data
    return render_template("preview.html", cv=data)


@app.get("/download/pdf")
def download_pdf():
    data = session.get("cv_data")
    if not data:
        return redirect(url_for("index"))

    out_path = build_pdf(data)
    filename = f"CV_{data['name'].replace(' ', '_')}_{data.get('template','ats')}_{data.get('lang','pt')}.pdf"
    return send_file(out_path, as_attachment=True, download_name=filename)


@app.get("/download/docx")
def download_docx():
    data = session.get("cv_data")
    if not data:
        return redirect(url_for("index"))

    out_path = build_docx(data)
    filename = f"CV_{data['name'].replace(' ', '_')}_{data.get('template','ats')}_{data.get('lang','pt')}.docx"
    return send_file(out_path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(debug=True)