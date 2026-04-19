"""
Response Formatter for WhatsApp.
Formats LLM outputs into WhatsApp-friendly messages.
"""

import re

def format_for_whatsapp(
    text: str,
    max_length: int = 1500,
    include_ticker: bool = True,
    ticker: str = None
) -> str:
    """
    Format LLM response for WhatsApp delivery.

    Args:
        text: Raw LLM response
        max_length: Maximum message length
        include_ticker: Whether to include ticker prefix
        ticker: Ticker symbol

    Returns:
        Formatted message ready for WhatsApp
    """
    if not text:
        return "No response generated."

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # Add ticker prefix if requested
    if include_ticker and ticker:
        text = f"📊 *{ticker}*\n\n{text}"

    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length]
        # Try to end at a sentence boundary
        last_period = text.rfind('.')
        if last_period > max_length - 200:
            text = text[:last_period + 1]
        text += "\n\n[...] (response truncated)"

    return text


def format_risk_response(text: str, ticker: str = None) -> str:
    """Format risk analysis response with emoji emphasis."""
    header = "🔍 RISK ANALYSIS"
    if ticker:
        header += f" for {ticker}"

    # Ensure emoji categories are prominent
    text = text.replace("REGULATORY:", "🔴 REGULATORY:")
    text = text.replace("REGULATORY EXPOSURE:", "🔴 REGULATORY EXPOSURE:")
    text = text.replace("CUSTOMER:", "🟠 CUSTOMER CONCENTRATION:")
    text = text.replace("CUSTOMER CONCENTRATION:", "🟠 CUSTOMER CONCENTRATION:")
    text = text.replace("MACRO:", "🟡 MACRO SENSITIVITY:")
    text = text.replace("MACRO SENSITIVITY:", "🟡 MACRO SENSITIVITY:")
    text = text.replace("SUPPLY CHAIN:", "🟢 SUPPLY CHAIN:")
    text = text.replace("LITIGATION:", "🔵 LITIGATION:")
    text = text.replace("PE IMPACT:", "\n⚠️ PE IMPACT:")

    return f"{header}\n\n{text}"


def format_financials_response(text: str, ticker: str = None) -> str:
    """Format financial analysis response."""
    header = "📈 BUSINESS QUALITY"
    if ticker:
        header += f" for {ticker}"

    # Ensure emoji categories
    text = text.replace("REVENUE:", "📊 REVENUE:")
    text = text.replace("EBITDA:", "💵 EBITDA:")
    text = text.replace("CASH FLOW:", "💵 CASH FLOW:")
    text = text.replace("SEGMENTS:", "🏢 SEGMENT PERFORMANCE:")

    return f"{header}\n\n{text}"


def format_valuation_response(text: str, ticker: str = None) -> str:
    """Format valuation assumptions response."""
    header = "💰 VALUATION ASSUMPTIONS"
    if ticker:
        header += f" for {ticker}"

    return f"{header}\n\n{text}"


def format_value_response(text: str, ticker: str = None) -> str:
    """Format value creation response."""
    header = "💡 VALUE CREATION OPPORTUNITIES"
    if ticker:
        header += f" for {ticker}"

    return f"{header}\n\n{text}"


def format_diligence_response(text: str, ticker: str = None) -> str:
    """Format due diligence validation response."""
    header = "✅ DUE DILIGENCE VALIDATION"
    if ticker:
        header += f" for {ticker}"

    text = text.replace("VERIFIED:", "✅ VERIFIED:")
    text = text.replace("DISCREPANCY:", "⚠️ DISCREPANCY FOUND:")
    text = text.replace("WARNING:", "⚠️ WARNING:")

    return f"{header}\n\n{text}"


def format_error(error: str) -> str:
    """Format error message for WhatsApp."""
    return f"❌ Error\n\n{error[:500]}"


def format_success(message: str) -> str:
    """Format success message for WhatsApp."""
    return f"✅ {message}"


def chunk_message(text: str, chunk_size: int = 1500) -> list[str]:
    """
    Split a long message into chunks for WhatsApp.

    Args:
        text: Message to split
        chunk_size: Max characters per chunk

    Returns:
        List of message chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []

    while len(text) > chunk_size:
        # Find last newline before chunk_size
        split_point = text.rfind('\n', 0, chunk_size)

        # If no newline, try sentence
        if split_point < chunk_size - 200:
            split_point = text.rfind('. ', 0, chunk_size)

        # If still no good split, hard cut
        if split_point < chunk_size - 100:
            split_point = chunk_size

        chunks.append(text[:split_point + 1])
        text = text[split_point + 1:].strip()

    if text:
        chunks.append(text)

    return chunks


def format_comparison(text: str, ticker1: str, ticker2: str) -> str:
    """Format comparison response."""
    return f"⚖️ COMPARISON: {ticker1} vs {ticker2}\n\n{text}"
