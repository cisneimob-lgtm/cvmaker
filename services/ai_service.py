import os

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.3-chat-latest")


def _has_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def improve_text_optional(kind: str, raw: str, context: str = "") -> str:
    raw = (raw or "").strip()
    if not raw:
        return raw
    if not _has_key():
        return raw

    try:
        from openai import OpenAI
    except Exception:
        return raw

    prompt = _build_prompt(kind=kind, raw=raw, context=context)

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.responses.create(model=DEFAULT_MODEL, input=prompt)
        text = (resp.output_text or "").strip()
        return text if text else raw
    except Exception:
        return raw


def translate_cv_optional(cv: dict) -> dict:
    """
    Tradução para inglês (opcional).
    Se não tiver API key, retorna cv com _translated_ok=False.
    """
    if not _has_key():
        out = dict(cv)
        out["_translated_ok"] = False
        return out

    try:
        from openai import OpenAI
    except Exception:
        out = dict(cv)
        out["_translated_ok"] = False
        return out

    # campos para traduzir
    payload = {
        "title": cv.get("title", ""),
        "summary": cv.get("summary", ""),
        "objective": cv.get("objective", ""),
        "skills": cv.get("skills", []),
        "experience": cv.get("experience", []),
        "education": cv.get("education", []),
        "certs": cv.get("certs", []),
        "languages": cv.get("languages", []),
    }

    prompt = f"""
You are an expert resume writer.
Translate the following resume fields from Portuguese (Brazil) to English.
Rules:
- Do NOT invent facts, numbers, companies, dates, certifications, or roles.
- Keep it professional, ATS-friendly, concise.
- Keep bullet lines starting with "•".
- Output MUST be valid JSON with the same keys.

INPUT JSON:
{payload}
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.responses.create(
            model=DEFAULT_MODEL,
            input=prompt,
        )
        text = (resp.output_text or "").strip()

        import json
        translated = json.loads(text)

        out = dict(cv)
        for k in payload.keys():
            if k in translated:
                out[k] = translated[k]
        out["_translated_ok"] = True
        return out

    except Exception:
        out = dict(cv)
        out["_translated_ok"] = False
        return out


def _build_prompt(kind: str, raw: str, context: str) -> str:
    base_rules = """
Você é um especialista em RH e ATS.
Reescreva o texto em PT-BR, profissional, claro e objetivo.
Regras:
- Não invente fatos, números, empresas, datas ou certificações.
- Não use emojis.
- Evite exageros.
- Preserve o sentido original.
"""

    if kind == "summary":
        extra = "Tarefa: Resumo profissional (2 a 4 linhas)."
    elif kind == "objective":
        extra = "Tarefa: Objetivo (1 linha) com cargo/área."
    else:
        extra = "Tarefa: Reescrever curto e direto."

    return f"""{base_rules}

Contexto (se houver): {context}

Texto original:
{raw}

{extra}

Responda SOMENTE com o texto final, sem explicações.
"""