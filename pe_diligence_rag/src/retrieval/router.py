"""
Query Router.
Routes user queries to the correct chain based on menu option or intent.
"""

import re
from typing import Optional, Tuple

from ..config.settings import MENU_OPTIONS


def extract_ticker(query: str) -> Optional[str]:
    """Extract ticker symbol from query."""
    # Common patterns:
    # "AAPL", "Apple", "for AAPL", "AAPL risk"
    patterns = [
        r'\b([A-Z]{1,5})\b',  # All caps 1-5 letters
        r'for\s+([A-Z]{1,5})\b',
        r'ticker\s+([A-Z]{1,5})\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, query.upper())
        if match:
            ticker = match.group(1)
            # Filter out common words
            if ticker not in ['FOR', 'AND', 'THE', 'RISK', 'BUSINESS', 'VALUE', 'YEAR', 'YEARS', 'MARGIN', 'GROWTH']:
                return ticker

    return None


def extract_year(query: str) -> Optional[int]:
    """Extract year from query."""
    patterns = [
        r'\b(20\d{2})\b',  # 2019, 2020, etc.
        r'\bFY(20\d{2})\b',  # FY2020
        r'\b(202[0-9]|201[0-9])\b',  # 2015-2029
    ]

    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            year = int(match.group(1))
            if 2000 <= year <= 2030:
                return year

    return None


def extract_year_range(query: str) -> str:
    """Extract year range for display."""
    year = extract_year(query)
    if year:
        return f"{year-2} - {year}"
    return "recent 3 years"


def route_by_option(option: str) -> dict:
    """
    Route by menu option (1-5).

    Returns:
        Dict with index, section, chain_name
    """
    return MENU_OPTIONS.get(option, MENU_OPTIONS["1"])


def route_by_query(query: str) -> str:
    """
    Auto-route based on query content.

    Returns:
        Menu option (1-5)
    """
    query_lower = query.lower()

    # Risk indicators
    risk_words = ['risk', 'risks', 'regulatory', 'litigation', 'lawsuit', 'compliance', 'lawsuit', 'exposure']
    if any(w in query_lower for w in risk_words):
        return "1"

    # Financial indicators
    financial_words = ['ebitda', 'revenue', 'margin', 'income', 'cash flow', 'profit', 'sales', 'eps']
    if any(w in query_lower for w in financial_words):
        return "2"

    # Valuation indicators
    valuation_words = ['valuation', 'lbo', 'multiple', 'irr', 'model', 'assumptions', 'growth rate']
    if any(w in query_lower for w in valuation_words):
        return "3"

    # Value creation indicators
    value_words = ['improve', 'optimize', 'efficiency', 'cost', 'margin expansion', 'opportunity']
    if any(w in query_lower for w in value_words):
        return "4"

    # Diligence indicators
    diligence_words = ['verify', 'consistent', 'claim', 'management', 'accounting', 'actual', 'real']
    if any(w in query_lower for w in diligence_words):
        return "5"

    # Default
    return "1"


def parse_query(query: str, option: Optional[str] = None) -> dict:
    """
    Parse a user query and extract components.

    Args:
        query: User's message
        option: Menu option if selected

    Returns:
        Dict with ticker, year, year_range, intent, option
    """
    ticker = extract_ticker(query)
    year = extract_year(query)
    year_range = extract_year_range(query)

    if option:
        intent = MENU_OPTIONS[option]["name"]
        route = MENU_OPTIONS[option]
    else:
        option = route_by_query(query)
        route = MENU_OPTIONS[option]
        intent = route["name"]

    return {
        "ticker": ticker or "THE_COMPANY",
        "year": year,
        "year_range": year_range,
        "intent": intent,
        "option": option,
        "section": route["section"],
        "index": route["index"]
    }
