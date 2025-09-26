"""Message rendering utilities for Streamlit."""

from typing import Any
import streamlit as st

from handlers.ui_handlers import (
    parse_model_response,
    render_chain_of_thought,
    render_tool_calls,
)


class MessageRenderer:
    """Handle rendering of assistant messages in Streamlit."""

    @staticmethod
    def render_assistant_message(content: Any) -> None:
        """Render the assistant message using the helper utilities."""
        if isinstance(content, dict) and "text" in content:
            text = content.get("text", "")
            tool_calls = content.get("tool_calls") or []
            chain_of_thought = content.get("chain_of_thought")

            if tool_calls:
                render_tool_calls(tool_calls)
            if chain_of_thought:
                render_chain_of_thought(chain_of_thought)
            if text:
                st.markdown(text)
            elif not tool_calls and not chain_of_thought:
                st.markdown("*Response is empty.*")
            return

        # Fallback for string content
        text, chain_of_thought = parse_model_response(str(content))
        if chain_of_thought:
            render_chain_of_thought(chain_of_thought)
        if text:
            st.markdown(text)
        elif not chain_of_thought:
            st.markdown("*Response is empty.*")