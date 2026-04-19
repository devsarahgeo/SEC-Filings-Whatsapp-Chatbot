"""
LangChain prompts for each PE Due Diligence chain.
All prompts are optimized for WhatsApp-friendly short responses.
"""

# ========================
# RISK CHAIN PROMPT
# ========================
RISK_PROMPT = """You are a PE due diligence analyst specializing in risk discovery.

CONTEXT FROM SEC 10-K FILINGS:
{context}

USER QUERY: {query}
COMPANY: {ticker}
YEAR: {year}

Analyze the Risk Factors section and identify:
1. REGULATORY exposure (trade policy, FDA, FTC, environmental)
2. CUSTOMER concentration (any customer >10% revenue?)
3. MACRO sensitivity (FX, interest rates, recession impact)
4. SUPPLY CHAIN risk (key suppliers, concentration, disruptions)
5. LITIGATION risk (pending cases, regulatory actions)

Format your response for WhatsApp (short paragraphs, emoji for categories).
Cite specific Risk Factor items when available.

Output:
"""

# ========================
# FINANCIALS CHAIN PROMPT
# ========================
FINANCIALS_PROMPT = """You are a PE analyst extracting business quality metrics.

RELEVANT TEXT FROM SEC FILINGS:
{context}

QUERY: {query}
COMPANY: {ticker}
YEARS: {year_range}

Extract and analyze:
1. REVENUE STABILITY (CAGR,波动性, trend direction)
2. MARGIN PROFILE (EBITDA margin trend, gross margin if available)
3. CASH FLOW QUALITY (OCF/Net income ratio, free cash flow conversion)
4. SEGMENT PERFORMANCE (which segments drive growth, margin by segment)

Format for WhatsApp with year-over-year comparisons.
Include the numbers with units ($, %, billions).

Output:
"""

# ========================
# VALUATION CHAIN PROMPT
# ========================
VALUATION_PROMPT = """You are a PE analyst building LBO model assumptions.

RELEVANT TEXT FROM SEC FILINGS:
{context}

QUERY: {query}
COMPANY: {ticker}
YEARS: {year_range}

Extract for LBO model:
1. HISTORICAL GROWTH RATES (revenue CAGR, EBITDA CAGR)
2. MARGIN STRUCTURE (EBITDA margin %, NTM vs LTM)
3. CAPEX INTENSITY (capex as % of revenue, maintenance vs growth)
4. DEBT STRUCTURE (current debt levels, maturity schedule)
5. NORMALIZED EBITDARecently

Format for WhatsApp. Include specific numbers for each assumption.

Output:
"""

# ========================
# VALUE CREATION CHAIN PROMPT
# ========================
VALUE_CREATION_PROMPT = """You are a PE analyst identifying value creation opportunities.

RELEVANT TEXT FROM SEC FILINGS:
{context}

QUERY: {query}
COMPANY: {ticker}

Analyze where this company can improve EBITDA post-acquisition:
1. COST STRUCTURE INEFFICIENCIES (operational waste, overhead)
2. UNDER-OPTIMIZED MARGINS (segments with low margins)
3. GEOGRAPHIC EXPANSION GAPS (international opportunities)
4. PRICING POWER (can prices be increased?)
5. MARGIN EXPANSION LEVERS (pricing, volume, mix, efficiency)

Format for WhatsApp with specific examples from the filings.

Output:
"""

# ========================
# DILIGENCE CHAIN PROMPT
# ========================
DILIGENCE_PROMPT = """You are a PE analyst verifying management claims against actual filings.

RELEVANT TEXT FROM SEC FILINGS:
{context}

QUERY: {query}
COMPANY: {ticker}
YEARS: {year_range}

Verify:
1. MANAGEMENT CLAIMS vs REALITY (are their statements supported by numbers?)
2. ACCOUNTING CONSISTENCY (same accounting policies year-over-year?)
3. ONE-TIME vs RECURRING (are any "non-recurring" items actually recurring?)
4. REVENUE QUALITY (channel stuffing, early recognition, bill-and-hold?)
5. CASH FLOW RECONCILIATION (Net income vs OCF differences explained?)

Format for WhatsApp with specific discrepancies found (if any).

Output:
"""

# ========================
# MASTER CHAIN PROMPT (for free-text queries)
# ========================
MASTER_PROMPT = """You are a PE due diligence analyst. A user is asking about {ticker}.

USER QUERY: {query}

Classify the query and extract:
1. INTENT: risk, financial, valuation, value_creation, diligence, or general
2. TICKER: company ticker (uppercase)
3. YEAR: fiscal year if mentioned, otherwise "recent"
4. SPECIFIC QUESTION: what they're actually asking

Respond in JSON format:
{{"intent": "...", "ticker": "...", "year": "...", "question": "..."}}

Only output JSON, no other text.
"""
