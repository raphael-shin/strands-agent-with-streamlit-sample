"""Placeholder management for Streamlit UI."""

from typing import Tuple, Any
import streamlit as st


class PlaceholderManager:
    """Manage Streamlit placeholders for the chat interface."""

    @staticmethod
    def create_chat_placeholders(message_container) -> Tuple[Any, Any, Any, Any]:
        """Create dedicated placeholders inside a single container."""
        status_placeholder = message_container.empty()
        tool_placeholder = message_container.empty()
        chain_placeholder = message_container.empty()
        response_placeholder = message_container.empty()

        return status_placeholder, tool_placeholder, chain_placeholder, response_placeholder

    @staticmethod
    def setup_ui_handler_placeholders(agent, status_ph, tool_ph, chain_ph, response_ph) -> None:
        """Inject placeholders into the UI handler instance."""
        for handler in agent.event_registry._handlers:
            if hasattr(handler, "set_placeholders"):
                handler.set_placeholders(
                    status_ph,
                    tool_ph,
                    chain_ph,
                    response_ph,
                )
                break