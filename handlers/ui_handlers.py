"""Streamlit UI event handler orchestrating domain-specific managers."""

from __future__ import annotations

from typing import Any, Dict, Iterable

import streamlit as st

from .event_handlers import EventHandler, EventType
from .ui import (
    MessageUIManager,
    ReasoningUIManager,
    StreamlitUIState,
    ToolUIManager,
    render_chain_of_thought,
    render_tool_calls,
    utils,
)


__all__ = [
    'StreamlitUIHandler',
    'StreamlitUIState',
    'render_chain_of_thought',
    'render_tool_calls',
    'parse_model_response',
    'strip_partial_thinking',
    'normalize_tool_value',
    'render_tool_value',
]

# Re-export the utility helpers for backwards compatibility -----------------
parse_model_response = utils.parse_model_response
strip_partial_thinking = utils.strip_partial_thinking
normalize_tool_value = utils.normalize_tool_value
render_tool_value = utils.render_tool_value


class StreamlitUIHandler(EventHandler):
    """Coordinate specialised UI managers in response to streaming events."""

    def __init__(self, ui_state: StreamlitUIState):
        self.ui_state = ui_state
        self.reasoning_manager = ReasoningUIManager(ui_state)
        self.tool_manager = ToolUIManager(ui_state)
        self.message_manager = MessageUIManager(ui_state)
        self._managers = (
            self.reasoning_manager,
            self.tool_manager,
            self.message_manager,
        )

    # ------------------------------------------------------------------
    def set_placeholders(self, status_placeholder, tool_placeholder, chain_placeholder, response_placeholder):
        """Attach Streamlit placeholders for progressive rendering."""
        self.ui_state.status_placeholder = status_placeholder
        self.ui_state.tool_placeholder = tool_placeholder
        self.ui_state.chain_placeholder = chain_placeholder
        self.ui_state.response_placeholder = response_placeholder

    @property
    def priority(self) -> int:
        return 10

    def can_handle(self, event_type: str) -> bool:
        ui_events = {
            "reasoningText",
            "current_tool_use",
            "tool_result",
            "data",
            "result",
            "force_stop",
            "event",
        }
        return event_type in ui_events

    # ------------------------------------------------------------------
    def handle(self, event: Dict[str, Any]) -> None:
        for manager in self._managers:
            if manager.can_handle(event):
                manager.handle(event)

        if event.get("force_stop"):
            self.reasoning_manager.mark_force_stop()
            self.tool_manager.mark_force_stop()

    # ------------------------------------------------------------------
    def finalize_response(self) -> Dict[str, Any]:
        result = self.message_manager.finalize()
        assistant_message = result["assistant_message"]
        display_text = result.get("display_text", "")
        chain_of_thought = result.get("chain_of_thought")
        final_container = result.get("final_container")
        force_stop = result.get("force_stop", False)

        tool_calls = assistant_message.get("tool_calls") or []

        self.tool_manager.finalize()

        render_parent = final_container
        if render_parent is None and self.ui_state.message_container:
            render_parent = self.ui_state.message_container.empty()

        if render_parent is not None:
            with render_parent:
                if tool_calls:
                    render_tool_calls(tool_calls)
                if chain_of_thought:
                    render_chain_of_thought(chain_of_thought)
                if display_text:
                    if force_stop:
                        st.markdown(f":red[{display_text}]")
                    else:
                        st.markdown(display_text)
        else:
            if tool_calls:
                render_tool_calls(tool_calls)
            if chain_of_thought:
                render_chain_of_thought(chain_of_thought)
            if display_text:
                if force_stop:
                    self.message_manager.render_force_stop_message(None)
                else:
                    self.message_manager.render_final_text(display_text, None)

        self.reasoning_manager.finalize(chain_of_thought)

        return assistant_message
