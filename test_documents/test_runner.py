"""
Test Runner for Policy Compliance Checker

Quick script to test the compliance checker with sample documents.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_orchestrator import AgentOrchestrator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_document(document_path: str, regulation_types: list = None):
    """
    Test a document against regulations.
    
    Args:
        document_path: Path to the policy document
        regulation_types: List of regulations to check (default: all)
    """
    if regulation_types is None:
        regulation_types = ["GDPR", "AI Act", "NIS2"]
    
    print(f"\n{'='*60}")
    print(f"Testing: {Path(document_path).name}")
    print(f"Regulations: {', '.join(regulation_types)}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize orchestrator
        print("Initializing orchestrator...")
        orchestrator = AgentOrchestrator(verbose=True)
        
        # Run analysis
        print("Running compliance analysis...")
        results = orchestrator.analyze_policy(
            file_path=document_path,
            regulation_types=regulation_types
        )
        
        # Display results
        report = results.get("report", {})
        comparison = results.get("comparison_results", {})
        citations = results.get("citations", {})
        
        print(f"\n{'='*60}")
        print("ANALYSIS RESULTS")
        print(f"{'='*60}\n")
        
        print(f"Compliance Score: {report.get('compliance_score', 0)}/100")
        print(f"\nDiscrepancies Found: {len(comparison.get('discrepancies', []))}")
        print(f"Citations Found: {citations.get('num_citations', 0)}")
        print(f"\nReport Path: {report.get('report_path', 'N/A')}")
        
        # Show top discrepancies
        discrepancies = comparison.get("discrepancies", [])[:5]
        if discrepancies:
            print(f"\nTop Discrepancies:")
            for i, disc in enumerate(discrepancies, 1):
                if isinstance(disc, dict):
                    desc = disc.get("description", str(disc))[:100]
                    severity = disc.get("severity", "unknown")
                    print(f"  {i}. [{severity}] {desc}...")
                else:
                    print(f"  {i}. {str(disc)[:100]}...")
        
        # Show citations by regulation
        citations_by_reg = citations.get("citations_by_regulation", {})
        if citations_by_reg:
            print(f"\nCitations by Regulation:")
            for reg_type, cit_list in citations_by_reg.items():
                print(f"  {reg_type}: {len(cit_list)} citations")
                for cit in cit_list[:3]:  # Show first 3
                    ref = cit.get("reference", "Unknown")
                    print(f"    - Article {ref}")
        
        print(f"\n{'='*60}\n")
        
        return results
    
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run tests on all sample documents."""
    test_dir = Path(__file__).parent
    
    documents = {
        "sample_privacy_policy.txt": ["GDPR"],
        "sample_ai_usage_policy.txt": ["GDPR", "AI Act"],
        "sample_cybersecurity_policy.txt": ["NIS2", "GDPR"],
        "sample_comprehensive_policy.txt": ["GDPR", "AI Act", "NIS2"]
    }
    
    print("Policy Compliance Checker - Test Suite")
    print("=" * 60)
    
    results_summary = []
    
    for doc_name, regulations in documents.items():
        doc_path = test_dir / doc_name
        
        if not doc_path.exists():
            print(f"\nWarning: {doc_name} not found, skipping...")
            continue
        
        results = test_document(str(doc_path), regulations)
        
        if results:
            report = results.get("report", {})
            score = report.get("compliance_score", 0)
            results_summary.append({
                "document": doc_name,
                "score": score,
                "regulations": regulations
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}\n")
    
    for result in results_summary:
        print(f"{result['document']}:")
        print(f"  Compliance Score: {result['score']}/100")
        print(f"  Regulations Checked: {', '.join(result['regulations'])}")
        print()
    
    print("Testing complete!")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment")
        print("Please set it in .env file or export the variable")
        sys.exit(1)
    
    main()
