import re

def score_cv(cv: dict) -> dict:
    score = 50
    tips = []

    name = (cv.get("name") or "").strip()
    title = (cv.get("title") or "").strip()
    email = (cv.get("email") or "").strip()
    phone = (cv.get("phone") or "").strip()
    summary = (cv.get("summary") or "").strip()
    skills = cv.get("skills") or []
    exp = cv.get("experience") or []
    edu = cv.get("education") or []

    # básicos
    if name:
        score += 5
    if title:
        score += 6
    else:
        tips.append("Adicione um título/cargo (ex: Desenvolvedor Python).")

    if email and re.search(r".+@.+\..+", email):
        score += 6
    else:
        tips.append("Coloque um e-mail válido.")

    if phone:
        score += 4
    else:
        tips.append("Coloque um telefone/WhatsApp para contato.")

    # resumo
    if 60 <= len(summary) <= 400:
        score += 10
    elif summary:
        score += 4
        tips.append("Seu resumo está curto/longo demais. Tente 2–4 linhas objetivas.")
    else:
        tips.append("Inclua um resumo profissional (2–4 linhas).")

    # skills
    if len(skills) >= 6:
        score += 10
    elif len(skills) >= 3:
        score += 6
        tips.append("Adicione mais habilidades relevantes (ideal: 6–12).")
    else:
        tips.append("Habilidades está fraco. Coloque pelo menos 6 itens.")

    # experiência
    bullets = [x for x in exp if str(x).strip().startswith("•")]
    if len(exp) >= 3 and len(bullets) >= 2:
        score += 12
    elif exp:
        score += 6
        tips.append("Em experiência, use bullets (•) com verbos de ação.")
    else:
        tips.append("Adicione experiência (mesmo freelas/projetos).")

    # formação
    if edu:
        score += 6
    else:
        tips.append("Inclua sua formação (curso, instituição, ano).")

    # links
    if cv.get("linkedin") or cv.get("github") or cv.get("portfolio"):
        score += 3
    else:
        tips.append("Se possível, adicione LinkedIn/GitHub/Portfólio.")

    # template ATS: foto não é prioridade
    if cv.get("template") == "ats" and cv.get("photo_path"):
        tips.append("Dica ATS: para RH/triagem automática, muitas vezes é melhor sem foto.")

    score = max(0, min(100, score))
    tips = tips[:6]
    return {"score": score, "tips": tips}