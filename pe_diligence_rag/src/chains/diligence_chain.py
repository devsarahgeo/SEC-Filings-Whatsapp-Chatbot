"""
Due Diligence Validation Chain.
LangChain RetrievalQA chain for verifying management claims vs actuals.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from ..config.settings import GROQ_API_KEY, MODEL_NAME
from ..config.prompts import DILIGENCE_PROMPT
from ..retrieval.retriever import SECRetriever


def create_diligence_chain(retriever: SECRetriever = None):
    """Create the Due Diligence Validation chain using modern LCEL."""

    # LLM (Groq - free)
    llm = ChatOpenAI(
        model=MODEL_NAME,
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        temperature=0.1  # Very low temp for critical analysis
    )

    # Prompt with explicit input variables
    prompt = PromptTemplate(
        input_variables=["context", "query", "ticker", "year_range"],
        template=DILIGENCE_PROMPT
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


def run_diligence_analysis(query: str, ticker: str, year_range: str = None) -> str:
    """Run due diligence validation."""
    chain = create_diligence_chain()

    # Construct the full query with context
    full_query = f"""
Ticker: {ticker.upper()}
Time Period: {year_range or "recent 3 years"}

Question: {query}
"""

    result = chain.invoke(full_query)
    return result


def validate_claims(ticker: str, years: int = 3) -> str:
    """Convenience function for claim validation."""
    retriever = SECRetriever()
    chain = create_diligence_chain(retriever)

    query = f"""
Ticker: {ticker.upper()}
Time Period: Last {years} years

Question: Verify management claims for {ticker}: 
- Accounting consistency
- One-time vs recurring items  
- Revenue quality
"""

    result = chain.invoke(query)
    return result
