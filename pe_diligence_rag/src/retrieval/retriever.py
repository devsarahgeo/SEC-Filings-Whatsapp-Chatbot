"""
Retriever for FAISS vector search with metadata filtering.
Provides hybrid retrieval combining vector similarity + metadata filters.
"""

from typing import Optional, List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from ..config.settings import RETRIEVAL_K
from ..indexing.embedder import get_embeddings


class SECRetriever:
    """Retriever for SEC filing chunks using FAISS."""

    # Index path mapping
    INDEX_MAP = {
        "1": "risk_factors",
        "2": "md&a",
        "3": "md&a",
        "4": "business",
        "5": "risk_factors"
    }

    SECTION_INDEX_MAP = {
        "Risk Factors": "risk_factors",
        "MD&A": "md&a",
        "Business": "business",
        "Financial Statements": "financial_statements"
    }

    def __init__(self, indexes_dir: str = None):
        self.embeddings = get_embeddings()
        self.indexes_dir = indexes_dir
        self._indexes = {}  # Cache for loaded indexes
        
        # Create indexes directory if it doesn't exist
        from ..config.settings import INDEXES_DIR
        import os
        INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    def check_indexes(self) -> dict:
        """Check which indexes are available."""
        from ..config.settings import INDEXES_DIR
        import os
        
        status = {}
        for index_name in ["risk_factors", "md&a", "business", "financial_statements"]:
            index_path = INDEXES_DIR / index_name
            status[index_name] = os.path.exists(index_path) and os.path.isdir(index_path)
        
        return status

    def _load_index(self, index_name: str) -> Optional[FAISS]:
        """Load a FAISS index from disk."""
        if index_name in self._indexes:
            return self._indexes[index_name]

        from ..config.settings import INDEXES_DIR
        import os

        index_path = INDEXES_DIR / index_name

        # Check if path exists
        if not os.path.exists(index_path):
            print(f"⚠️ Index path not found: {index_path}")
            return None
        
        # Check if it's a directory
        if not os.path.isdir(index_path):
            print(f"⚠️ Index path is not a directory: {index_path}")
            return None

        # Check if index files exist in the directory
        required_files = ["index.faiss", "index.pkl"]
        has_required = any(os.path.exists(index_path / f) for f in required_files)
        if not has_required:
            print(f"⚠️ No FAISS index files found in: {index_path}")
            return None

        try:
            index = FAISS.load_local(
                str(index_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            self._indexes[index_name] = index
            return index
        except Exception as e:
            print(f"❌ Error loading FAISS index {index_name}: {e}")
            print(f"   This usually means indexes haven't been built yet.")
            print(f"   Run: python main.py --mode build to build indexes.")
            return None

    def retrieve(
        self,
        query: str,
        option: str = None,
        section: str = None,
        ticker: str = None,
        year: int = None,
        k: int = RETRIEVAL_K
    ) -> List[Document]:
        """
        Retrieve relevant documents with metadata filtering.

        Args:
            query: Search query
            option: Menu option (1-5)
            section: Section name
            ticker: Company ticker
            year: Fiscal year
            k: Number of results

        Returns:
            List of relevant Documents
        """
        # Determine which index to use
        if section:
            index_name = self.SECTION_INDEX_MAP.get(section, "md&a")
        elif option:
            index_name = self.INDEX_MAP.get(option, "md&a")
        else:
            index_name = "md&a"

        index = self._load_index(index_name)
        if index is None:
            return []

        # Build filter
        filter_dict = {}
        if ticker:
            filter_dict["ticker"] = ticker.upper()
        if year:
            filter_dict["year"] = year

        # Search
        if filter_dict:
            # First get more results, then filter
            results = index.similarity_search("*", k=100)

            # Apply metadata filter manually
            filtered = []
            for doc in results:
                match = True
                for key, value in filter_dict.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if match:
                    filtered.append(doc)

            return filtered[:k]
        else:
            try:
                return index.similarity_search(query, k=k)
            except Exception as e:
                print(f"❌ Similarity search error: {e}")
                return []

    def retrieve_for_chain(
        self,
        query: str,
        ticker: str,
        year: int = None,
        section: str = "Risk Factors",
        k: int = RETRIEVAL_K
    ) -> str:
        """
        Retrieve documents and format as context string for LLM.

        Args:
            query: Search query
            ticker: Company ticker
            year: Fiscal year
            section: Section to search
            k: Number of results

        Returns:
            Formatted context string
        """
        docs = self.retrieve(
            query=query,
            section=section,
            ticker=ticker,
            year=year,
            k=k
        )

        if not docs:
            return "No relevant documents found."

        # Format as context
        context_parts = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            part = f"[Document {i}] ({meta.get('section', 'Unknown')}, {meta.get('year', 'N/A')})\n"
            part += doc.page_content
            context_parts.append(part)

        return "\n\n".join(context_parts)


def retrieve(
    query: str,
    ticker: str = None,
    year: int = None,
    option: str = None,
    section: str = None,
    k: int = RETRIEVAL_K
) -> List[Document]:
    """Convenience function for retrieval."""
    retriever = SECRetriever()
    return retriever.retrieve(
        query=query,
        option=option,
        section=section,
        ticker=ticker,
        year=year,
        k=k
    )
