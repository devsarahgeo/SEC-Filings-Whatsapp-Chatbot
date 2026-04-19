# PE Due Diligence RAG System

A free, production-ready RAG system for private equity due diligence using SEC 10-K filings.

## Architecture

```
WhatsApp → Twilio → ngrok → FastAPI → LangChain → Groq (free LLM)
                                              ↓
                                      FAISS Vector Store
                                              ↓
                                   SEC EDGAR (free data)
```

## Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| LLM | Groq Llama 3.3 70B | FREE (14.4K req/min) |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | FREE (local) |
| Vector Store | FAISS | FREE |
| WhatsApp | Twilio | ~$0.01/msg |
| Tunnel | ngrok | FREE tier |
| Framework | LangChain | FREE |

**Total monthly cost: ~$5-10 (Twilio only)**

## Features

### 5 PE Due Diligence Use Cases

1. **Risk Discovery** - Analyze Risk Factors section (regulatory, customer concentration, macro, supply chain, litigation)
2. **Business Quality** - EBITDA trends, margins, cash flow, segment performance
3. **Valuation Assumptions** - Historical growth rates, LBO model inputs
4. **Value Creation** - Margin improvement opportunities, cost inefficiencies
5. **Due Diligence Validation** - Verify management claims vs actuals

### Menu System (WhatsApp)

Send `1-5` for menu options, or type a free-text query:
```
1 - Risk Discovery
2 - Business Quality
3 - Valuation Assumptions
4 - Value Creation
5 - Due Diligence Validation
```

Example queries:
- `1 AAPL risk factors 2024`
- `2 NVDA EBITDA margin trends 3 years`
- `Compare risk profiles of AAPL vs MSFT`

## Setup

### 1. Install Dependencies

```bash
cd pe_diligence_rag
pip install -r requirements.txt
```

### 2. Get Free API Keys

**Groq** (free LLM):
1. Sign up at https://console.groq.com
2. Create API key
3. Add to `.env`: `GROQ_API_KEY=gsk_...`

**Twilio** (WhatsApp):
1. Sign up at https://www.twilio.com
2. Enable WhatsApp sandbox
3. Add credentials to `.env`

### 3. Run

```bash
# Terminal 1: Start ngrok tunnel
ngrok http 5000

# Terminal 2: Start server
python main.py --mode server

# Configure Twilio webhook to your ngrok URL
```

## Usage

### Ingest SEC Filings

```bash
# Fetch and process filings
python main.py --mode ingest --ticker AAPL --limit 10

# Full pipeline (ingest + index)
python main.py --mode all --ticker AAPL --limit 10
```

### Build Indexes

```bash
python main.py --mode index
```

### Start WhatsApp Server

```bash
python main.py --mode server --port 5000
```

## Project Structure

```
pe_diligence_rag/
├── src/
│   ├── ingestion/         # SEC filing fetcher, parser, loader
│   ├── indexing/         # HuggingFace embeddings, FAISS builder
│   ├── retrieval/        # Router, retriever
│   ├── chains/           # LangChain RetrievalQA chains (5 use cases)
│   ├── api/              # FastAPI server, WhatsApp webhook
│   └── config/           # Settings, prompts
├── data/
│   ├── raw/              # Original SEC HTML filings
│   ├── chunks/            # Structured JSON chunks
│   └── metrics/           # Extracted financial metrics
├── indexes/              # FAISS vector indexes
├── main.py               # CLI entry point
└── requirements.txt
```

## How It Works

1. **Ingestion**: Fetch 10-K filings from SEC EDGAR API
2. **Parsing**: Extract SEC sections (Item 1A Risk Factors, Item 7 MD&A, etc.)
3. **Chunking**: Split into semantic chunks (~300 words)
4. **Embedding**: Generate embeddings with HuggingFace (free, local)
5. **Indexing**: Build per-section FAISS indexes
6. **Retrieval**: Query FAISS with metadata filtering (ticker, year, section)
7. **Generation**: Groq Llama 3.3 70B generates analysis (free, fast)
8. **Delivery**: Twilio sends response to WhatsApp

## Menu Options Detail

| Option | Use Case | Example Query |
|--------|----------|---------------|
| 1 | Risk Discovery | "What are key risks for AAPL?" |
| 2 | Business Quality | "Show EBITDA trends for NVDA" |
| 3 | Valuation | "Get LBO model inputs for MSFT" |
| 4 | Value Creation | "Where can AAPL improve margins?" |
| 5 | Validation | "Verify AAPL management claims" |

## Development

```bash
# Run tests
pytest tests/

# Format code
black src/

# Lint
ruff src/
```

## License

MIT
