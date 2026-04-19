"""
Valuation Chain.
LangChain RetrievalQA chain for LBO model assumptions and valuation inputs.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from ..config.settings import GROQ_API_KEY, MODEL_NAME
from ..config.prompts import VALUATION_PROMPT
from ..retrieval.retriever import SECRetriever


def create_valuation_chain(retriever: SECRetriever = None):
    """Create the Valuation Assumptions chain using modern LCEL."""

    # LLM (Groq - free)
    llm = ChatOpenAI(
        model=MODEL_NAME,
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        temperature=0.2
    )

    # Prompt with explicit input variables
    prompt = PromptTemplate(
        input_variables=["context", "query", "ticker", "year_range"],
        template=VALUATION_PROMPT
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


def run_valuation_analysis(query: str, ticker: str, year_range: str = None) -> str:
    """Run valuation assumptions analysis."""
    chain = create_valuation_chain()

    # Construct the full query with context
    full_query = f"""
Ticker: {ticker.upper()}
Time Period: {year_range or "recent 3 years"}

Question: {query}
"""

    result = chain.invoke(full_query)
    return result


def get_lbo_assumptions(ticker: str, years: int = 3) -> str:
    """Convenience function for LBO model assumptions."""
    retriever = SECRetriever()
    chain = create_valuation_chain(retriever)

    query = f"""
Ticker: {ticker.upper()}
Time Period: Last {years} years

Question: Extract LBO model assumptions for {ticker}:
- Historical growth rates
- EBITDA margins
- Capex intensity
- Debt structure
"""

    result = chain.invoke(query)
    return result
