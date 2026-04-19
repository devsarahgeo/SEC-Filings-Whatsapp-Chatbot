#!/usr/bin/env python3
"""
PE Due Diligence RAG System - Main Entry Point

Usage:
    python main.py --mode server      # Start WhatsApp server
    python main.py --mode ingest     # Fetch SEC filings
    python main.py --mode index      # Build FAISS indexes
    python main.py --mode all        # Full pipeline
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description="PE Due Diligence RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--mode",
        choices=["server", "ingest", "index", "all"],
        default="server",
        help="Mode to run"
    )
    parser.add_argument(
        "--ticker",
        help="Ticker symbol (for ingest mode)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of filings to fetch (default: 10)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Server port (default: 5000)"
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip indexing after ingestion"
    )

    args = parser.parse_args()

    # ========================
    # SERVER MODE
    # ========================
    if args.mode == "server":
        print("=" * 60)
        print("🚀 PE DUE DILIGENCE RAG - WhatsApp Server")
        print("=" * 60)
        print(f"\n📡 Starting server on http://{args.host}:{args.port}")
        print("📱 Configure Twilio webhook to your ngrok URL")
        print("   Example: ngrok http 5000")
        print("\nPress Ctrl+C to stop\n")

        from src.api.server import start_server
        start_server(host=args.host, port=args.port)

    # ========================
    # INGEST MODE
    # ========================
    elif args.mode == "ingest":
        print("=" * 60)
        print("📥 SEC FILING INGESTION")
        print("=" * 60)

        if not args.ticker:
            print("❌ Error: --ticker required for ingest mode")
            print("   Example: python main.py --mode ingest --ticker AAPL --limit 10")
            return

        print(f"\n📊 Fetching filings for: {args.ticker.upper()}")
        print(f"📝 Limit: {args.limit} filings\n")

        # Import ingestion modules
        from src.ingestion.fetcher import SECFetcher
        from src.ingestion.parser import SECParser
        from src.ingestion.loader import ChunkLoader
        from src.config.settings import RAW_DIR, CHUNKS_DIR

        # Initialize
        fetcher = SECFetcher()
        parser = SECParser()
        loader = ChunkLoader()

        # Fetch filings
        print("🔍 Fetching from SEC EDGAR...")
        results = fetcher.fetch_10k(args.ticker, limit=args.limit, save_raw=True)
        print(f"✅ Downloaded {len(results)} filings\n")

        # Parse and save chunks
        total_chunks = 0
        for result in results:
            ticker = result["ticker"]
            cik = result["cik"]
            html = result["html"]
            filing = result["filing"]

            print(f"📄 Parsing {ticker} {filing.filed_date}...")

            metadata = {
                "ticker": ticker,
                "company": filing.company,
                "fiscal_year": filing.fiscal_year,
                "filed_date": filing.filed_date,
                "accession": filing.accession_number
            }

            chunks = parser.parse(html, metadata)
            loader.save_chunks(chunks)

            print(f"   → {len(chunks)} chunks saved")
            total_chunks += len(chunks)

        print(f"\n✅ TOTAL: {len(results)} filings, {total_chunks} chunks saved to:")
        print(f"   📁 Raw: {RAW_DIR}/{args.ticker.upper()}/")
        print(f"   📁 Chunks: {CHUNKS_DIR}/")

        # Build indexes if not skipped
        if not args.skip_index:
            print("\n🔨 Building FAISS indexes...")
            run_index()
            print("✅ Indexing complete")

    # ========================
    # INDEX MODE
    # ========================
    elif args.mode == "index":
        print("=" * 60)
        print("🔨 BUILDING FAISS INDEXES")
        print("=" * 60)
        run_index()

    # ========================
    # ALL MODE
    # ========================
    elif args.mode == "all":
        print("=" * 60)
        print("🔄 FULL PIPELINE")
        print("=" * 60)

        if not args.ticker:
            print("❌ Error: --ticker required for all mode")
            return

        print(f"\nRunning full pipeline for: {args.ticker.upper()}\n")

        # Ingest
        print("Step 1/2: Ingesting SEC filings...")
        args.mode = "ingest"
        args.skip_index = True
        # Re-parse but don't rebuild args
        import sys
        sys.argv = ["main.py", "--mode", "ingest", "--ticker", args.ticker, "--limit", str(args.limit)]
        # Just run ingest directly
        from src.ingestion.fetcher import SECFetcher
        from src.ingestion.parser import SECParser
        from src.ingestion.loader import ChunkLoader

        fetcher = SECFetcher()
        parser = SECParser()
        loader = ChunkLoader()
        results = fetcher.fetch_10k(args.ticker, limit=args.limit, save_raw=True)

        for result in results:
            ticker = result["ticker"]
            filing = result["filing"]
            chunks = parser.parse(result["html"], {
                "ticker": ticker,
                "company": filing.company,
                "fiscal_year": filing.fiscal_year,
                "filed_date": filing.filed_date,
                "accession": filing.accession_number
            })
            loader.save_chunks(chunks)

        print(f"✅ Ingested {len(results)} filings\n")

        # Index
        print("Step 2/2: Building indexes...")
        run_index()
        print("✅ Full pipeline complete!")


def run_index():
    """Build FAISS indexes."""
    from src.indexing.faiss_builder import FAISSBuilder
    from src.config.settings import INDEXES_DIR

    builder = FAISSBuilder()

    print("\n📦 Building indexes for sections:")
    for section in ["Risk Factors", "MD&A", "Business", "Financial Statements"]:
        print(f"   - {section}...")

    indexes = builder.build_all_indexes()

    print(f"\n✅ Built {len(indexes)} indexes")
    print(f"   📁 Indexes saved to: {INDEXES_DIR}/")

    # Print counts
    for section, index in indexes.items():
        print(f"   📊 {section}: {index.index.ntotal} vectors")


# ========================
# CLI INTERFACE
# ========================
if __name__ == "__main__":
    main()
