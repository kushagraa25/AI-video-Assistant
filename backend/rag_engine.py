import os
import torch
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

# Suppress HuggingFace symlink warning on Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

try:
    torch.set_num_threads(min(4, os.cpu_count() or 1))
except Exception:
    pass

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from backend.llm_service import get_llm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "vector_db")
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_embeddings_cache = None

def get_embeddings():
    """Returns cached HuggingFace embeddings instance."""
    global _embeddings_cache
    if _embeddings_cache is None:
        _embeddings_cache = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"}
        )
    return _embeddings_cache

def build_vector_store(transcript: str) -> Chroma:
    """
    Chunks transcript into small overlapping passages, generates dense embeddings,
    and stores them in persistent local ChromaDB.
    """
    os.makedirs(CHROMA_DIR, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(transcript) if transcript.strip() else ["No content in meeting transcript."]

    docs = [
        Document(page_content=chunk, metadata={'chunk_index': i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()

    # Reset any existing collection to avoid mixing transcripts from different sessions
    try:
        existing_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR
        )
        existing_store.delete_collection()
    except Exception:
        pass

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )

    return vector_store

def load_vector_store() -> Chroma:
    """Loads existing ChromaDB vector store."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

def get_retriever(vector_store: Chroma, k: int = 4):
    """Returns top-k similarity retriever."""
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

def format_docs(docs):
    """Concatenates retrieved documents for LLM context."""
    return "\n\n".join([doc.page_content for doc in docs])

def get_rag_prompt():
    """Returns system prompt constraining responses strictly to retrieved transcript context."""
    return ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

def build_rag_chain(transcript: str):
    """Builds an end-to-end LCEL RAG chain for the provided transcript."""
    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm(temperature=0.3)
    prompt = get_rag_prompt()

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

def load_rag_chain():
    """Rebuilds RAG chain from existing vector store."""
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm(temperature=0.3)
    prompt = get_rag_prompt()

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

def ask_question(rag_chain, question: str) -> str:
    """Queries the RAG chain and returns the grounded answer."""
    return rag_chain.invoke(question)
