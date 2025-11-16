"""
EU Policy Compliance Checker - Main Application

This module implements a RAG-based compliance checker for EU regulations.
It provides an interactive Chainlit interface for querying compliance questions
and generating detailed PDF reports.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import chainlit as cl
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from report_generator import ComplianceReportGenerator


# Load environment variables
load_dotenv()


class ComplianceRAGSystem:
    """
    Retrieval-Augmented Generation system for EU compliance analysis.
    
    This class handles the vector store initialization, retrieval logic,
    and the RAG chain construction for answering compliance questions.
    """
    
    def __init__(
        self,
        chroma_dir: str = "chroma_eu_laws",
        embed_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o-mini",
        retrieval_k: int = 4
    ):
        """
        Initialize the RAG system with vector store and LLM.
        
        Args:
            chroma_dir: Directory path for ChromaDB persistence
            embed_model: OpenAI embedding model name
            llm_model: OpenAI chat model name
            retrieval_k: Number of documents to retrieve
        """
        self.chroma_dir = chroma_dir
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.retrieval_k = retrieval_k
        
        # Ensure directory exists
        Path(chroma_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings and vector store
        self.embedding = OpenAIEmbeddings(model=embed_model)
        self.vectorstore = Chroma(
            persist_directory=chroma_dir,
            embedding_function=self.embedding
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": retrieval_k}
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        
        # Build RAG chain
        self.rag_chain = self._build_rag_chain()
    
    def _build_rag_chain(self):
        """
        Construct the RAG chain that combines retrieval and generation.
        
        Returns:
            A Runnable chain that takes a question and returns an answer
        """
        prompt = ChatPromptTemplate.from_template("""
You are a legal expert specialized in European and GDPR law.

Use the following retrieved context to answer the user's question precisely.
If uncertain, say you don't know.

Context:
{context}

Question:
{question}

Answer in a clear, structured format. Highlight key legal principles, 
relevant EU directives, and practical implications.
""")
        
        rag_chain = (
            RunnableMap({
                "context": self.retriever | (
                    lambda docs: "\n\n".join([d.page_content for d in docs])
                ),
                "question": RunnablePassthrough()
            })
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def query(self, question: str) -> str:
        """
        Process a compliance question through the RAG pipeline.
        
        Args:
            question: User's compliance question
        
        Returns:
            Generated answer based on retrieved context
        """
        return self.rag_chain.invoke(question)
    
    def generate_summary(self, question: str, full_answer: str) -> str:
        """
        Generate a concise summary of the compliance analysis.
        
        Args:
            question: Original user question
            full_answer: Complete RAG-generated answer
        
        Returns:
            Concise summary (6-8 lines) formatted in Markdown
        """
        summary_prompt = f"""
You are an EU compliance expert.
Provide a concise summary (max 6-8 lines) answering the user's question below.

Question: "{question}"
Analysis: "{full_answer}"

Format your response naturally and clearly in Markdown.
"""
        
        response = self.llm.invoke(summary_prompt)
        return response.content.strip()


class ComplianceApp:
    """
    Main application class that coordinates RAG system and report generation.
    """
    
    def __init__(
        self,
        chroma_dir: Optional[str] = None,
        embed_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o-mini",
        output_dir: Optional[str] = None
    ):
        """
        Initialize the compliance checker application.
        
        Args:
            chroma_dir: Directory for ChromaDB (defaults to env or "chroma_eu_laws")
            embed_model: Embedding model name
            llm_model: Chat model name
            output_dir: Directory for generated PDF reports
        """
        # Validate API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Create a .env file or export "
                "the variable before running."
            )
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Initialize components
        chroma_dir = chroma_dir or os.getenv("CHROMA_DIR", "chroma_eu_laws")
        self.rag_system = ComplianceRAGSystem(
            chroma_dir=chroma_dir,
            embed_model=embed_model,
            llm_model=llm_model
        )
        self.report_generator = ComplianceReportGenerator(
            llm_model=llm_model,
            output_dir=output_dir
        )
    
    async def handle_message(self, message: cl.Message) -> None:
        """
        Process an incoming message and generate response with report.
        
        Args:
            message: Chainlit message object containing user question
        """
        question = message.content
        
        # Send processing status
        await cl.Message(
            content="**Analyzing your question... please wait a few seconds.**"
        ).send()
        
        try:
            # Step 1: Run RAG pipeline
            rag_answer = self.rag_system.query(question)
            
            # Step 2: Generate concise summary
            short_response = self.rag_system.generate_summary(question, rag_answer)
            
            # Step 3: Generate full PDF report
            report_path = self.report_generator.generate(
                question=question,
                rag_answer=rag_answer
            )
            
            # Step 4: Display summary in chat
            await cl.Message(
                content=short_response + (
                    "\n\n**A detailed compliance report (with full analysis, "
                    "score, and next steps) is available below.**"
                )
            ).send()
            
            # Step 5: Attach PDF report for download
            await cl.Message(
                content="**Download your detailed compliance report:**",
                elements=[cl.File(
                    name=os.path.basename(report_path),
                    path=report_path
                )]
            ).send()
        
        except Exception as e:
            await cl.Message(
                content=f"**Error during analysis:** {str(e)}"
            ).send()


# Initialize application
app = ComplianceApp()


# Chainlit event handlers
@cl.on_chat_start
async def start():
    """Initialize chat session with welcome message."""
    await cl.Message(
        content=(
            "**Welcome to the EU Policy Compliance Checker**\n\n"
            "Ask any question related to EU regulations (GDPR, AI Act, NIS2, etc.)\n"
            "I'll analyze it, retrieve relevant laws, and generate a full compliance report."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    await app.handle_message(message)