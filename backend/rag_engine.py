"""
Step 4 - RAG chat: index the transcript in a vector database so users can ask
questions and get answers grounded only in what was actually said.

  transcript -> 500-char chunks -> embeddings (all-MiniLM-L6-v2) -> ChromaDB
  question   -> top-4 similar chunks -> Mistral answers using only those chunks
"""

import os
import uuid

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.llm_service import get_llm

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert meeting assistant. Answer the user's question based ONLY on the "
        "meeting transcript context below.\n"
        "If the answer is not in the context, say: "
        "\"I could not find this information in the meeting transcript.\"\n"
        "Be concise and precise. If quoting someone, mention it clearly.\n\n"
        "Context from meeting transcript:\n{context}",
    ),
    ("human", "{question}"),
])

_embeddings = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Loads the embedding model once and reuses it."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})
    return _embeddings


def build_rag_chain(transcript: str):
    """Indexes the transcript and returns a chain that answers questions about it."""
    chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_text(transcript)

    # In-memory collection with a unique name: every analysis (and every user) gets its own index
    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=get_embeddings(),
        collection_name=f"meeting_{uuid.uuid4().hex}",
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    def format_docs(docs) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | get_llm(temperature=0.3)
        | StrOutputParser()
    )


def ask_question(rag_chain, question: str) -> str:
    return rag_chain.invoke(question)
