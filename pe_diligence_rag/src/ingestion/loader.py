"""
Loader for saving and loading parsed SEC filings.
Stores chunks as JSON and tracks ingestion state.
"""

import json
from pathlib import Path
from dataclasses import asdict
from typing import Optional

from ..config.settings import CHUNKS_DIR, METRICS_DIR, RAW_DIR
from .parser import Chunk


class ChunkLoader:
    """Save and load structured chunks to/from JSON files."""

    def __init__(self, chunks_dir: Path = None, metrics_dir: Path = None):
        self.chunks_dir = chunks_dir or CHUNKS_DIR
        self.metrics_dir = metrics_dir or METRICS_DIR
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def save_chunk(self, chunk: Chunk) -> Path:
        """Save a single chunk to JSON file."""
        filename = self._chunk_filename(chunk)
        filepath = self.chunks_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(chunk), f, ensure_ascii=False, indent=2)

        return filepath

    def save_chunks(self, chunks: list[Chunk]) -> list[Path]:
        """Save multiple chunks to JSON files."""
        paths = []
        for chunk in chunks:
            path = self.save_chunk(chunk)
            paths.append(path)
        return paths

    def _chunk_filename(self, chunk: Chunk) -> str:
        """Generate filename for a chunk."""
        safe_section = chunk.section.lower().replace(' ', '_').replace('/', '_')
        filename = f"{chunk.ticker}_{safe_section}_{chunk.fiscal_year}_{chunk.chunk_index:04d}.json"
        return filename

    def load_chunk(self, filepath: Path) -> Chunk:
        """Load a chunk from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Chunk(**data)

    def load_all_chunks(self) -> list[Chunk]:
        """Load all chunks from the chunks directory."""
        chunks = []
        for filepath in self.chunks_dir.glob("*.json"):
            try:
                chunk = self.load_chunk(filepath)
                chunks.append(chunk)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue
        return chunks

    def load_chunks_for_company(self, ticker: str) -> list[Chunk]:
        """Load all chunks for a specific company."""
        chunks = []
        pattern = f"{ticker.upper()}_*.json"
        for filepath in self.chunks_dir.glob(pattern):
            try:
                chunk = self.load_chunk(filepath)
                chunks.append(chunk)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue
        return chunks

    def load_chunks_for_section(self, section: str) -> list[Chunk]:
        """Load all chunks for a specific section."""
        chunks = []
        safe_section = section.lower().replace(' ', '_')
        pattern = f"*_{safe_section}_*.json"
        for filepath in self.chunks_dir.glob(pattern):
            try:
                chunk = self.load_chunk(filepath)
                chunks.append(chunk)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue
        return chunks


class MetricsLoader:
    """Load and save extracted financial metrics."""

    def __init__(self, metrics_dir: Path = None):
        self.metrics_dir = metrics_dir or METRICS_DIR
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def save_metrics(self, ticker: str, year: int, metrics: dict) -> Path:
        """Save metrics for a company/year."""
        filename = f"{ticker.upper()}_metrics_{year}.json"
        filepath = self.metrics_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "ticker": ticker.upper(),
                "year": year,
                "metrics": metrics
            }, f, ensure_ascii=False, indent=2)

        return filepath

    def load_metrics(self, ticker: str, year: int) -> Optional[dict]:
        """Load metrics for a company/year."""
        filename = f"{ticker.upper()}_metrics_{year}.json"
        filepath = self.metrics_dir / filename

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_metrics_for_company(self, ticker: str) -> list[dict]:
        """Load all metrics for a company across years."""
        pattern = f"{ticker.upper()}_metrics_*.json"
        results = []
        for filepath in self.metrics_dir.glob(pattern):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue
        return sorted(results, key=lambda x: x['year'])
