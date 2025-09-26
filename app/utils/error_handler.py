"""Error handling utilities for Streamlit."""

from typing import Any, Dict, List
import streamlit as st


class ErrorHandler:
    """Handle and display errors in the Streamlit interface."""

    @staticmethod
    def handle_streaming_error(error: Exception, status_placeholder, response_placeholder,
                             chain_placeholder) -> Dict[str, Any]:
        """Handle streaming errors and return error message for session."""
        # Clear other placeholders and show error
        status_placeholder.empty()
        chain_placeholder.empty()

        error_message = f"Error: {error}"
        response_placeholder.markdown(f":red[{error_message}]")

        # Return assistant message format for session storage
        return {
            "text": error_message,
            "chain_of_thought": None,
            "tool_calls": [],
        }

    @staticmethod
    def handle_handler_errors(results: List[Dict[str, Any]], status_placeholder) -> None:
        """Handle handler errors during event processing."""
        for result in results:
            if "handler_error" in result:
                error_info = result["handler_error"]
                status_placeholder.markdown(
                    f":red[{error_info['handler']} error: {error_info['error_message']}]"
                )

    @staticmethod
    def display_handler_error(handler_error: Exception, status_placeholder) -> None:
        """Display a general handler error."""
        status_placeholder.markdown(f":red[Handler error: {handler_error}]")