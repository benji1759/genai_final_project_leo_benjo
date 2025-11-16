"""
Compliance Report Generator

This module handles the generation of structured PDF compliance reports
from RAG-generated legal analysis.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import markdown
from langchain_openai import ChatOpenAI


class ComplianceReportGenerator:
    """
    Generates structured PDF compliance reports from legal analysis.
    
    The generator uses an LLM to structure the RAG output into a professional
    report format with executive summary, compliance scores (when applicable),
    detailed analysis, and actionable next steps.
    """
    
    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        output_dir: Optional[str] = None
    ):
        """
        Initialize the report generator.
        
        Args:
            llm_model: OpenAI chat model name for report structuring
            output_dir: Directory for saving PDF reports (defaults to current directory)
        """
        self.llm_model = llm_model
        self.output_dir = Path(output_dir or ".").resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM for report structuring
        self.llm = ChatOpenAI(model=llm_model, temperature=0.4)
        
        # PDF styles
        self.styles = self._initialize_styles()
    
    def _initialize_styles(self) -> dict:
        """
        Initialize ReportLab paragraph styles for PDF formatting.
        
        Returns:
            Dictionary containing style objects for title, section, and normal text
        """
        styles = getSampleStyleSheet()
        
        normal_style = ParagraphStyle(
            "Normal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        )
        
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=12,
            textColor="#1a1a1a",
        )
        
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor="#000000",
        )
        
        return {
            "normal": normal_style,
            "title": title_style,
            "section": section_style
        }
    
    def _build_report_prompt(self, question: str, rag_answer: str) -> str:
        """
        Construct the LLM prompt for structuring the compliance report.
        
        Args:
            question: Original user question
            rag_answer: RAG-generated legal analysis
        
        Returns:
            Formatted prompt string
        """
        return f"""
You are a legal compliance expert specialized in EU law, GDPR, and AI regulation.

Based on the following analysis, decide first if the user is describing a project, 
company, or internal policy. If yes, include a compliance score (e.g. "Compliance Score: 75/100") 
and give concrete recommendations. If the user is only asking an informational or general question, 
do not include any compliance score.

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
    
    def _clean_markdown(self, markdown_text: str) -> str:
        """
        Clean and normalize markdown text, removing duplicate compliance scores.
        
        Args:
            markdown_text: Raw markdown text from LLM
        
        Returns:
            Cleaned markdown text
        """
        # Remove duplicate compliance scores if present
        cleaned = re.sub(
            r"(Compliance Score\s*[:\-]?\s*\d{1,3}\s*/\s*100)[\s\S]*?"
            r"(Compliance Score\s*[:\-]?\s*\d{1,3}\s*/\s*100)?",
            r"\1",
            markdown_text,
            flags=re.IGNORECASE,
        )
        return cleaned
    
    def _parse_html_sections(self, html_text: str) -> list:
        """
        Parse HTML content into structured sections for PDF generation.
        
        Args:
            html_text: HTML content converted from markdown
        
        Returns:
            List of paragraph elements ready for PDF
        """
        paragraphs = []
        
        # Split by h2 headers
        sections = re.split(r"<h2.*?>(.*?)</h2>", html_text)
        
        for section_html in sections:
            if not section_html.strip():
                continue
            
            # Check if this is a section title (uppercase, short text)
            if (re.match(r'^[A-Z].*', section_html.strip()) and 
                len(section_html.strip()) < 100):
                # Add as section header
                paragraphs.append(Paragraph(
                    f"<b>{section_html.strip()}</b>",
                    self.styles["section"]
                ))
            else:
                # Clean and add as content
                clean_html = (
                    section_html
                    .replace("</li>", "<br/><br/>")
                    .replace("<ul>", "")
                    .replace("</ul>", "")
                    .replace("<p>", "")
                    .replace("</p>", "<br/><br/>")
                )
                paragraphs.append(Paragraph(clean_html, self.styles["normal"]))
                paragraphs.append(Spacer(1, 6))
        
        return paragraphs
    
    def _generate_filename(self, question: str) -> str:
        """
        Generate a safe filename for the PDF report.
        
        Args:
            question: User question (used for filename generation)
        
        Returns:
            Safe filename string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_question = re.sub(
            r"[^A-Za-z0-9._-]+", "_", question.strip()
        )[:40].strip("_")
        
        base_name = f"compliance_report_{timestamp}"
        if safe_question:
            base_name += f"_{safe_question}"
        
        return f"{base_name}.pdf"
    
    def generate(self, question: str, rag_answer: str) -> str:
        """
        Generate a complete PDF compliance report from RAG analysis.
        
        Args:
            question: Original user question
            rag_answer: RAG-generated legal analysis
        
        Returns:
            Absolute path to the generated PDF file
        """
        # Step 1: Generate structured report content via LLM
        prompt = self._build_report_prompt(question, rag_answer)
        response = self.llm.invoke(prompt)
        markdown_text = response.content.strip()
        
        # Step 2: Clean markdown
        markdown_text = self._clean_markdown(markdown_text)
        
        # Step 3: Convert markdown to HTML
        html_text = markdown.markdown(markdown_text)
        
        # Step 4: Generate filename
        filename = self._generate_filename(question)
        pdf_path = self.output_dir / filename
        
        # Step 5: Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=60,
            rightMargin=60,
            topMargin=60,
            bottomMargin=50,
        )
        
        # Step 6: Build document content
        story = []
        
        # Header
        story.append(Paragraph(
            "<b>Compliance Analysis Report</b>",
            self.styles["title"]
        ))
        story.append(Paragraph(
            f"<b>Date:</b> {datetime.now().strftime('%d %B %Y, %H:%M')}",
            self.styles["normal"]
        ))
        story.append(Paragraph(
            f"<b>Question:</b> {question}",
            self.styles["normal"]
        ))
        story.append(Spacer(1, 12))
        
        # Report content
        content_paragraphs = self._parse_html_sections(html_text)
        story.extend(content_paragraphs)
        
        # Footer
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "<i>Generated automatically by the Policy Checker (GenAI).</i>",
            self.styles["normal"]
        ))
        
        # Step 7: Build PDF
        doc.build(story)
        
        print(f"Compliance report saved as: {pdf_path}")
        return str(pdf_path)


# Backward compatibility function
def generate_full_compliance_report(
    question: str,
    rag_answer: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Legacy function for generating compliance reports.
    
    Args:
        question: User question
        rag_answer: RAG-generated answer
        output_dir: Optional output directory
    
    Returns:
        Path to generated PDF
    """
    generator = ComplianceReportGenerator(output_dir=output_dir)
    return generator.generate(question, rag_answer)