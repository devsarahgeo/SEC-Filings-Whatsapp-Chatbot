"""
FAISS Index Builder.
Builds per-section FAISS indexes from structured chunks.
"""

import json
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from ..config.settings import INDEXES_DIR, CHUNKS_DIR
from ..ingestion.loader import ChunkLoader
from ..ingestion.parser import SECParser
from .embedder import get_embeddings, get_embeddings


class FAISSBuilder:
    """Builds and manages FAISS indexes for SEC filing chunks."""

    def __init__(self, chunks_dir: Path = None, indexes_dir: Path = None):
        self.chunks_dir = chunks_dir or CHUNKS_DIR
        self.indexes_dir = indexes_dir or INDEXES_DIR
        self.loader = ChunkLoader()
        self.embeddings = get_embeddings()

    def chunks_to_documents(self, chunks: list) -> list[Document]:
        """Convert chunks to LangChain Documents."""
        docs = []
        for chunk in chunks:
            if isinstance(chunk, dict):
                docs.append(Document(
                    page_content=chunk["chunk_text"],
                    metadata={
                        "ticker": chunk["ticker"],
                        "company": chunk["company"],
                        "section": chunk["section"],
                        "section_id": chunk["section_id"],
                        "year": chunk["fiscal_year"],
                        "filed_date": chunk["filed_date"],
                        "accession": chunk["accession"],
                        "chunk_index": chunk["chunk_index"]
                    }
                ))
            else:
                # Assume it's a Chunk object
                docs.append(Document(
                    page_content=chunk.chunk_text,
                    metadata={
                        "ticker": chunk.ticker,
                        "company": chunk.company,
                        "section": chunk.section,
                        "section_id": chunk.section_id,
                        "year": chunk.fiscal_year,
                        "filed_date": chunk.filed_date,
                        "accession": chunk.accession,
                        "chunk_index": chunk.chunk_index
                    }
                ))
        return docs

    def build_section_index(self, section: str, save_path: Path = None) -> FAISS:
        """
        Build a FAISS index for a specific section.

        Args:
            section: Section name (e.g., "Risk Factors")
            save_path: Path to save the index

        Returns:
            FAISS vector store
        """
        print(f"Building index for section: {section}")

        # Load all chunks
        chunks = self.loader.load_all_chunks()
        print(f"  Loaded {len(chunks)} total chunks")

        # Filter to this section
        section_chunks = [c for c in chunks if c.section == section]
        print(f"  Found {len(section_chunks)} chunks for {section}")

        if not section_chunks:
            print(f"  No chunks found for section: {section}")
            return None

        # Convert to documents
        docs = self.chunks_to_documents(section_chunks)

        # Build index
        vectorstore = FAISS.from_documents(
            documents=docs,
            embedding=self.embeddings
        )

        # Save
        if save_path:
            save_path = Path(save_path)
            save_path.mkdir(parents=True, exist_ok=True)
            vectorstore.save_local(str(save_path))
            print(f"  Saved to {save_path}")

        return vectorstore

    def build_all_indexes(self) -> dict[str, FAISS]:
        """
        Build FAISS indexes for all priority sections.

        Returns:
            Dict of section_name -> FAISS vector store
        """
        indexes = {}

        for section in ["Risk Factors", "MD&A", "Business", "Financial Statements"]:
            save_path = self.indexes_dir / section.lower().replace(' ', '_')
            index = self.build_section_index(section, save_path)
            if index:
                indexes[section] = index

        return indexes

    def add_to_index(self, section: str, chunks: list, index_path: Path):
        """Add new chunks to an existing index."""
        index = self.load_index(section, index_path)

        if index is None:
            # Create new index
            docs = self.chunks_to_documents(chunks)
            index = FAISS.from_documents(docs, self.embeddings)
            index_path.mkdir(parents=True, exist_ok=True)
            index.save_local(str(index_path))
            return index

        # Add to existing
        docs = self.chunks_to_documents(chunks)
        index.add_documents(docs)
        index.save_local(str(index_path))
        return index

    def load_index(self, section: str, index_path: Path = None) -> Optional[FAISS]:
        """Load a FAISS index from disk."""
        if index_path is None:
            index_path = self.indexes_dir / section.lower().replace(' ', '_')

        if not index_path.exists():
            return None

        return FAISS.load_local(
            str(index_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )


def build_all_indexes():
    """Convenience function to build all indexes."""
    builder = FAISSBuilder()
    return builder.build_all_indexes()


def load_section_index(section: str) -> FAISS:
    """Convenience function to load a section index."""
    builder = FAISSBuilder()
    return builder.load_index(section)
