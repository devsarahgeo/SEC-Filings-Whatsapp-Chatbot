"""
Master Chain and Router.
LangChain LCEL chain that routes queries to the appropriate specialized chain.
"""

import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda
from ..config.settings import GROQ_API_KEY, MODEL_NAME
from ..config.prompts import MASTER_PROMPT, RISK_PROMPT, FINANCIALS_PROMPT, VALUATION_PROMPT, VALUE_CREATION_PROMPT, DILIGENCE_PROMPT
from ..retrieval.retriever import SECRetriever
from ..retrieval.router import parse_query


# LLM (Groq - free)
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
    temperature=0.3
)


def create_master_chain():
    """
    Create the master routing chain using LCEL.
    Routes to specialized chains based on query content.
    """
    from .risk_chain import create_risk_chain
    from .financials_chain import create_financials_chain
    from .valuation_chain import create_valuation_chain
    from .value_chain import create_value_chain
    from .diligence_chain import create_diligence_chain

    retriever = SECRetriever()

    # Create specialized chains
    risk_chain = create_risk_chain(retriever)
    financials_chain = create_financials_chain(retriever)
    valuation_chain = create_valuation_chain(retriever)
    value_chain = create_value_chain(retriever)
    diligence_chain = create_diligence_chain(retriever)

    # Master routing prompt
    master_prompt = PromptTemplate.from_template(MASTER_PROMPT)

    # Router that classifies the query
    def route_query(inputs):
        query = inputs.get("query", "")
        parsed = parse_query(query)

        intent = parsed["intent"].lower()
        ticker = parsed["ticker"]
        year = parsed.get("year")

        if "risk" in intent.lower():
            return "risk"
        elif "financial" in intent.lower():
            return "financials"
        elif "valuation" in intent.lower():
            return "valuation"
        elif "value" in intent.lower():
            return "value"
        elif "diligence" in intent.lower():
            return "diligence"
        else:
            return "risk"

    # LCEL RunnableBranch for routing
    branch = RunnableBranch(
        (lambda x: route_query(x) == "risk", risk_chain),
        (lambda x: route_query(x) == "financials", financials_chain),
        (lambda x: route_query(x) == "valuation", valuation_chain),
        (lambda x: route_query(x) == "value", value_chain),
        (lambda x: route_query(x) == "diligence", diligence_chain),
        risk_chain  # Default
    )

    return branch


def run_master(query: str) -> str:
    """
    Run the master chain on a query.
    Automatically routes to the correct chain.
    """
    chain = create_master_chain()

    # Parse query
    parsed = parse_query(query)

    # Prepare input
    inputs = {
        "query": query,
        "ticker": parsed["ticker"],
        "year": parsed.get("year") or "recent",
        "year_range": parsed.get("year_range", "recent 3 years"),
        "context": ""
    }

    result = chain.invoke(inputs)

    return result


def route_and_run(query: str, option: str = None) -> dict:
    """
    Parse query, route to correct chain, return result.
    """
    from ..retrieval.router import parse_query

    # Parse the query
    parsed = parse_query(query, option)

    # Import chains
    from .risk_chain import create_risk_chain
    from .financials_chain import create_financials_chain
    from .valuation_chain import create_valuation_chain
    from .value_chain import create_value_chain
    from .diligence_chain import create_diligence_chain

    retriever = SECRetriever()

    # Create correct chain
    chain_map = {
        "1": create_risk_chain,
        "2": create_financials_chain,
        "3": create_valuation_chain,
        "4": create_value_chain,
        "5": create_diligence_chain
    }

    chain_fn = chain_map.get(parsed["option"], create_risk_chain)
    chain = chain_fn(retriever)

    try:
        # Prepare input string for the chain
        input_str = f"Ticker: {parsed.get('ticker', 'UNKNOWN')}\n\nQuestion: {query}"

        # Run - chains now return strings directly with StrOutputParser
        result = chain.invoke(input_str)

        return {
            "result": result,  # result is already a string from StrOutputParser
            "ticker": parsed["ticker"],
            "year": parsed.get("year"),
            "intent": parsed["intent"],
            "option": parsed["option"]
        }
    except Exception as e:
        print(f"❌ Error in route_and_run: {e}")
        import traceback
        traceback.print_exc()
        return {
            "result": f"Error: {str(e)}",
            "ticker": parsed.get("ticker", "UNKNOWN"),
            "year": parsed.get("year"),
            "intent": parsed.get("intent", "unknown"),
            "option": parsed.get("option", "1")
        }
