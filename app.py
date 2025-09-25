"""Streamlit application entry point."""

import streamlit as st

from agents.bedrock_agent import BedrockAgent
from handlers.ui_handlers import (
    parse_model_response,
    render_chain_of_thought,
    render_tool_calls,
)


def display_assistant_message(content):
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

    text, chain_of_thought = parse_model_response(str(content))
    if chain_of_thought:
        render_chain_of_thought(chain_of_thought)
    if text:
        st.markdown(text)
    elif not chain_of_thought:
        st.markdown("*Response is empty.*")


def run_app() -> None:
    """Render the Streamlit chat interface."""

    # Configure Streamlit page
    st.set_page_config(
        page_title="Bedrock Agent Chat",
        page_icon="🤖",
        layout="wide",
    )

    st.title("🤖 Amazon Bedrock Agent Chat")

    # Initialize session state
    if "agent" not in st.session_state:
        st.session_state.agent = BedrockAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Replay previous conversation so the UI stays in sync
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                display_assistant_message(message["content"])

    # Handle a new user message
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Create dedicated placeholders inside a single container
            message_container = st.container()
            status_placeholder = message_container.empty()
            tool_placeholder = message_container.empty()
            chain_placeholder = message_container.empty()
            response_placeholder = message_container.empty()

            # Provide placeholders to the UI handler
            ui_state = st.session_state.agent.get_ui_state()
            ui_state.reset()
            ui_state.message_container = message_container

            # Inject placeholders into the UI handler instance
            for handler in st.session_state.agent.event_registry._handlers:
                if hasattr(handler, "set_placeholders"):
                    handler.set_placeholders(
                        status_placeholder,
                        tool_placeholder,
                        chain_placeholder,
                        response_placeholder,
                    )
                    break

            try:
                # Stream events and process them on the main thread
                stream = st.session_state.agent.stream_response(prompt)
                for event in stream:
                    # Process events on the main thread to stay inside the Streamlit context
                    try:
                        results = st.session_state.agent.event_registry.process_event(event)

                        # Surface handler errors to the user, but keep streaming
                        for result in results:
                            if "handler_error" in result:
                                error_info = result["handler_error"]
                                status_placeholder.markdown(
                                    f":red[{error_info['handler']} error: {error_info['error_message']}]"
                                )

                    except Exception as handler_error:  # pragma: no cover - defensive
                        # Display the error but continue streaming
                        status_placeholder.markdown(f":red[Handler error: {handler_error}]")

                    # Stop streaming once the agent reports completion
                    if event.get("result") or event.get("force_stop"):
                        break

                # Persist the final assistant message
                for handler in st.session_state.agent.event_registry._handlers:
                    if hasattr(handler, "finalize_response"):
                        assistant_message = handler.finalize_response()
                        st.session_state.messages.append(
                            {"role": "assistant", "content": assistant_message}
                        )
                        break

            except Exception as error:  # pragma: no cover - runtime safety
                # Render an error message when streaming fails
                status_placeholder.empty()
                error_message = f"Error: {error}"
                response_placeholder.markdown(f":red[{error_message}]")
                chain_placeholder.empty()

                assistant_message = {
                    "text": error_message,
                    "chain_of_thought": None,
                    "tool_calls": [],
                }
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_message}
                )


if __name__ == "__main__":  # pragma: no cover - manual execution
    run_app()
