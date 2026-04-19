"""
Financials Chain.
LangChain RetrievalQA chain for EBITDA, margins, revenue analysis.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from ..config.settings import GROQ_API_KEY, MODEL_NAME
from ..config.prompts import FINANCIALS_PROMPT
from ..retrieval.retriever import SECRetriever


def create_financials_chain(retriever: SECRetriever = None):
    """Create the Business Quality / Financials chain using modern LCEL."""

    # LLM (Groq - free)
    llm = ChatOpenAI(
        model=MODEL_NAME,
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        temperature=0.2  # Low temp for factual extraction
    )

    # Prompt with explicit input variables
    prompt = PromptTemplate(
        input_variables=["context", "query", "ticker", "year_range"],
        template=FINANCIALS_PROMPT
    )

    # Create retriever if not provided
    if retriever is None:
        retriever = SECRetriever()

    # Helper to parse input and retrieve context
    def prepare_input(query: str) -> dict:
        """Parse query and retrieve context."""
        try:
            ticker = "UNKNOWN"
            year_range = "recent"
            if "Ticker:" in query:
                ticker = query.split("Ticker:")[1].split("\n")[0].strip()
            
            docs = retriever.retrieve(query, ticker=ticker if ticker != "UNKNOWN" else None)
            context = "\n".join([doc.page_content for doc in docs]) if docs else "No relevant documents found."
            
            return {
                "context": context,
                "query": query,
                "ticker": ticker,
                "year_range": year_range
            }
        except Exception as e:
            print(f"❌ prepare_input error: {e}")
            return {
                "context": "Error retrieving documents.",
                "query": query,
                "ticker": "UNKNOWN",
                "year_range": "recent"
            }

    # Modern LCEL chain
    chain = (
        RunnableLambda(prepare_input)
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def run_financial_analysis(query: str, ticker: str, year: int = None, year_range: str = None) -> str:
    """Run financial analysis for a company."""
    chain = create_financials_chain()

    # Construct the full query with context
    full_query = f"""
Ticker: {ticker.upper()}
Time Period: {year_range or "recent years"}

Question: {query}
"""

    result = chain.invoke(full_query)
    return result


def analyze_business_quality(ticker: str, years: int = 3) -> str:
    """Convenience function for business quality analysis."""
    retriever = SECRetriever()
    chain = create_financials_chain(retriever)

    query = f"""
Ticker: {ticker.upper()}
Time Period: Last {years} years

Question: Analyze business quality for {ticker}:
- Revenue stability
- EBITDA trends
- Cash flow quality
- Segment performance
"""

    result = chain.invoke(query)
    return result
