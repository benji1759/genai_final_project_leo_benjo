"""
Streamlit Frontend Application

Interactive interface for policy compliance checking with document upload,
comparison visualization, and report generation.
"""

import os
import streamlit as st
from pathlib import Path
import tempfile
from typing import Optional
from dotenv import load_dotenv

from agent_orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EU Policy Compliance Checker",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None


def initialize_orchestrator():
    """Initialize the agent orchestrator."""
    if st.session_state.orchestrator is None:
        with st.spinner("Initializing compliance checker..."):
            try:
                st.session_state.orchestrator = AgentOrchestrator(
                    chroma_dir=os.getenv("CHROMA_DIR", "chroma_eu_laws"),
                    verbose=True
                )
            except Exception as e:
                st.error(f"Error initializing orchestrator: {e}")
                st.stop()


def main():
    """Main Streamlit application."""
    st.title("EU Policy Compliance Checker")
    st.markdown("""
    Analyze internal policy documents against EU regulations (GDPR, AI Act, NIS2, etc.)
    and identify compliance discrepancies with cited articles.
    """)
    
    # Initialize orchestrator
    initialize_orchestrator()
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Regulation selection
        st.subheader("Regulations to Check")
        check_gdpr = st.checkbox("GDPR", value=True)
        check_ai_act = st.checkbox("AI Act", value=True)
        check_nis2 = st.checkbox("NIS2", value=True)
        check_dsa = st.checkbox("DSA", value=False)
        check_dma = st.checkbox("DMA", value=False)
        
        regulation_types = []
        if check_gdpr:
            regulation_types.append("GDPR")
        if check_ai_act:
            regulation_types.append("AI Act")
        if check_nis2:
            regulation_types.append("NIS2")
        if check_dsa:
            regulation_types.append("DSA")
        if check_dma:
            regulation_types.append("DMA")
        
        st.divider()
        
        # API Key check
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY not set in environment")
            st.info("Set it in .env file or environment variables")
        else:
            st.success("API Key configured")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["Upload Document", "Analysis Results", "Reports"])
    
    with tab1:
        st.header("Upload Policy Document")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt"],
            help="Upload a PDF, DOCX, or TXT file containing your policy"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            
            # Display file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Filename", uploaded_file.name)
            with col2:
                st.metric("Size", f"{uploaded_file.size / 1024:.2f} KB")
            with col3:
                st.metric("Type", uploaded_file.name.split('.')[-1].upper())
            
            # Analyze button
            if st.button("Analyze Compliance", type="primary"):
                if not regulation_types:
                    st.warning("Please select at least one regulation to check.")
                else:
                    analyze_document(uploaded_file, regulation_types)
    
    with tab2:
        if st.session_state.analysis_results is not None:
            display_analysis_results(st.session_state.analysis_results)
        else:
            st.info("Upload a document and run analysis to see results here.")
    
    with tab3:
        if st.session_state.analysis_results is not None:
            display_reports(st.session_state.analysis_results)
        else:
            st.info("Generate an analysis to view reports here.")


def analyze_document(uploaded_file, regulation_types: list):
    """Analyze uploaded document for compliance."""
    with st.spinner("Analyzing document... This may take a few minutes."):
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{uploaded_file.name.split('.')[-1]}"
            ) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            try:
                # Run analysis
                orchestrator = st.session_state.orchestrator
                results = orchestrator.analyze_policy(
                    file_path=tmp_path,
                    regulation_types=regulation_types
                )
                
                st.session_state.analysis_results = results
                st.success("Analysis complete!")
                st.rerun()
            
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.exception(e)


def display_analysis_results(results: dict):
    """Display analysis results in a structured way."""
    st.header("Analysis Results")
    
    # Summary metrics
    report_info = results.get("report", {})
    compliance_score = report_info.get("compliance_score", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Compliance Score", f"{compliance_score}/100")
    
    comparison = results.get("comparison_results", {})
    num_discrepancies = len(comparison.get("discrepancies", []))
    
    with col2:
        st.metric("Discrepancies", num_discrepancies)
    
    with col3:
        num_citations = results.get("citations", {}).get("num_citations", 0)
        st.metric("Citations Found", num_citations)
    
    with col4:
        num_chunks = results.get("parsed_document", {}).get("num_chunks", 0)
        st.metric("Document Chunks", num_chunks)
    
    st.divider()
    
    # Compliance score visualization
    st.subheader("Compliance Status")
    score_color = "green" if compliance_score >= 80 else "orange" if compliance_score >= 60 else "red"
    st.progress(compliance_score / 100)
    st.markdown(f"**Overall Compliance: {compliance_score}/100** ({score_color})")
    
    # Discrepancies section
    st.subheader("Identified Discrepancies")
    
    discrepancies = comparison.get("discrepancies", [])
    if discrepancies:
        for i, disc in enumerate(discrepancies, 1):
            if isinstance(disc, dict):
                disc_type = disc.get("type", "discrepancy")
                description = disc.get("description", str(disc))
                severity = disc.get("severity", "medium")
            else:
                disc_type = "discrepancy"
                description = str(disc)
                severity = "medium"
            
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            
            with st.expander(f"{severity_emoji} Issue {i}: {disc_type}"):
                st.write(description)
                st.caption(f"Severity: {severity}")
    else:
        st.success("No discrepancies found!")
    
    # Citations section
    st.subheader("Regulation Citations")
    citations = results.get("citations", {})
    citations_by_reg = citations.get("citations_by_regulation", {})
    
    if citations_by_reg:
        for reg_type, cit_list in citations_by_reg.items():
            with st.expander(f"{reg_type} ({len(cit_list)} citations)"):
                for cit in cit_list:
                    ref = cit.get("reference", "Unknown")
                    st.write(f"• Article {ref}")
    else:
        st.info("No citations extracted.")
    
    # Regulation types found
    st.subheader("Regulations Analyzed")
    reg_types = results.get("regulation_retrieval", {}).get("regulation_types", [])
    if reg_types:
        st.write(", ".join(reg_types))
    else:
        st.info("No regulations matched.")


def display_reports(results: dict):
    """Display generated reports and download options."""
    st.header("Generated Reports")
    
    report_info = results.get("report", {})
    report_path = report_info.get("report_path")
    
    if report_path and Path(report_path).exists():
        # Report summary
        st.subheader("Report Summary")
        summary = report_info.get("report_summary", "No summary available.")
        st.write(summary)
        
        # Download buttons
        st.divider()
        st.subheader("Download Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # PDF download
            with open(report_path, "rb") as pdf_file:
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_file.read(),
                    file_name=Path(report_path).name,
                    mime="application/pdf"
                )
        
        with col2:
            # JSON download
            json_data = str(results)
            st.download_button(
                label="Download JSON Data",
                data=json_data,
                file_name="analysis_results.json",
                mime="application/json"
            )
        
        st.info(f"Report saved at: {report_path}")
    else:
        st.warning("Report not found. Please run analysis first.")


if __name__ == "__main__":
    main()
