"""Reasoning-specific rendering for the Streamlit UI."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from .state import StreamlitUIState


class ReasoningUIManager:
    """Render reasoning updates and final content for the agent."""

    def __init__(self, ui_state: StreamlitUIState):
        self.ui_state = ui_state

    # ------------------------------------------------------------------
    def can_handle(self, event: Dict[str, Any]) -> bool:
        return "reasoningText" in event or self._contains_reasoning_event(event)

    def handle(self, event: Dict[str, Any]) -> None:
        if "reasoningText" in event:
            self._handle_reasoning_text(event.get("reasoningText", ""))
        if "event" in event:
            self._handle_event(event.get("event", {}))

    # ------------------------------------------------------------------
    def finalize(self, chain_of_thought: str | None) -> None:
        reasoning_state = self.ui_state.reasoning
        status = reasoning_state.status
        if status:
            if reasoning_state.text or chain_of_thought:
                status.update(
                    label="✅ Reasoning Complete",
                    state="complete",
                    expanded=False,
                )
            else:
                status.update(
                    label="No reasoning captured",
                    state="complete",
                    expanded=False,
                )

        placeholder = reasoning_state.content_placeholder
        if placeholder:
            placeholder.empty()
            with placeholder:
                if reasoning_state.text:
                    st.markdown(reasoning_state.text)
                if chain_of_thought:
                    st.markdown(chain_of_thought)

    def mark_force_stop(self) -> None:
        status = self.ui_state.reasoning.status
        if status:
            status.update(
                label="❌ Reasoning aborted",
                state="error",
                expanded=False,
            )

    # ------------------------------------------------------------------
    def _handle_reasoning_text(self, reasoning_content: str) -> None:
        if not reasoning_content:
            return

        self._ensure_reasoning_status()
        self.ui_state.reasoning.text += reasoning_content

        status = self.ui_state.reasoning.status
        if status:
            status.update(
                label="🧠 Reasoning in progress…",
                state="running",
                expanded=True,
            )

    def _handle_event(self, event_data: Dict[str, Any]) -> None:
        if "contentBlockDelta" not in event_data:
            return

        delta = event_data["contentBlockDelta"].get("delta", {})
        if "SDK_UNKNOWN_MEMBER" not in delta:
            return

        unknown_member = delta["SDK_UNKNOWN_MEMBER"]
        if unknown_member.get("name") == "reasoningContent":
            self._ensure_reasoning_status()

    def _ensure_reasoning_status(self) -> None:
        if self.ui_state.reasoning.expander:
            return

        parent = self.ui_state.chain_placeholder or self.ui_state.status_placeholder
        if not parent:
            return

        with parent.container():
            expander = st.expander("🧠 Reasoning", expanded=False)
            with expander:
                status = st.status("🧠 Reasoning in progress…", expanded=False)
                content_placeholder = st.empty()

        reasoning_state = self.ui_state.reasoning
        reasoning_state.expander = expander
        reasoning_state.status = status
        reasoning_state.content_placeholder = content_placeholder

    def _contains_reasoning_event(self, event: Dict[str, Any]) -> bool:
        if "event" not in event:
            return False
        event_data = event["event"]
        if "contentBlockDelta" not in event_data:
            return False
        delta = event_data["contentBlockDelta"].get("delta", {})
        unknown_member = delta.get("SDK_UNKNOWN_MEMBER")
        if not isinstance(unknown_member, dict):
            return False
        return unknown_member.get("name") == "reasoningContent"
