# report_generator.py
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import markdown
import re
from langchain_openai import ChatOpenAI

def generate_full_compliance_report(question: str, rag_answer: str):
    """
    🧠 Full-Intelligence Compliance Report
    → Résumé, score, analyse, next steps
    → PDF format with bold titles, spacing & readability
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

    # 🧩 Prompt optimisé avec détection du score
    prompt = f"""
You are a legal compliance expert specialized in EU law, GDPR, and AI regulation.

Based on the following analysis, decide first if the user is **describing a project, company, or internal policy**.
If yes, include a compliance score (e.g. "Compliance Score: 75/100") and give concrete recommendations.
If the user is only asking an informational or general question, **do not include any compliance score**.

Structure your report as follows:
- **Executive Summary**
- *(Optional)* **Compliance Score** (only if relevant)
- **Detailed Analysis**
- **Specific, Actionable Next Steps**

Use clear Markdown formatting:
- Use '## ' for section titles
- Use bold (**...**) for key terms
- Add blank lines between sections and bullet points
- Keep the report concise (max 2 pages)

Analysis:
\"\"\"{rag_answer}\"\"\"

Question: "{question}"
"""

    # 💬 GPT-4o output
    response = llm.invoke(prompt)
    markdown_text = response.content.strip()

    # 🧹 Nettoyage du double score éventuel sans supprimer le "/100"
    markdown_text = re.sub(
        r"(Compliance Score\s*[:\-]?\s*\d{1,3}\s*/\s*100)[\s\S]*?(Compliance Score\s*[:\-]?\s*\d{1,3}\s*/\s*100)?",
        r"\1",
        markdown_text,
        flags=re.IGNORECASE,
    )

    # 🔁 Conversion Markdown → HTML
    html_text = markdown.markdown(markdown_text)

    # 📄 Création PDF
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"compliance_report_{timestamp}.pdf"

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        spaceAfter=8,
    )
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=16,
        leading=20,
        spaceAfter=12,
        textColor="#1a1a1a",
    )
    section = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor="#000000",
    )

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=60,
        rightMargin=60,
        topMargin=60,
        bottomMargin=50,
    )

    story = []

    # En-tête
    story.append(Paragraph("<b>Compliance Analysis Report</b>", title))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y, %H:%M')}", normal))
    story.append(Paragraph(f"<b>Question:</b> {question}", normal))
    story.append(Spacer(1, 12))

    # ✅ Ajout du contenu converti Markdown → HTML
    for section_html in re.split(r"<h2.*?>(.*?)</h2>", html_text):
        if not section_html.strip():
            continue
        # Si c’est un titre de section
        if re.match(r'^[A-Z].*', section_html.strip()) and len(section_html.strip()) < 100:
            story.append(Paragraph(f"<b>{section_html.strip()}</b>", section))
        else:
            # Nettoyage des listes et ajout de sauts de ligne
            clean_html = (
                section_html
                .replace("</li>", "<br/><br/>")
                .replace("<ul>", "")
                .replace("</ul>", "")
                .replace("<p>", "")
                .replace("</p>", "<br/><br/>")
            )
            story.append(Paragraph(clean_html, normal))
            story.append(Spacer(1, 6))

    # Signature
    story.append(Spacer(1, 12))
    story.append(Paragraph("<i>Generated automatically by the Policy Checker (GenAI).</i>", normal))

    doc.build(story)
    print(f"✅ Formatted compliance report saved as {filename}")
    return filename