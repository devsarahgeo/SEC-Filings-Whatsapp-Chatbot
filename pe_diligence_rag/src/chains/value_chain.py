"""
Value Creation Chain.
LangChain RetrievalQA chain for identifying margin improvement opportunities.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from ..config.settings import GROQ_API_KEY, MODEL_NAME
from ..config.prompts import VALUE_CREATION_PROMPT
from ..retrieval.retriever import SECRetriever


def create_value_chain(retriever: SECRetriever = None):
    """Create the Value Creation Opportunities chain using modern LCEL."""

    # LLM (Groq - free)
    llm = ChatOpenAI(
        model=MODEL_NAME,
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
        temperature=0.4  # Slightly higher for creative analysis
    )

    # Prompt with explicit input variables
    prompt = PromptTemplate(
        input_variables=["context", "query", "ticker"],
        template=VALUE_CREATION_PROMPT
    )

    # Create retriever if not provided
    if retriever is None:
        retriever = SECRetriever()

    # Helper to parse input and retrieve context
    def prepare_input(query: str) -> dict:
        """Parse query and retrieve context."""
        try:
            # Simple extraction
            ticker = "UNKNOWN"
            if "Ticker:" in query:
                ticker = query.split("Ticker:")[1].split("\n")[0].strip()
            
            # Retrieve context
            docs = retriever.retrieve(query, ticker=ticker if ticker != "UNKNOWN" else None)
            context = "\n".join([doc.page_content for doc in docs]) if docs else "No relevant documents found."
            
            return {
                "context": context,
                "query": query,
                "ticker": ticker
            }
        except Exception as e:
            print(f"❌ prepare_input error: {e}")
            return {
                "context": "Error retrieving documents.",
                "query": query,
                "ticker": "UNKNOWN"
            }

    # Modern LCEL chain
    chain = (
        RunnableLambda(prepare_input)
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def run_value_analysis(query: str, ticker: str) -> str:
    """Run value creation analysis."""
    try:
        chain = create_value_chain()
        full_query = f"Ticker: {ticker.upper()}\n\nQuestion: {query}"
        print(f"🔄 Running value analysis...")
        result = chain.invoke(full_query)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


def find_value_opportunities(ticker: str) -> str:
    """Convenience function for value creation analysis."""
    retriever = SECRetriever()
    chain = create_value_chain(retriever)

    query = f"""
Ticker: {ticker.upper()}

Question: Identify value creation opportunities for {ticker}:
- Cost inefficiencies
- Margin expansion levers
- Geographic gaps
- Pricing power
"""

    result = chain.invoke(query)
    return result
