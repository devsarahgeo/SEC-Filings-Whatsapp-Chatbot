"""
SEC 10-K Parser.
Parses SEC filings into structured sections and chunks.
Extracts text from HTML, splits by SEC Item structure.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from ..config.settings import SEC_SECTIONS, PRIORITY_SECTIONS, MAX_CHUNK_WORDS


@dataclass
class Chunk:
    """A structured chunk from a SEC filing."""
    ticker: str
    company: str
    section: str
    section_id: str
    chunk_text: str
    chunk_index: int
    fiscal_year: int
    filed_date: str
    accession: str
    word_count: int


class SECParser:
    """Parses SEC 10-K filings into structured chunks."""

    def __init__(self, max_words: int = MAX_CHUNK_WORDS):
        self.max_words = max_words

    def parse(self, html: str, metadata: dict) -> list[Chunk]:
        """
        Parse a 10-K filing HTML into structured chunks.

        Args:
            html: Raw HTML content from SEC
            metadata: Dict with ticker, company, fiscal_year, filed_date, accession

        Returns:
            List of Chunk objects
        """
        # Extract plain text from HTML
        text = self._html_to_text(html)

        # Split by sections
        sections = self._extract_sections(text)

        # Convert to chunks
        chunks = []
        for section_id, section_name in SEC_SECTIONS.items():
            if section_id not in PRIORITY_SECTIONS:
                continue

            if section_id not in sections:
                continue

            section_text = sections[section_id]
            section_chunks = self._chunk_text(section_text, section_name)

            for i, chunk_text in enumerate(section_chunks):
                if len(chunk_text.split()) < 50:  # Skip too short chunks
                    continue

                chunks.append(Chunk(
                    ticker=metadata.get("ticker", ""),
                    company=metadata.get("company", ""),
                    section=section_name,
                    section_id=section_id,
                    chunk_text=chunk_text,
                    chunk_index=i,
                    fiscal_year=metadata.get("fiscal_year", 2024),
                    filed_date=metadata.get("filed_date", ""),
                    accession=metadata.get("accession", ""),
                    word_count=len(chunk_text.split())
                ))

        return chunks

    def _html_to_text(self, html: str) -> str:
        """
        Convert iXBRL HTML to plain text, preserving readable content.
        Handles SEC 10-K filings with embedded XBRL data.
        """
        import html as html_lib
        
        # Decode HTML entities first
        html = html_lib.unescape(html)
        
        # Try XML parser for iXBRL, fall back to HTML
        try:
            soup = BeautifulSoup(html, "xml")
        except:
            soup = BeautifulSoup(html, "html.parser")

        # Remove elements that are not readable content
        for tag in soup(["script", "style", "ix:header", "ix:hidden", "head"]):
            tag.decompose()

        # Remove divs with display:none (XBRL metadata)
        for div in soup.find_all("div", {"style": re.compile("display.*none", re.I)}):
            div.decompose()

        # Remove XBRL-specific tags but keep their text content
        for tag in soup.find_all(["ix:nonfraction", "ix:continuation", "ix:nonnumeric"]):
            tag.unwrap()  # Remove tag but keep content

        # Extract visible text
        text = soup.get_text(separator="\n", strip=True)

        # Clean up XBRL artifacts
        # Remove namespace prefixes (e.g., "us-gaap:RevenueNet" → "RevenueNet")
        text = re.sub(r'[a-z]+:[a-zA-Z]+', '', text)
        # Remove URLs
        text = re.sub(r'http[s]?://[^\s]+', '', text)
        # Remove context IDs (e.g., "c-123")
        text = re.sub(r'c-\d+', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)

        return text

    def _extract_sections(self, text: str) -> dict[str, str]:
        """
        Extract SEC sections from filing text.
        Intelligently skips TOC and handles various formatting.
        """
        sections = {}

        # Find and skip TABLE OF CONTENTS
        toc_match = re.search(r'TABLE\s+OF\s+CONTENTS', text)
        if toc_match:
            # TOC usually ends before we see substantial content repeated
            # Look for the first Item section with real content (not TOC listings with page numbers)
            search_start = toc_match.end()
            
            # Find "PART I" or first real Item 1 section with business content
            part_match = re.search(r'(?:PART\s+I|Part\s+I).*?Item\s+1[A]?\s*\.\s+\w+', text[search_start:], re.IGNORECASE | re.DOTALL)
            if part_match:
                # Start search from after the Part heading
                search_text_start = search_start + part_match.start()
            else:
                search_text_start = search_start
        else:
            search_text_start = 0

        # Find all Item sections after TOC
        item_positions = {}
        
        for section_id in PRIORITY_SECTIONS:
            # Build regex pattern for this section
            if len(section_id) > 1:
                # Letter items like 1A, 7A
                pattern = rf'Item\s+{re.escape(section_id)}\s*\.?\s+([^\n]+)'
            else:
                # Single digit items
                pattern = rf'Item\s+{section_id}\s*\.?\s+([^\n]+)'
            
            # Find ALL matches starting from after TOC
            for match in re.finditer(pattern, text[search_text_start:], re.IGNORECASE):
                # Check if this looks like real content or TOC
                # Real content will have 100+ chars until next Item
                content_start = search_text_start + match.end()
                next_item = re.search(r'\nItem\s+\d+', text[content_start:])
                if next_item:
                    content_length = next_item.start()
                else:
                    content_length = len(text) - content_start
                
                # If substantial content, this is likely the real section (not TOC)
                if content_length > 500:
                    item_positions[section_id] = search_text_start + match.start()
                    break  # Found the real one, stop looking

        if not item_positions:
            return sections

        # Sort by position in document
        sorted_items = sorted(item_positions.items(), key=lambda x: x[1])

        # Extract content for each section
        for i, (section_id, start_pos) in enumerate(sorted_items):
            # Find end: start of next Item
            next_pos = len(text)
            if i + 1 < len(sorted_items):
                next_pos = sorted_items[i + 1][1]

            # Extract section text
            section_full = text[start_pos:next_pos].strip()

            # Remove the header line (Item X. Title\n)
            first_newline = section_full.find('\n')
            if first_newline > 0:
                content = section_full[first_newline+1:].strip()
            else:
                content = section_full

            # Add to results if has content
            if len(content) > 500:
                sections[section_id] = content

        return sections

    def _chunk_text(self, text: str, section: str) -> list[str]:
        """
        Split section text into semantic chunks.
        Aims for chunks of ~300 words while preserving paragraph structure.
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = []
        current_words = 0

        for para in paragraphs:
            words = len(para.split())

            # If single paragraph is too long, split it further
            if words > self.max_words:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_words = 0

                # Split long paragraph by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    sent_words = len(sent.split())
                    if current_words + sent_words > self.max_words and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = [sent]
                        current_words = sent_words
                    else:
                        current_chunk.append(sent)
                        current_words += sent_words
            else:
                if current_words + words > self.max_words and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [para]
                    current_words = words
                else:
                    current_chunk.append(para)
                    current_words += words

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def chunks_to_documents(self, chunks: list[Chunk]) -> list[Document]:
        """Convert Chunk objects to LangChain Documents."""
        docs = []
        for chunk in chunks:
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

    def parse_to_documents(self, html: str, metadata: dict) -> list[Document]:
        """Parse HTML and return LangChain Documents directly."""
        chunks = self.parse(html, metadata)
        return self.chunks_to_documents(chunks)
