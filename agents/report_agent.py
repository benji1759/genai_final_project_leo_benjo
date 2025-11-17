"""
Report Agent

Responsible for generating structured compliance reports
from comparison results and citations.
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
from report_generator import ComplianceReportGenerator


class ReportAgent(BaseAgent):
    """
    Agent specialized in generating comprehensive compliance reports.
    
    This agent synthesizes comparison results, citations, and discrepancies
    into structured, professional compliance reports.
    """
    
    def __init__(self, output_dir: str = ".", **kwargs):
        """
        Initialize the report agent.
        
        Args:
            output_dir: Directory for saving reports
            **kwargs: Additional arguments for BaseAgent
        """
        super().__init__(
            agent_id="report_agent",
            agent_name="Report Generation Agent",
            temperature=0.4,  # Slightly higher for more natural report language
            **kwargs
        )
        
        self.report_generator = ComplianceReportGenerator(
            llm_model=self.llm_model,
            output_dir=output_dir
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive compliance report.
        
        Expected input_data:
            - document_info: Document metadata (title, author, etc.)
            - comparison_results: Results from comparison agent
            - citations: Citations from citation agent
            - discrepancies: List of discrepancies with severity
        
        Returns:
            Dictionary containing:
                - report_path: Path to generated PDF report
                - report_summary: Text summary of the report
                - compliance_score: Overall compliance score
        """
        # Validate input
        self.validate_input(input_data, ["document_info", "comparison_results"])
        
        document_info = input_data["document_info"]
        comparison_results = input_data["comparison_results"]
        citations = input_data.get("citations", {})
        discrepancies = input_data.get("discrepancies", [])
        
        self.log("Generating compliance report")
        
        try:
            # Build comprehensive report content
            report_content = self._build_report_content(
                document_info,
                comparison_results,
                citations,
                discrepancies
            )
            
            # Generate structured report using LLM
            structured_report = self._generate_structured_report(report_content)
            
            # Generate PDF report
            document_title = document_info.get("title", "Policy Document")
            report_path = self.report_generator.generate(
                question=f"Compliance Analysis: {document_title}",
                rag_answer=structured_report
            )
            
            # Extract summary
            report_summary = self._extract_summary(structured_report)
            compliance_score = comparison_results.get("compliance_score", 0)
            
            output = {
                "report_path": report_path,
                "report_summary": report_summary,
                "compliance_score": compliance_score,
                "num_discrepancies": len(discrepancies),
                "structured_report": structured_report
            }
            
            # Store results in state
            if self.state:
                self.store_result("report", output)
            
            self.log(f"Report generated: {report_path}")
            
            return output
        
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            self.log(error_msg, level="ERROR")
            raise RuntimeError(error_msg) from e
    
    def _build_report_content(
        self,
        document_info: Dict[str, Any],
        comparison_results: Dict[str, Any],
        citations: Dict[str, Any],
        discrepancies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build comprehensive report content structure."""
        return {
            "document": {
                "title": document_info.get("title", "Unknown"),
                "author": document_info.get("author", "Unknown"),
                "date": document_info.get("date", None),
                "filename": document_info.get("filename", "Unknown")
            },
            "comparison": {
                "compliance_score": comparison_results.get("compliance_score", 0),
                "compliant_elements": comparison_results.get("comparison_results", {}).get("compliant_elements", []),
                "discrepancies": comparison_results.get("discrepancies", []),
                "missing_requirements": comparison_results.get("comparison_results", {}).get("missing_requirements", [])
            },
            "citations": citations,
            "discrepancies_detailed": discrepancies
        }
    
    def _generate_structured_report(
        self,
        report_content: Dict[str, Any]
    ) -> str:
        """Generate structured report text using LLM."""
        doc = report_content["document"]
        comp = report_content["comparison"]
        citations = report_content.get("citations", {})
        discrepancies = report_content.get("discrepancies_detailed", [])
        
        # Build comprehensive prompt
        prompt = f"""
You are a compliance reporting expert. Generate a comprehensive compliance report
for a policy document compared against EU regulations (GDPR, AI Act, NIS2, etc.).

Document Information:
- Title: {doc['title']}
- Author: {doc.get('author', 'Unknown')}
- Date: {doc.get('date', 'Unknown')}

Compliance Score: {comp['compliance_score']}/100

Compliant Elements:
{self._format_list(comp['compliant_elements'])}

Discrepancies:
{self._format_list([d.get('description', d) if isinstance(d, dict) else d for d in comp['discrepancies']])}

Missing Requirements:
{self._format_list(comp['missing_requirements'])}

Citations Found:
{self._format_citations(citations)}

Generate a structured report with the following sections:

## Executive Summary
Provide a high-level overview of compliance status (2-3 paragraphs).

## Compliance Assessment
Overall compliance score: {comp['compliance_score']}/100

Break down the compliance status with clear explanations.

## Detailed Findings

### Compliant Elements
List and explain elements that comply with regulations, citing specific articles.

### Identified Discrepancies
Detail each discrepancy with:
- Description
- Severity level
- Relevant regulation articles
- Impact assessment

### Missing Requirements
List requirements from regulations that are not addressed in the policy.

## Article Citations
Provide a comprehensive list of all relevant regulation articles cited, organized by regulation type (GDPR, AI Act, etc.).

## Recommendations
Provide specific, actionable recommendations for addressing identified issues.

Use clear Markdown formatting with section headers (##) and bullet points.
"""
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def _format_list(self, items: List[Any]) -> str:
        """Format a list of items as text."""
        if not items:
            return "- None"
        return "\n".join(f"- {item}" if isinstance(item, str) else f"- {str(item)}" for item in items)
    
    def _format_citations(self, citations: Dict[str, Any]) -> str:
        """Format citations for the prompt."""
        if not citations:
            return "No citations found."
        
        formatted = []
        
        citations_by_reg = citations.get("citations_by_regulation", {})
        for reg_type, cit_list in citations_by_reg.items():
            formatted.append(f"\n{reg_type}:")
            for cit in cit_list:
                ref = cit.get("reference", "Unknown")
                formatted.append(f"  - Article {ref}")
        
        return "\n".join(formatted) if formatted else "No citations found."
    
    def _extract_summary(self, report_text: str) -> str:
        """Extract executive summary from report."""
        lines = report_text.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if "Executive Summary" in line:
                in_summary = True
                continue
            
            if in_summary:
                if line.startswith('##'):
                    break
                if line.strip():
                    summary_lines.append(line.strip())
        
        return "\n".join(summary_lines) if summary_lines else report_text[:500]
    
    def generate_quick_summary(
        self,
        comparison_results: Dict[str, Any],
        max_length: int = 200
    ) -> str:
        """
        Generate a quick text summary of compliance status.
        
        Args:
            comparison_results: Results from comparison agent
            max_length: Maximum length of summary
        
        Returns:
            Brief summary string
        """
        score = comparison_results.get("compliance_score", 0)
        num_discrepancies = len(comparison_results.get("discrepancies", []))
        
        summary = (
            f"Compliance Score: {score}/100. "
            f"Found {num_discrepancies} discrepancies. "
        )
        
        if score >= 80:
            summary += "Policy is largely compliant with minor issues to address."
        elif score >= 60:
            summary += "Policy has moderate compliance issues requiring attention."
        else:
            summary += "Policy has significant compliance gaps requiring major revisions."
        
        return summary[:max_length]
