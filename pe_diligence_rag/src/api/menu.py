"""
Menu State Machine for WhatsApp interactions.
Handles menu navigation and state for WhatsApp conversations.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class MenuState(Enum):
    """Menu states for conversation tracking."""
    MAIN = "main"
    AWAITING_TICKER = "awaiting_ticker"
    AWAITING_YEAR = "awaiting_year"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class ConversationState:
    """Tracks state for a single conversation."""
    phone_number: str
    state: MenuState = MenuState.MAIN
    last_option: Optional[str] = None
    last_ticker: Optional[str] = None
    last_year: Optional[int] = None
    error_count: int = 0


class MenuHandler:
    """
    Manages menu state for WhatsApp conversations.
    Supports multi-turn conversations where we ask for missing info.
    """

    def __init__(self):
        # Phone number -> ConversationState
        self._conversations: dict[str, ConversationState] = {}

    def get_state(self, phone_number: str) -> ConversationState:
        """Get or create conversation state."""
        if phone_number not in self._conversations:
            self._conversations[phone_number] = ConversationState(phone_number=phone_number)
        return self._conversations[phone_number]

    def reset(self, phone_number: str):
        """Reset conversation state."""
        self._conversations[phone_number] = ConversationState(phone_number=phone_number)

    def handle(self, phone_number: str, message: str) -> tuple[str, ConversationState]:
        """
        Handle incoming message and return (response_text, new_state).

        Args:
            phone_number: User's phone number
            message: User's message

        Returns:
            Tuple of (response_text, updated_state)
        """
        state = self.get_state(phone_number)
        message = message.strip()

        # Command to reset
        if message.upper() in ["/START", "/RESET", "/MENU"]:
            self.reset(phone_number)
            return self._get_main_menu(), state

        # Handle based on current state
        if state.state == MenuState.MAIN:
            return self._handle_main(phone_number, message, state)

        elif state.state == MenuState.AWAITING_TICKER:
            return self._handle_awaiting_ticker(phone_number, message, state)

        elif state.state == MenuState.AWAITING_YEAR:
            return self._handle_awaiting_year(phone_number, message, state)

        elif state.state == MenuState.PROCESSING:
            return "⏳ Please wait for the previous request to complete.", state

        elif state.state == MenuState.ERROR:
            if state.error_count >= 3:
                self.reset(phone_number)
                return "🔄 Resetting conversation. Send /menu to start over.", state
            state.error_count += 1
            return "⚠️ There was an error. Please try again or send /menu.", state

        return "Unknown state. Send /menu.", state

    def _handle_main(self, phone_number: str, message: str, state: ConversationState) -> tuple[str, ConversationState]:
        """Handle main menu input."""
        message_upper = message.upper()
        message_lower = message.lower()

        # Check for menu option
        if message_upper in ["1", "2", "3", "4", "5"]:
            state.last_option = message_upper
            # Parse ticker/year from message
            from ..retrieval.router import extract_ticker, extract_year

            ticker = extract_ticker(message)
            year = extract_year(message)

            if ticker:
                state.last_ticker = ticker
                if year:
                    state.last_year = year
                    return self._process_request(state)
                else:
                    state.state = MenuState.AWAITING_YEAR
                    return f"📅 Which year for {ticker}? (e.g., 2024 or 'latest')", state
            else:
                state.state = MenuState.AWAITING_TICKER
                return "🏢 Which company? (Enter ticker symbol, e.g., AAPL)", state

        # Free text query
        elif len(message) > 5:
            state.state = MenuState.PROCESSING
            return "🔍 Processing your query...", state

        else:
            return self._get_main_menu(), state

    def _handle_awaiting_ticker(self, phone_number: str, message: str, state: ConversationState) -> tuple[str, ConversationState]:
        """Handle state where we're waiting for a ticker."""
        from ..retrieval.router import extract_ticker

        ticker = extract_ticker(message)

        if ticker:
            state.last_ticker = ticker
            state.state = MenuState.AWAITING_YEAR
            return f"📅 Which year for {ticker}? (e.g., 2024 or 'latest')", state
        else:
            return "⚠️ Could not understand ticker. Please enter a valid ticker (e.g., AAPL, MSFT).", state

    def _handle_awaiting_year(self, phone_number: str, message: str, state: ConversationState) -> tuple[str, ConversationState]:
        """Handle state where we're waiting for a year."""
        from ..retrieval.router import extract_year

        year = extract_year(message)

        if year:
            state.last_year = year

        # Proceed with request
        return self._process_request(state)

    def _process_request(self, state: ConversationState) -> tuple[str, ConversationState]:
        """Process the request with collected parameters."""
        state.state = MenuState.PROCESSING

        # This would call the chain here
        # For now, return confirmation
        option_name = {
            "1": "Risk Discovery",
            "2": "Business Quality",
            "3": "Valuation Assumptions",
            "4": "Value Creation",
            "5": "Due Diligence Validation"
        }.get(state.last_option, "Analysis")

        ticker = state.last_ticker or "the company"
        year = state.last_year or "latest"

        return f"🔍 Running {option_name} for {ticker} ({year})...\n\nThis may take a moment.", state

    def _get_main_menu(self) -> str:
        """Return the main menu text."""
        return """
📊 PE DUE DILIGENCE RAG

Select an option (1-5):

1️⃣ Risk Discovery
2️⃣ Business Quality
3️⃣ Valuation Assumptions
4️⃣ Value Creation
5️⃣ Due Diligence Validation

Or type your question directly!
"""


# Singleton instance
menu_handler = MenuHandler()
