"""Streaming and final response rendering for the Streamlit UI."""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from . import utils
from .placeholders import safe_markdown
from .state import StreamlitUIState




def render_chain_of_thought(chain_of_thought: Optional[str]) -> None:
    """Render the optional chain-of-thought inside an expander."""
    if not chain_of_thought:
        return
    with st.expander("🤔 Chain of Thought", expanded=False):
        st.markdown(chain_of_thought)


class MessageUIManager:
    """Handle token streaming, final results, and error reporting."""

    def __init__(self, ui_state: StreamlitUIState):
        self.ui_state = ui_state

    # ------------------------------------------------------------------
    def can_handle(self, event: Dict[str, Any]) -> bool:
        return any(key in event for key in ("data", "result", "force_stop"))

    def handle(self, event: Dict[str, Any]) -> None:
        if "data" in event:
            self._handle_data(event.get("data", ""))
        if "result" in event:
            self._handle_result(event.get("result"))
        if event.get("force_stop"):
            reason = event.get("force_stop_reason", "Unknown error")
            self.handle_force_stop(reason)

    # ------------------------------------------------------------------
    def finalize(self) -> Dict[str, Any]:
        message_state = self.ui_state.message
        assistant_message = self.ui_state.assistant_message

        final_container = None
        if self.ui_state.message_container:
            final_container = self.ui_state.message_container.empty()

        if message_state.force_stop_error:
            assistant_message["text"] = message_state.force_stop_error
            assistant_message["chain_of_thought"] = None
            return {
                "assistant_message": assistant_message,
                "display_text": message_state.force_stop_error,
                "chain_of_thought": None,
                "final_container": final_container,
                "force_stop": True,
            }

        if not message_state.raw_response and message_state.final_message:
            message_state.raw_response = self._extract_text_from_message(message_state.final_message)

        final_text, chain_of_thought = utils.parse_model_response(message_state.raw_response)
        display_text = final_text or "*Computation completed.*"

        assistant_message["text"] = display_text
        assistant_message["chain_of_thought"] = chain_of_thought

        return {
            "assistant_message": assistant_message,
            "display_text": display_text,
            "chain_of_thought": chain_of_thought,
            "final_container": final_container,
            "force_stop": False,
        }

    def render_final_text(self, text: str, final_container: Optional[Any]) -> None:
        self._render_final_text(text, final_container)

    def handle_force_stop(self, reason: str) -> None:
        self.ui_state.message.force_stop_error = f"Error: {reason}"
        safe_markdown(self.ui_state.response_placeholder, f":red[{self.ui_state.message.force_stop_error}]")

    def render_force_stop_message(self, final_container: Optional[Any]) -> None:
        self._render_force_stop(final_container)

    # ------------------------------------------------------------------
    def _handle_data(self, data_chunk: str) -> None:
        placeholder = self.ui_state.response_placeholder
        if not data_chunk or not placeholder:
            return

        self.ui_state.message.raw_response += data_chunk
        partial_text = utils.strip_partial_thinking(self.ui_state.message.raw_response)
        if partial_text:
            placeholder.markdown(f"{partial_text}▌")
        else:
            placeholder.markdown("▌")

    def _handle_result(self, agent_result: Any) -> None:
        if hasattr(agent_result, "message") and agent_result.message:
            self.ui_state.message.final_message = agent_result.message
        elif isinstance(agent_result, dict):
            self.ui_state.message.final_message = agent_result.get("message")

        if agent_result:
            self._backfill_tool_inputs_from_metrics(agent_result)

    def _render_force_stop(self, final_container: Optional[Any]) -> None:
        error_text = f":red[{self.ui_state.message.force_stop_error}]"
        if final_container is not None:
            with final_container:
                st.markdown(error_text)
        else:
            safe_markdown(self.ui_state.response_placeholder, error_text)

    def _render_final_text(self, text: str, final_container: Optional[Any]) -> None:
        if final_container is not None:
            with final_container:
                st.markdown(text)
        else:
            safe_markdown(self.ui_state.response_placeholder, text)

    def _extract_text_from_message(self, message: Any) -> str:
        if not message:
            return ""
        if isinstance(message, str):
            return message

        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            for item in content:
                text = item.get("text")
                if text:
                    return text
        if isinstance(content, str):
            return content
        return ""

    # ------------------------------------------------------------------
    def _backfill_tool_inputs_from_metrics(self, agent_result: Any) -> bool:
        metrics = getattr(agent_result, "metrics", None)
        if metrics is None and isinstance(agent_result, dict):
            metrics = agent_result.get("metrics")
        if not metrics:
            return False

        tool_metrics = getattr(metrics, "tool_metrics", None)
        if tool_metrics is None and isinstance(metrics, dict):
            tool_metrics = metrics.get("tool_metrics")
        if not tool_metrics:
            return False

        metric_entries = tool_metrics.values() if isinstance(tool_metrics, dict) else tool_metrics
        updated = False

        for metric in metric_entries:
            tool_info = getattr(metric, "tool", None)
            if tool_info is None and isinstance(metric, dict):
                tool_info = metric.get("tool")
            if not tool_info:
                continue

            if isinstance(tool_info, dict):
                tool_id = tool_info.get("toolUseId") or tool_info.get("tool_use_id")
                raw_input = tool_info.get("input") or tool_info.get("arguments")
                name = tool_info.get("name")
            else:
                tool_id = getattr(tool_info, "toolUseId", None) or getattr(tool_info, "tool_use_id", None)
                raw_input = getattr(tool_info, "input", None) or getattr(tool_info, "arguments", None)
                name = getattr(tool_info, "name", None)

            if raw_input in (None, ""):
                continue

            tool_entry = self._get_or_create_tool_entry(tool_id, name)
            if not tool_entry:
                continue

            if self._update_tool_entry_input(tool_entry, raw_input):
                updated = True

        return updated

    def _get_or_create_tool_entry(self, tool_id: Optional[str], name: Optional[str]) -> Optional[Dict[str, Any]]:
        if tool_id and tool_id in self.ui_state.tool_map:
            return self.ui_state.tool_map[tool_id]

        if not tool_id and name:
            for entry in self.ui_state.assistant_message["tool_calls"]:
                if entry.get("name") == name:
                    return entry

        if not tool_id and not name:
            return None

        entry = {
            "name": name or f"Tool {len(self.ui_state.assistant_message['tool_calls']) + 1}",
            "tool_use_id": tool_id,
            "input": None,
            "input_is_json": False,
            "result": None,
            "result_is_json": False,
        }
        self.ui_state.assistant_message["tool_calls"].append(entry)
        if tool_id:
            self.ui_state.tool_map[tool_id] = entry
        return entry

    def _update_tool_entry_input(self, tool_entry: Dict[str, Any], raw_input: Any) -> bool:
        existing = tool_entry.get("input")
        if isinstance(existing, str) and existing.strip():
            return False
        if existing not in (None, [], {}) and not isinstance(existing, str):
            return False

        normalized_input, input_is_json = utils.normalize_tool_value(raw_input)
        value = normalized_input if normalized_input is not None else raw_input
        if value is None:
            return False

        tool_entry["input"] = value
        tool_entry["input_is_json"] = input_is_json or isinstance(raw_input, (dict, list))
        return True
