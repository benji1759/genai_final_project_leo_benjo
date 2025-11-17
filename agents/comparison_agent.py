"""
Comparison Agent

Responsible for comparing policy documents against EU regulations
to identify discrepancies and compliance issues.
"""

from typing import Dict, Any, List
from agents.base import BaseAgent


class ComparisonAgent(BaseAgent):
    """
    Agent specialized in comparing policies against regulations.
    
    This agent performs semantic comparison between policy content
    and regulation requirements to identify discrepancies.
    """
    
    def __init__(self, **kwargs):
        """Initialize the comparison agent."""
        super().__init__(
            agent_id="comparison_agent",
            agent_name="Compliance Comparison Agent",
            temperature=0.2,  # Lower temperature for more consistent comparison
            **kwargs
        )
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare policy content against regulations.
        
        Expected input_data:
            - policy_content: Policy document content or chunk
            - regulations: List of relevant regulation chunks
            - policy_section: Optional section name in policy
        
        Returns:
            Dictionary containing:
                - comparison_results: List of comparison findings
                - compliance_score: Overall compliance score (0-100)
                - discrepancies: List of identified discrepancies
        """
        # Validate input
        self.validate_input(input_data, ["policy_content", "regulations"])
        
        policy_content = input_data["policy_content"]
        regulations = input_data["regulations"]
        policy_section = input_data.get("policy_section", "General")
        
        self.log(f"Comparing policy section '{policy_section}' against regulations")
        
        try:
            # Prepare regulation context
            regulation_context = self._prepare_regulation_context(regulations)
            
            # Perform comparison using LLM
            comparison_prompt = self._build_comparison_prompt(
                policy_content,
                regulation_context,
                policy_section
            )
            
            response = self.llm.invoke(comparison_prompt)
            comparison_analysis = response.content.strip()
            
            # Extract structured comparison results
            results = self._extract_comparison_results(comparison_analysis)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(results)
            
            # Identify discrepancies
            discrepancies = self._identify_discrepancies(results)
            
            output = {
                "comparison_results": results,
                "compliance_score": compliance_score,
                "discrepancies": discrepancies,
                "policy_section": policy_section,
                "raw_analysis": comparison_analysis
            }
            
            # Store results in state
            if self.state:
                self.store_result("comparison_results", output)
                self.update_state_context("compliance_score", compliance_score)
            
            self.log(f"Comparison complete. Compliance score: {compliance_score}/100")
            
            return output
        
        except Exception as e:
            error_msg = f"Error performing comparison: {str(e)}"
            self.log(error_msg, level="ERROR")
            raise RuntimeError(error_msg) from e
    
    def _prepare_regulation_context(self, regulations: List[Dict[str, Any]]) -> str:
        """Prepare regulation context for comparison."""
        context_parts = []
        
        for i, reg in enumerate(regulations, 1):
            content = reg.get("content", "")
            reg_type = reg.get("regulation_type", "Unknown")
            source = reg.get("source", "Unknown")
            
            context_parts.append(
                f"[Regulation {i}] {reg_type}\n"
                f"Source: {source}\n"
                f"Content: {content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _build_comparison_prompt(
        self,
        policy_content: str,
        regulation_context: str,
        policy_section: str
    ) -> str:
        """Build the LLM prompt for comparison."""
        return f"""
You are a compliance analyst specializing in EU regulations (GDPR, AI Act, NIS2, etc.).

Compare the following policy content against the relevant EU regulations and identify:
1. Compliance points (where the policy aligns with regulations)
2. Discrepancies (where the policy conflicts with or lacks required elements)
3. Missing requirements (regulations that should be addressed but aren't)
4. Specific article citations for each finding

Policy Section: {policy_section}

Policy Content:
\"\"\"{policy_content}\"\"\"

Relevant EU Regulations:
\"\"\"{regulation_context}\"\"\"

Provide your analysis in the following structured format:

## Compliance Analysis

### Compliant Elements
- [List elements that comply, cite articles]

### Discrepancies
- [List discrepancies, cite specific articles that are violated or missing]

### Missing Requirements
- [List requirements from regulations that should be addressed, cite articles]

### Compliance Score
Provide a score from 0-100 indicating overall compliance level.

Format: Compliance Score: XX/100
"""
    
    def _extract_comparison_results(self, analysis_text: str) -> Dict[str, Any]:
        """Extract structured results from LLM analysis."""
        results = {
            "compliant_elements": [],
            "discrepancies": [],
            "missing_requirements": [],
            "compliance_score": None
        }
        
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Detect sections
            if "Compliant Elements" in line or "compliant" in line.lower():
                current_section = "compliant"
            elif "Discrepancies" in line or "discrepancy" in line.lower():
                current_section = "discrepancies"
            elif "Missing Requirements" in line or "missing" in line.lower():
                current_section = "missing"
            elif line.startswith('-') or line.startswith('*'):
                # Extract bullet point
                content = line.lstrip('-* ').strip()
                if current_section and content:
                    if current_section == "compliant":
                        results["compliant_elements"].append(content)
                    elif current_section == "discrepancies":
                        results["discrepancies"].append(content)
                    elif current_section == "missing":
                        results["missing_requirements"].append(content)
            elif "Compliance Score" in line:
                # Extract score
                import re
                score_match = re.search(r'(\d+)\s*/?\s*100', line)
                if score_match:
                    results["compliance_score"] = int(score_match.group(1))
        
        return results
    
    def _calculate_compliance_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall compliance score."""
        # If score was extracted, use it
        if results["compliance_score"] is not None:
            return results["compliance_score"]
        
        # Otherwise, estimate from findings
        num_discrepancies = len(results["discrepancies"])
        num_missing = len(results["missing_requirements"])
        num_compliant = len(results["compliant_elements"])
        
        total_issues = num_discrepancies + num_missing
        total_points = num_compliant + total_issues
        
        if total_points == 0:
            return 50  # Neutral score if no findings
        
        # Simple scoring: compliant elements increase score, issues decrease it
        base_score = 100
        issue_penalty = min(total_issues * 10, 70)  # Max 70 point penalty
        
        score = max(0, base_score - issue_penalty)
        return score
    
    def _identify_discrepancies(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Structure discrepancies with metadata."""
        discrepancies = []
        
        for disc in results["discrepancies"]:
            discrepancies.append({
                "type": "discrepancy",
                "description": disc,
                "severity": "medium"  # Will be refined by severity assessor
            })
        
        for missing in results["missing_requirements"]:
            discrepancies.append({
                "type": "missing_requirement",
                "description": missing,
                "severity": "high"
            })
        
        return discrepancies
    
    def compare_document_chunks(
        self,
        policy_chunks: List[Dict[str, Any]],
        regulation_map: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Compare multiple policy chunks against their corresponding regulations.
        
        Args:
            policy_chunks: List of policy chunk dictionaries
            regulation_map: Dictionary mapping chunk IDs to regulation lists
        
        Returns:
            Dictionary containing comparison results for all chunks
        """
        all_results = {}
        
        for chunk in policy_chunks:
            chunk_id = chunk.get("chunk_id", 0)
            regulations = regulation_map.get(chunk_id, [])
            
            if regulations:
                result = self.execute({
                    "policy_content": chunk.get("content", ""),
                    "regulations": regulations,
                    "policy_section": chunk.get("section", "General")
                })
                all_results[chunk_id] = result
        
        return {
            "chunk_comparisons": all_results,
            "num_chunks_compared": len(all_results)
        }
