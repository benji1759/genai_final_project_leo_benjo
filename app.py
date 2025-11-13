import os
from datetime import datetime
import chainlit as cl
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from report_generator import generate_full_compliance_report
from getpass import getpass

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") \
    or getpass("Enter your OpenAI API key: ")
# ----------- CONFIG -----------
CHROMA_DIR = "chroma_eu_laws"
EMBED_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# ----------- BUILD RAG CHAIN -----------
embedding = OpenAIEmbeddings(model=EMBED_MODEL)
vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

prompt = ChatPromptTemplate.from_template("""
You are a legal expert specialized in European and GDPR law.

Use the following retrieved context to answer the user's question precisely.
If uncertain, say you don't know.

Context:
{context}

Question:
{question}

Answer in a clear, structured format. Highlight key legal principles, relevant EU directives, and practical implications.
""")

llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
rag_chain = (
    RunnableMap({
        "context": retriever | (lambda docs: "\n\n".join([d.page_content for d in docs])),
        "question": RunnablePassthrough()
    })
    | prompt
    | llm
    | StrOutputParser()
)

# ----------- CHAINLIT APP -----------

@cl.on_chat_start
async def start():
    await cl.Message(
        content=(
            "👋 **Welcome to the EU Policy Compliance Checker**!\n\n"
            "Ask any question related to EU regulations (GDPR, AI Act, NIS2, etc.)\n"
            "I'll analyze it, retrieve relevant laws, and generate a full compliance report. 🚀"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    question = message.content
    await cl.Message(content="🔍 **Analyzing your question... please wait a few seconds.**").send()

    try:
        # Step 1: Run RAG pipeline
        rag_answer = rag_chain.invoke(question)

        # Step 2: Create short summary
        short_prompt = f"""
        You are an EU compliance expert.
        Provide a concise summary (max 6–8 lines) answering the user's question below.

        Question: "{question}"
        Analysis: "{rag_answer}"

        Format your response naturally and clearly in Markdown.
        """
        short_response = llm.invoke(short_prompt).content.strip()

        # Step 3: Generate the full PDF report
        report_path = generate_full_compliance_report(question, rag_answer)

        # Step 4: Display short summary in the chat
        await cl.Message(
            content=short_response + "\n\n📄 **A detailed compliance report (with full analysis, score, and next steps) is available below.**"
        ).send()

        # Step 5: Attach the report for download
        await cl.Message(
            content="⬇️ **Download your detailed compliance report:**",
            elements=[cl.File(name=os.path.basename(report_path), path=report_path)]
        ).send()

    except Exception as e:
        await cl.Message(content=f"❌ Error during analysis: {str(e)}").send()
