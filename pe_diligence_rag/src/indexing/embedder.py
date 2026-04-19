"""
HuggingFace Embeddings (Free, local).
Uses sentence-transformers for embeddings.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from ..config.settings import EMBEDDING_MODEL


# Singleton embeddings instance
_embeddings = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Get or create the HuggingFace embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},  # Use CPU (can change to "cuda" for GPU)
            encode_kwargs={"normalize_embeddings": True}  # Normalize for cosine similarity
        )
    return _embeddings


def create_vectorstore(documents, embeddings=None, save_path: str = None):
    """
    Create a FAISS vector store from documents.

    Args:
        documents: List of LangChain Documents
        embeddings: Embeddings instance (uses default if None)
        save_path: Optional path to save the index

    Returns:
        FAISS vector store
    """
    if embeddings is None:
        embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    if save_path:
        vectorstore.save_local(save_path)

    return vectorstore


def load_vectorstore(load_path: str, embeddings=None):
    """
    Load a FAISS vector store from disk.

    Args:
        load_path: Path to the saved index
        embeddings: Embeddings instance (uses default if None)

    Returns:
        FAISS vector store
    """
    if embeddings is None:
        embeddings = get_embeddings()

    return FAISS.load_local(
        load_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )
