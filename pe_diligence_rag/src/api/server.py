"""
WhatsApp Server - FastAPI + Twilio Webhook.
Handles incoming WhatsApp messages and routes to appropriate chain.
"""

import asyncio
import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pydantic import BaseModel

from ..config.settings import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    WHATSAPP_FROM,
    WHATSAPP_WEBHOOK_URL
)
from ..chains.master_chain import route_and_run
from ..retrieval.router import parse_query
from ..config.settings import MENU_OPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="PE Due Diligence RAG API")

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ========================
# MENU TEXT
# ========================
WELCOME_MENU = """
📊 *PE DUE DILIGENCE RAG*

Welcome! I analyze SEC 10-K filings for private equity due diligence.

*Available companies:* AAPL, MSFT, NVDA, TSLA, GOOGL + more

*INPUT FORMAT:* Option,Ticker,Year
*Example:* 1,AAPL,2024

*OPTIONS:*
1️⃣ Risk Discovery
2️⃣ Business Quality (EBITDA/Margins)
3️⃣ Valuation Assumptions (LBO)
4️⃣ Value Creation
5️⃣ Due Diligence Validation

*Examples:*
• 1,AAPL,2024
• 2,NVDA,2023
• 3,MSFT
• What are TSLA risks?

Reply with: *Option,Ticker,Year* or your question
"""


def get_menu_with_prompt() -> str:
    """Return shorter menu prompt."""
    return """
📊 *MENU:* Option,Ticker,Year
*Ex:* 1,AAPL,2024

1️⃣ Risk | 2️⃣ Business | 3️⃣ Val | 4️⃣ Value | 5️⃣ Diligence

*Or ask your question directly!*
"""


def get_full_menu() -> str:
    """Return the FULL menu - shown 2 seconds after answer."""
    return """
📊 *PE DUE DILIGENCE RAG*

*INPUT FORMAT:* Option,Ticker,Year
*Example:* 1,AAPL,2024

*OPTIONS:*
1️⃣ Risk Discovery
   → Analyze Risk Factors (regulatory, customer concentration, supply chain, litigation)

2️⃣ Business Quality
   → EBITDA trends, margins, revenue, cash flow

3️⃣ Valuation Assumptions
   → Historical growth rates, LBO model inputs

4️⃣ Value Creation
   → Margin improvement, cost efficiency opportunities

5️⃣ Due Diligence Validation
   → Verify management claims vs actuals

*AVAILABLE COMPANIES:* AAPL, MSFT, NVDA, TSLA, GOOGL

*EXAMPLES:*
• 1,AAPL,2024
• 2,NVDA,2023
• 3,MSFT
• What are TSLA risks?

Reply: Option,Ticker,Year or your question
"""


HELP_MENU = """
📋 *COMMANDS:*
/menu - Show menu
/companies - List companies
/status - System status
"""


class WhatsAppMessage(BaseModel):
    """Incoming WhatsApp message model."""
    from_number: str
    body: str


TWILIO_MAX_LENGTH = 1500  # Safe limit


def send_whatsapp(to: str, body: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Automatically splits long messages into chunks.

    Args:
        to: Phone number in format whatsapp:+1XXXXXXXXXX
        body: Message text

    Returns:
        True if sent successfully
    """
    if not twilio_client:
        logger.warning("Twilio client not configured")
        return False

    try:
        # Split into chunks if too long
        messages = split_message(body)

        for i, msg in enumerate(messages, 1):
            if len(messages) > 1:
                msg = f"[{i}/{len(messages)}]\n{msg}"

            message = twilio_client.messages.create(
                from_=WHATSAPP_FROM,
                to=to,
                body=msg
            )
            logger.info(f"Message part {i}/{len(messages)} sent: {message.sid}")

        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


def split_message(text: str, max_length: int = TWILIO_MAX_LENGTH) -> list[str]:
    """Split a long message into chunks that fit Twilio's limit."""
    if len(text) <= max_length:
        return [text]

    chunks = []

    while len(text) > max_length:
        split_point = text.rfind('\n', 0, max_length)
        if split_point < max_length - 200:
            split_point = text.rfind('. ', 0, max_length)
        if split_point < max_length - 100:
            split_point = text.rfind(' ', 0, max_length)
        if split_point < max_length - 50:
            split_point = max_length

        chunks.append(text[:split_point].strip())
        text = text[split_point:].strip()

    if text:
        chunks.append(text)

    return chunks


def format_response(text: str, ticker: str = None, option: str = None) -> str:
    """
    Format LLM response for WhatsApp.
    Keeps messages concise and readable.
    """
    if len(text) <= TWILIO_MAX_LENGTH:
        return text

    # Truncate with note
    return text[:TWILIO_MAX_LENGTH] + "\n\n[...] (truncated)"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "running", "service": "PE Due Diligence RAG"}


@app.get("/status")
async def status():
    """Status check endpoint."""
    return {
        "status": "ok",
        "twilio_configured": twilio_client is not None,
        "webhook_url": WHATSAPP_WEBHOOK_URL
    }


@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Main webhook endpoint for Twilio WhatsApp messages.
    Receives messages, processes them, and sends responses via Twilio API.
    """
    try:
        # Parse form data
        form_data = await request.form()

        from_number = form_data.get("From", "")
        body = form_data.get("Body", "").strip()
        to_number = form_data.get("To", "")

        logger.info(f"[WEBHOOK] Incoming from {from_number}: {body}")

        # Immediately acknowledge webhook
        ack = MessagingResponse()

        # Handle empty message
        if not body:
            logger.info(f"[WEBHOOK] Empty message")
            send_whatsapp(from_number, "Please send a message.")
            return PlainTextResponse(str(ack), media_type="application/xml")

        # Normalize
        body_upper = body.upper().strip()
        body_lower = body.lower().strip()

        # ========================
        # COMMAND HANDLING
        # ========================
        if body_lower.startswith("/"):
            command = body_lower.split()[0]

            if command == "/menu":
                logger.info(f"[WEBHOOK] Command: /menu")
                send_whatsapp(from_number, get_full_menu())
                return PlainTextResponse(str(ack), media_type="application/xml")

            elif command == "/status":
                logger.info(f"[WEBHOOK] Command: /status")
                send_whatsapp(from_number, "✅ System operational.\n\nAvailable commands:\n/menu - Show menu\n/companies - List companies")
                return PlainTextResponse(str(ack), media_type="application/xml")

            elif command == "/companies":
                logger.info(f"[WEBHOOK] Command: /companies")
                companies = list_available_companies()
                send_whatsapp(from_number, companies)
                return PlainTextResponse(str(ack), media_type="application/xml")

            elif command == "/help":
                logger.info(f"[WEBHOOK] Command: /help")
                send_whatsapp(from_number, HELP_MENU)
                return PlainTextResponse(str(ack), media_type="application/xml")

            else:
                logger.info(f"[WEBHOOK] Unknown command: {command}")
                send_whatsapp(from_number, f"Unknown command: {command}.\n\nSend /menu for options.")
                return PlainTextResponse(str(ack), media_type="application/xml")

        # ========================
        # NEW USER (first message or just said "hi", "hello", "start")
        # ========================
        if body_lower in ["hi", "hello", "start", "help", "menu"]:
            send_whatsapp(from_number, WELCOME_MENU)
            return PlainTextResponse(str(ack), media_type="application/xml")

        # ========================
        # PARSE INPUT FORMAT: Option,Ticker,Year or Option,Ticker or just Ticker
        # ========================
        parsed_input = None
        option = None
        ticker = None
        year = None

        # Try comma-separated format: Option,Ticker,Year
        if "," in body:
            parts = [p.strip() for p in body.split(",")]
            if len(parts) >= 2:
                # First part could be option or ticker
                if parts[0] in ["1", "2", "3", "4", "5"]:
                    option = parts[0]
                    ticker = parts[1].upper()
                    year = parts[2] if len(parts) > 2 else None
                else:
                    # Assume: Ticker,Option or Ticker,Year
                    ticker = parts[0].upper()
                    option = parts[1] if parts[1] in ["1", "2", "3", "4", "5"] else None

        # Try space-separated format: Option Ticker Year or Ticker Option Year
        if not option:
            parts = body_upper.split()
            if len(parts) >= 1:
                # Check if first part is option
                if parts[0] in ["1", "2", "3", "4", "5"]:
                    option = parts[0]
                    ticker = parts[1].upper() if len(parts) > 1 else None
                    year = parts[2] if len(parts) > 2 else None
                # Check if last part is option
                elif parts[-1] in ["1", "2", "3", "4", "5"]:
                    option = parts[-1]
                    ticker = parts[0].upper() if len(parts) > 1 else None
                # Just a ticker
                elif len(parts[0]) <= 5 and parts[0].isalpha():
                    ticker = parts[0]

        # ========================
        # PROCESS THE QUERY
        # ========================
        try:
            # Use parsed values or fallback to auto-parse
            if option and ticker:
                parsed = parse_query(f"{option} {ticker}", option)
            elif ticker:
                parsed = parse_query(ticker)
                option = parsed.get("option", "1")
            else:
                parsed = parse_query(body)
                option = parsed.get("option", "1")
                ticker = parsed.get("ticker", "UNKNOWN")

            logger.info(f"[WEBHOOK] Parsed: option={option}, ticker={ticker}, year={year}")

            # Route and run
            result = route_and_run(body, option)
            reply = format_response(result.get("result", str(result)), ticker, option)

            # Send answer FIRST
            logger.info(f"[WEBHOOK] Sending answer to {from_number}")
            send_whatsapp(from_number, reply)
            logger.info(f"[WEBHOOK] ✅ Answer sent")

            # Send menu as SEPARATE message after 2 seconds
            async def send_menu_later():
                await asyncio.sleep(2)
                logger.info(f"[WEBHOOK] Sending menu to {from_number}")
                send_whatsapp(from_number, get_full_menu())

            # Fire and forget - menu will be sent after 2 seconds
            asyncio.create_task(send_menu_later())

        except Exception as e:
            logger.error(f"[WEBHOOK] Error processing request: {e}", exc_info=True)
            error_msg = f"❌ Error: {str(e)[:200]}"
            send_whatsapp(from_number, error_msg)

        return PlainTextResponse(str(ack), media_type="application/xml")

    except Exception as e:
        logger.error(f"[WEBHOOK] Unhandled exception: {e}", exc_info=True)
        ack = MessagingResponse()
        return PlainTextResponse(str(ack), media_type="application/xml")


def list_available_companies() -> str:
    """List all companies that have been ingested."""
    import os
    from ..config.settings import CHUNKS_DIR

    companies = set()
    if CHUNKS_DIR.exists():
        for f in CHUNKS_DIR.glob("*.json"):
            # Filename format: TICKER_section_year_####.json
            ticker = f.stem.split("_")[0]
            companies.add(ticker)

    if not companies:
        return "📋 *No companies ingested yet.*\n\nUse: /ingest TICKER\nExample: /ingest AAPL"

    companies_list = ", ".join(sorted(companies))
    return f"""
📋 *Available Companies:*

{companies_list}

*Total:* {len(companies)} companies

*To analyze:* Option,Ticker,Year
*Example:* 1,AAPL,2024
"""


def start_server(host: str = "0.0.0.0", port: int = 5000):
    """Start the FastAPI server with uvicorn."""
    import uvicorn

    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Webhook URL should be: {WHATSAPP_WEBHOOK_URL}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
