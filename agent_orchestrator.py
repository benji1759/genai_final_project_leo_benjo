"""
Agent Orchestrator

Coordinates multiple specialized agents in an LLM-Mesh pattern
to perform comprehensive policy compliance checking.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import uuid

from agents.base import BaseAgent, AgentState
from agents.document_agent import DocumentAgent
from agents.regulation_agent import RegulationAgent
from agents.comparison_agent import ComparisonAgent
from agents.citation_agent import CitationAgent
from agents.report_agent import ReportAgent


class AgentOrchestrator:
    """
    Orchestrates multi-agent compliance checking workflow.
    
    Implements LLM-Mesh pattern where specialized agents collaborate
    to analyze policy documents against EU regulations.
    """
    
    def __init__(
        self,
        chroma_dir: str = "chroma_eu_laws",
        embed_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o-mini",
        output_dir: str = ".",
        verbose: bool = False
    ):
        """
        Initialize the agent orchestrator.
        
        Args:
            chroma_dir: Directory containing ChromaDB regulation database
            embed_model: Embedding model name
            llm_model: LLM model name for agents
            output_dir: Directory for generated reports
            verbose: Enable verbose logging
        """
        self.chroma_dir = chroma_dir
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.output_dir = output_dir
        self.verbose = verbose
        
        # Initialize agents
        self.agents = {
            "document": DocumentAgent(
                llm_model=llm_model,
                verbose=verbose
            ),
            "regulation": RegulationAgent(
                chroma_dir=chroma_dir,
                embed_model=embed_model,
                llm_model=llm_model,
                verbose=verbose
            ),
            "comparison": ComparisonAgent(
                llm_model=llm_model,
                verbose=verbose
            ),
            "citation": CitationAgent(
                llm_model=llm_model,
                verbose=verbose
            ),
            "report": ReportAgent(
                output_dir=output_dir,
                llm_model=llm_model,
                verbose=verbose
            )
        }
        
        # Shared state
        self.state: Optional[AgentState] = None
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new agent session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
        
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.state = AgentState(
            session_id=session_id,
            current_task="initialized",
            context={},
            results={},
            messages=[]
        )
        
        # Set state for all agents
        for agent in self.agents.values():
            agent.set_state(self.state)
        
        return session_id
    
    def analyze_policy(
        self,
        file_path: str,
        regulation_types: Optional[List[str]] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete policy analysis workflow.
        
        Args:
            file_path: Path to policy document
            regulation_types: Optional list of regulation types to check (e.g., ["GDPR", "AI Act"])
            document_id: Optional document identifier
        
        Returns:
            Complete analysis results including report path
        """
        # Create session if not exists
        if self.state is None:
            self.create_session()
        
        self.state.current_task = "analyzing_policy"
        self.log("Starting policy analysis workflow")
        
        try:
            # Phase 1: Document Parsing
            self.log("Phase 1: Parsing document")
            doc_result = self.agents["document"].execute({
                "file_path": file_path,
                "document_id": document_id
            })
            
            parsed_doc = doc_result["parsed_document"]
            document_info = {
                "title": parsed_doc.title or parsed_doc.filename,
                "author": parsed_doc.author,
                "date": parsed_doc.date.isoformat() if parsed_doc.date else None,
                "filename": parsed_doc.filename,
                "document_id": doc_result["document_id"]
            }
            
            # Phase 2: Regulation Retrieval
            self.log("Phase 2: Retrieving relevant regulations")
            regulation_results = {}
            
            # Retrieve regulations for each chunk
            for chunk in doc_result["chunks"]:
                chunk_id = chunk["chunk_id"]
                chunk_content = chunk["content"]
                
                reg_result = self.agents["regulation"].execute({
                    "query": chunk_content,
                    "regulation_types": regulation_types
                })
                
                regulation_results[chunk_id] = reg_result["retrieved_regulations"]
            
            # Also retrieve for full document
            full_doc_query = parsed_doc.full_text[:2000]  # First 2000 chars as query
            full_reg_result = self.agents["regulation"].execute({
                "query": full_doc_query,
                "regulation_types": regulation_types
            })
            
            # Phase 3: Comparison
            self.log("Phase 3: Comparing policy against regulations")
            comparison_results_all = {}
            
            for chunk in doc_result["chunks"]:
                chunk_id = chunk["chunk_id"]
                regulations = regulation_results.get(chunk_id, [])
                
                if regulations:
                    comp_result = self.agents["comparison"].execute({
                        "policy_content": chunk["content"],
                        "regulations": regulations,
                        "policy_section": chunk.get("section", "General")
                    })
                    comparison_results_all[chunk_id] = comp_result
            
            # Aggregate comparison results
            aggregated_comparison = self._aggregate_comparison_results(comparison_results_all)
            
            # Phase 4: Citation Extraction
            self.log("Phase 4: Extracting citations")
            all_comparison_text = "\n".join([
                result.get("raw_analysis", "")
                for result in comparison_results_all.values()
            ])
            
            citation_result = self.agents["citation"].extract_citations_from_comparison(
                {"raw_analysis": all_comparison_text}
            )
            
            # Phase 5: Report Generation
            self.log("Phase 5: Generating compliance report")
            discrepancies = aggregated_comparison.get("discrepancies", [])
            
            report_result = self.agents["report"].execute({
                "document_info": document_info,
                "comparison_results": aggregated_comparison,
                "citations": citation_result,
                "discrepancies": discrepancies
            })
            
            # Prepare final output
            output = {
                "session_id": self.state.session_id,
                "document_info": document_info,
                "parsed_document": {
                    "num_chunks": len(doc_result["chunks"]),
                    "total_length": len(parsed_doc.full_text)
                },
                "regulation_retrieval": {
                    "regulation_types": full_reg_result["regulation_types"],
                    "num_chunks_processed": len(regulation_results)
                },
                "comparison_results": aggregated_comparison,
                "citations": citation_result,
                "report": {
                    "report_path": report_result["report_path"],
                    "report_summary": report_result["report_summary"],
                    "compliance_score": report_result["compliance_score"]
                },
                "workflow_summary": {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Store final results in state
            self.state.results["final_analysis"] = output
            self.state.current_task = "completed"
            
            self.log(f"Analysis complete. Report: {report_result['report_path']}")
            
            return output
        
        except Exception as e:
            self.state.current_task = "error"
            error_msg = f"Error in policy analysis workflow: {str(e)}"
            self.log(error_msg, level="ERROR")
            raise RuntimeError(error_msg) from e
    
    def _aggregate_comparison_results(
        self,
        comparison_results_all: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate comparison results from multiple chunks."""
        if not comparison_results_all:
            return {
                "compliance_score": 0,
                "discrepancies": [],
                "compliant_elements": [],
                "missing_requirements": []
            }
        
        all_compliant = []
        all_discrepancies = []
        all_missing = []
        scores = []
        
        for chunk_id, result in comparison_results_all.items():
            comp_results = result.get("comparison_results", {})
            
            all_compliant.extend(comp_results.get("compliant_elements", []))
            all_discrepancies.extend(result.get("discrepancies", []))
            all_missing.extend(comp_results.get("missing_requirements", []))
            
            score = result.get("compliance_score", 0)
            if score is not None:
                scores.append(score)
        
        # Calculate average compliance score
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Deduplicate findings
        unique_compliant = list(set(all_compliant))
        unique_discrepancies = self._deduplicate_discrepancies(all_discrepancies)
        unique_missing = list(set(all_missing))
        
        return {
            "compliance_score": int(avg_score),
            "discrepancies": unique_discrepancies,
            "compliant_elements": unique_compliant,
            "missing_requirements": unique_missing,
            "num_chunks_compared": len(comparison_results_all)
        }
    
    def _deduplicate_discrepancies(
        self,
        discrepancies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate discrepancies."""
        seen = set()
        unique = []
        
        for disc in discrepancies:
            # Create a key from description
            if isinstance(disc, dict):
                key = disc.get("description", str(disc))
            else:
                key = str(disc)
            
            if key not in seen:
                seen.add(key)
                unique.append(disc)
        
        return unique
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[Orchestrator] [{level}]: {message}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def get_state(self) -> Optional[AgentState]:
        """Get the current shared state."""
        return self.state
