"""Streamlit UI event handlers and helpers."""
import json
import re
from typing import Any, Dict, Optional

import streamlit as st

from .event_handlers import EventHandler, EventType

THINKING_PATTERN = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL)


def parse_model_response(raw_text):
    """Return response text and optional chain-of-thought from raw model output."""
    if not raw_text:
        return "", None
    match = THINKING_PATTERN.search(raw_text)
    chain_of_thought = match.group(1).strip() if match else None
    cleaned = THINKING_PATTERN.sub("", raw_text).strip()
    return cleaned, chain_of_thought


def strip_partial_thinking(raw_text):
    """Hide incomplete thinking tags during streaming."""
    if "<thinking>" in raw_text and "</thinking>" not in raw_text:
        return raw_text.split("<thinking>")[0]
    if "<thinking>" in raw_text and "</thinking>" in raw_text:
        cleaned, _ = parse_model_response(raw_text)
        return cleaned
    return raw_text


def normalize_tool_value(value):
    """Normalize tool payloads into display value and format hint."""
    if value is None:
        return None, False
    if isinstance(value, (dict, list)):
        return value, True
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.startswith("{") or candidate.startswith("["):
            try:
                return json.loads(value), True
            except json.JSONDecodeError:
                pass
        return value, False
    return value, False


def render_tool_value(value, as_json):
    """Render a tool payload in the appropriate Streamlit widget."""
    if value is None:
        return
    if as_json:
        st.json(value)
    elif isinstance(value, str):
        st.code(value)
    else:
        st.write(value)


def render_chain_of_thought(chain_of_thought):
    if not chain_of_thought:
        return
    with st.expander("🤔 Chain of Thought", expanded=False):
        st.markdown(chain_of_thought)


def render_tool_calls(tool_calls):
    if not tool_calls:
        return
    for index, call in enumerate(tool_calls, start=1):
        title_name = call.get("name") or f"Tool {index}"
        with st.expander(f"🔧 Tool Usage: {title_name}", expanded=False):
            tool_use_id = call.get("tool_use_id")
            if tool_use_id:
                st.write(f"**Tool ID:** {tool_use_id}")
            input_value = call.get("input")
            if input_value is not None:
                st.write("**Input:**")
                render_tool_value(input_value, call.get("input_is_json", False))
            result_value = call.get("result")
            if result_value is not None:
                st.write("**Result:**")
                render_tool_value(result_value, call.get("result_is_json", False))


class StreamlitUIState:
    """State container used by the Streamlit UI handler."""
    
    def __init__(self):
        # Streamlit placeholders
        self.status_placeholder = None
        self.tool_placeholder = None
        self.chain_placeholder = None
        self.response_placeholder = None
        self.reasoning_status = None
        self.reasoning_placeholder = None
        self.message_container = None
        
        # Assistant message state
        self.assistant_message = {
            "text": "",
            "chain_of_thought": None,
            "tool_calls": [],
        }
        self.tool_map = {}
        self.raw_response = ""
        self.reasoning_text = ""
        self.final_message = None
        self.force_stop_error = None
        self.assistant_appended = False
    
    def reset(self):
        """Reset state while keeping placeholder references alive."""
        self.assistant_message = {
            "text": "",
            "chain_of_thought": None,
            "tool_calls": [],
        }
        self.tool_map = {}
        self.raw_response = ""
        self.reasoning_text = ""
        self.final_message = None
        self.force_stop_error = None
        self.assistant_appended = False
        self.reasoning_status = None
        self.reasoning_placeholder = None
        self.message_container = None
        # Placeholders remain attached to the Streamlit container


class StreamlitUIHandler(EventHandler):
    """Update the Streamlit UI in response to streaming events."""
    
    def __init__(self, ui_state: StreamlitUIState):
        self.ui_state = ui_state
    
    def set_placeholders(self, status_placeholder, tool_placeholder, chain_placeholder, response_placeholder):
        """Attach Streamlit placeholders for progressive rendering."""
        self.ui_state.status_placeholder = status_placeholder
        self.ui_state.tool_placeholder = tool_placeholder
        self.ui_state.chain_placeholder = chain_placeholder
        self.ui_state.response_placeholder = response_placeholder
    
    @property
    def priority(self) -> int:
        return 10  # UI updates should happen early
    
    def can_handle(self, event_type: str) -> bool:
        """Handle only events that influence the UI."""
        ui_events = {
            "reasoningText",
            "current_tool_use", 
            "tool_result",
            "data",
            "result",
            "force_stop",
        }
        return event_type in ui_events
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Dispatch events to the appropriate UI update method."""
        # Resolve the event type in priority order
        if "reasoningText" in event:
            self._handle_reasoning_text(event)
        elif "current_tool_use" in event:
            self._handle_current_tool_use(event)
        elif "tool_result" in event:
            self._handle_tool_result(event)
        elif "data" in event:
            self._handle_data(event)
        elif "result" in event:
            self._handle_result(event)
        elif "force_stop" in event:
            self._handle_force_stop(event)
        
        return None  # UI updates do not return additional payload
    
    def _handle_reasoning_text(self, event: Dict[str, Any]) -> None:
        """Append reasoning text to the status placeholder."""
        if not self.ui_state.reasoning_status and self.ui_state.status_placeholder:
            with self.ui_state.status_placeholder.container():
                self.ui_state.reasoning_status = st.status("🧠 Reasoning...", expanded=True)
                self.ui_state.reasoning_placeholder = self.ui_state.reasoning_status.empty()
        
        reasoning_content = event.get("reasoningText", "")
        if reasoning_content and self.ui_state.reasoning_placeholder:
            self.ui_state.reasoning_text += reasoning_content
            self.ui_state.reasoning_placeholder.markdown(self.ui_state.reasoning_text)
    
    def _handle_current_tool_use(self, event: Dict[str, Any]) -> None:
        """Capture metadata when a tool invocation starts."""
        tool_data = event.get("current_tool_use", {})
        tool_id = tool_data.get("toolUseId") or tool_data.get("tool_use_id")
        
        if tool_id and tool_id in self.ui_state.tool_map:
            tool_entry = self.ui_state.tool_map[tool_id]
        else:
            input_value, input_is_json = normalize_tool_value(tool_data.get("input"))
            tool_entry = {
                "name": tool_data.get("name") or f"Tool {len(self.ui_state.assistant_message['tool_calls']) + 1}",
                "tool_use_id": tool_id,
                "input": input_value,
                "input_is_json": input_is_json,
                "result": None,
                "result_is_json": False,
            }
            self.ui_state.assistant_message["tool_calls"].append(tool_entry)
            if tool_id:
                self.ui_state.tool_map[tool_id] = tool_entry
        
        self._refresh_tool_ui()
    
    def _handle_tool_result(self, event: Dict[str, Any]) -> None:
        """Attach a tool result payload to the most recent invocation."""
        result_payload = event.get("tool_result")
        tool_id = None
        display_payload = result_payload
        
        if isinstance(result_payload, dict):
            tool_id = result_payload.get("toolUseId") or result_payload.get("tool_use_id")
            if "output" in result_payload:
                display_payload = result_payload["output"]
            elif "content" in result_payload:
                display_payload = result_payload["content"]
            else:
                stripped = {
                    k: v for k, v in result_payload.items()
                    if k not in {"toolUseId", "tool_use_id"}
                }
                if stripped:
                    display_payload = stripped
        
        value, is_json = normalize_tool_value(display_payload)
        
        if tool_id and tool_id in self.ui_state.tool_map:
            tool_entry = self.ui_state.tool_map[tool_id]
        elif self.ui_state.assistant_message["tool_calls"]:
            tool_entry = self.ui_state.assistant_message["tool_calls"][-1]
        else:
            tool_entry = {
                "name": "Tool",
                "tool_use_id": tool_id,
                "input": None,
                "input_is_json": False,
                "result": None,
                "result_is_json": False,
            }
            self.ui_state.assistant_message["tool_calls"].append(tool_entry)
            if tool_id:
                self.ui_state.tool_map[tool_id] = tool_entry
        
        tool_entry["result"] = value if value is not None else display_payload
        tool_entry["result_is_json"] = is_json or isinstance(display_payload, (dict, list))
        self._refresh_tool_ui()
    
    def _handle_data(self, event: Dict[str, Any]) -> None:
        """Stream token chunks into the response placeholder."""
        data_chunk = event.get("data", "")
        if not data_chunk or not self.ui_state.response_placeholder:
            return
        
        self.ui_state.raw_response += data_chunk
        partial_text = strip_partial_thinking(self.ui_state.raw_response)
        
        if partial_text:
            self.ui_state.response_placeholder.markdown(f"{partial_text}▌")
        else:
            self.ui_state.response_placeholder.markdown("▌")
    
    def _handle_result(self, event: Dict[str, Any]) -> None:
        """Cache the final agent result for post-processing."""
        agent_result = event.get("result")
        if hasattr(agent_result, "message") and agent_result.message:
            self.ui_state.final_message = agent_result.message
        elif isinstance(agent_result, dict):
            self.ui_state.final_message = agent_result.get("message")
    
    def _handle_force_stop(self, event: Dict[str, Any]) -> None:
        """Render a force-stop error message."""
        reason = event.get("force_stop_reason", "Unknown error")
        self.ui_state.force_stop_error = f"Error: {reason}"
        
        if self.ui_state.response_placeholder:
            self.ui_state.response_placeholder.markdown(f":red[{self.ui_state.force_stop_error}]")
    
    def _refresh_tool_ui(self):
        """Re-render the tool call expander."""
        if not self.ui_state.tool_placeholder:
            return
            
        self.ui_state.tool_placeholder.empty()
        if self.ui_state.assistant_message["tool_calls"]:
            with self.ui_state.tool_placeholder.container():
                render_tool_calls(self.ui_state.assistant_message["tool_calls"])
    
    def finalize_response(self):
        """Finalize UI elements after streaming completes."""
        # Complete the reasoning status indicator if it exists
        if self.ui_state.reasoning_text and self.ui_state.reasoning_status:
            self.ui_state.reasoning_status.update(
                label="✅ Reasoning Complete", 
                state="complete", 
                expanded=False
            )

        # Create a clean container for the final layout
        final_container = self.ui_state.message_container.empty() if self.ui_state.message_container else None

        # Handle error scenarios first
        if self.ui_state.force_stop_error:
            self.ui_state.assistant_message["text"] = self.ui_state.force_stop_error
            self.ui_state.assistant_message["chain_of_thought"] = None

            if final_container:
                with final_container:
                    st.markdown(f":red[{self.ui_state.force_stop_error}]")
            elif self.ui_state.response_placeholder:
                self.ui_state.response_placeholder.markdown(f":red[{self.ui_state.force_stop_error}]")

            return self.ui_state.assistant_message

        # Clear temporary placeholders; the final container will replace them
        if self.ui_state.status_placeholder:
            self.ui_state.status_placeholder.empty()
        if self.ui_state.tool_placeholder:
            self.ui_state.tool_placeholder.empty()
        if self.ui_state.chain_placeholder:
            self.ui_state.chain_placeholder.empty()
        if self.ui_state.response_placeholder:
            self.ui_state.response_placeholder.empty()

        # Determine the final text content
        if not self.ui_state.raw_response and self.ui_state.final_message:
            self.ui_state.raw_response = self._extract_text_from_message(self.ui_state.final_message)

        final_text, chain_of_thought = parse_model_response(self.ui_state.raw_response)
        display_text = final_text or "*Computation completed.*"

        self.ui_state.assistant_message["text"] = display_text
        self.ui_state.assistant_message["chain_of_thought"] = chain_of_thought

        if final_container:
            with final_container:
                if self.ui_state.reasoning_text:
                    with st.expander("🧠 Reasoning", expanded=False):
                        st.markdown(self.ui_state.reasoning_text)

                if self.ui_state.assistant_message["tool_calls"]:
                    render_tool_calls(self.ui_state.assistant_message["tool_calls"])

                if chain_of_thought:
                    render_chain_of_thought(chain_of_thought)

                st.markdown(display_text)
        else:
            if self.ui_state.reasoning_text and self.ui_state.status_placeholder:
                with self.ui_state.status_placeholder.container():
                    with st.expander("🧠 Reasoning", expanded=False):
                        st.markdown(self.ui_state.reasoning_text)

            if self.ui_state.assistant_message["tool_calls"]:
                self._refresh_tool_ui()

            if self.ui_state.response_placeholder:
                self.ui_state.response_placeholder.markdown(display_text)

            if chain_of_thought and self.ui_state.chain_placeholder:
                with self.ui_state.chain_placeholder.container():
                    render_chain_of_thought(chain_of_thought)

        return self.ui_state.assistant_message

    def _extract_text_from_message(self, message):
        """Extract plain text from an agent message payload."""
        if not message:
            return ""
        if isinstance(message, str):
            return message
        content = message.get("content")
        if isinstance(content, list):
            for item in content:
                text = item.get("text")
                if text:
                    return text
        if isinstance(content, str):
            return content
        return ""
