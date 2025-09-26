"""Streamlit session state management."""

from typing import List, Dict, Any, Optional
import streamlit as st

from agents.strands_agent import StrandsAgent


class SessionManager:
    """Manage Streamlit session state for the chat application."""

    def __init__(self):
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize session state if not already present."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "agent" not in st.session_state:
            st.session_state.agent = None

        if "current_model" not in st.session_state:
            st.session_state.current_model = None

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Get the chat messages from session state."""
        return st.session_state.messages

    @property
    def agent(self) -> Optional[StrandsAgent]:
        """Get the current agent from session state."""
        return st.session_state.agent

    @property
    def current_model(self) -> Optional[str]:
        """Get the current model from session state."""
        return st.session_state.current_model

    def add_message(self, role: str, content: Any) -> None:
        """Add a message to the chat history."""
        st.session_state.messages.append({"role": role, "content": content})

    def handle_model_change(self, selected_model: str) -> bool:
        """Handle model selection changes. Returns True if model was changed."""
        # First time initialization
        if st.session_state.current_model is None:
            st.session_state.current_model = selected_model
            st.session_state.agent = StrandsAgent(model_id=selected_model)
            return True

        # Model changed - reset session
        if st.session_state.current_model != selected_model:
            st.session_state.current_model = selected_model
            st.session_state.agent = StrandsAgent(model_id=selected_model)
            st.session_state.messages = []
            st.rerun()
            return True

        return False

    def get_agent_ui_state(self):
        """Get the UI state from the current agent."""
        if self.agent:
            return self.agent.get_ui_state()
        return None

    def clear_messages(self) -> None:
        """Clear all chat messages."""
        st.session_state.messages = []