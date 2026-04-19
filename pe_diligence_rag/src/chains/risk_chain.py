"""
Risk Discovery Chain.
LangChain RetrievalQA chain for SEC Risk Factors analysis.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from ..config.settings import GROQ_API_KEY, MODEL_NAME, RETRIEVAL_K
from ..config.prompts import RISK_PROMPT
from ..retrieval.retriever import SECRetriever


def create_risk_chain(retriever: SECRetriever = None):
    """Create the Risk Discovery chain using modern LCEL."""

    # LLM (Groq - free)
    llm = ChatOpenAI(
        model=MODEL_NAME,
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        temperature=0.3  # Lower temp for factual analysis
    )

    # Prompt with explicit input variables
    prompt = PromptTemplate(
        input_variables=["context", "query", "ticker", "year"],
        template=RISK_PROMPT
    )

    # Create retriever if not provided
    if retriever is None:
        retriever = SECRetriever()

    # Helper to parse input and retrieve context
    def prepare_input(query: str) -> dict:
        """Parse query and retrieve context."""
        try:
            ticker = "UNKNOWN"
            year = "recent"
            if "Ticker:" in query:
                ticker = query.split("Ticker:")[1].split("\n")[0].strip()
            
            docs = retriever.retrieve(query, ticker=ticker if ticker != "UNKNOWN" else None)
            context = "\n".join([doc.page_content for doc in docs]) if docs else "No relevant documents found."
            
            return {
                "context": context,
                "query": query,
                "ticker": ticker,
                "year": year
            }
        except Exception as e:
            print(f"❌ prepare_input error: {e}")
            return {
                "context": "Error retrieving documents.",
                "query": query,
                "ticker": "UNKNOWN",
                "year": "recent"
            }

    # Modern LCEL chain
    chain = (
        RunnableLambda(prepare_input)
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def run_risk_analysis(
    query: str,
    ticker: str,
    year: int = None,
    ticker_alt: str = None  # For comparison queries like "AAPL vs MSFT"
) -> str:
    """
    Run risk analysis for a company.

    Args:
        query: User's question
        ticker: Company ticker
        year: Fiscal year (optional)
        ticker_alt: Second ticker for comparison

    Returns:
        Analysis result
    """
    chain = create_risk_chain()

    if ticker_alt:
        # Comparison query
        query = f"Compare risk profiles of {ticker} and {ticker_alt}"

    # Construct the full query with context
    full_query = f"""
Ticker: {ticker.upper()}
Year: {year or "recent"}

Question: {query}
"""

    result = chain.invoke(full_query)
    return result


# Standalone function
def analyze_risks(ticker: str, year: int = None, query: str = None) -> str:
    """Convenience function to analyze risks."""
    from ..retrieval.retriever import SECRetriever

    retriever = SECRetriever()
    chain = create_risk_chain(retriever)

    default_query = f"What are the key risk factors for {ticker}?"
    full_query = f"""
Ticker: {ticker.upper()}
Year: {year or "recent"}

Question: {query or default_query}
"""

    result = chain.invoke(full_query)
    return result
