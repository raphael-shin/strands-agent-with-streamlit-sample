"""Automated tests for the Streamlit event flow."""
from pathlib import Path
import sys

import pytest
from unittest.mock import Mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pytest.importorskip("strands")

from agents.bedrock_agent import BedrockAgent
from handlers import ui_handlers as ui_handlers_module
from handlers.ui_handlers import StreamlitUIHandler, StreamlitUIState


class MockPlaceholder:
    """Simple mock that mimics Streamlit placeholders."""
    def __init__(self, name):
        self.name = name
        self.content = ""
        self.markdown_calls = []
        self.empty_calls = 0
    
    def markdown(self, content):
        self.content = content
        self.markdown_calls.append(content)
    
    def empty(self):
        self.empty_calls += 1
        self.content = ""


class TestStreamlitUIState:
    """Tests that validate StreamlitUIState behaviour."""
    
    def test_placeholder_persistence_after_reset(self):
        """reset() should keep placeholder references intact."""
        ui_state = StreamlitUIState()
        
        # Provide placeholder references
        response_placeholder = MockPlaceholder("response")
        tool_placeholder = MockPlaceholder("tool")
        ui_state.response_placeholder = response_placeholder
        ui_state.tool_placeholder = tool_placeholder
        
        # Seed message state
        ui_state.raw_response = "test response"
        ui_state.tool_map = {"tool1": "data"}
        
        # Call reset
        ui_state.reset()
        
        # Placeholders remain while state resets
        assert ui_state.response_placeholder is response_placeholder
        assert ui_state.tool_placeholder is tool_placeholder
        assert ui_state.raw_response == ""
        assert ui_state.tool_map == {}


class TestStreamlitUIHandler:
    """Tests around StreamlitUIHandler behaviour."""
    
    def setup_method(self):
        """Construct a handler with mock placeholders."""
        self.ui_state = StreamlitUIState()
        self.handler = StreamlitUIHandler(self.ui_state)
        
        # Construct mock placeholders
        self.response_placeholder = MockPlaceholder("response")
        self.tool_placeholder = MockPlaceholder("tool")
        self.status_placeholder = MockPlaceholder("status")
        self.chain_placeholder = MockPlaceholder("chain")
        
        self.handler.set_placeholders(
            self.status_placeholder,
            self.tool_placeholder,
            self.chain_placeholder,
            self.response_placeholder
        )
    
    def test_can_handle_ui_events(self):
        """The handler should accept relevant event types."""
        assert self.handler.can_handle("data") == True
        assert self.handler.can_handle("reasoningText") == True
        assert self.handler.can_handle("current_tool_use") == True
        assert self.handler.can_handle("tool_result") == True
        assert self.handler.can_handle("result") == True
        assert self.handler.can_handle("force_stop") == True
        assert self.handler.can_handle("unknown_event") == False
    
    def test_handle_data_event(self):
        """Streaming data should update the response placeholder."""
        # Process a data event
        event = {"data": "Hello World"}
        self.handler.handle(event)
        
        # Ensure state and placeholder were touched
        assert "Hello World" in self.ui_state.raw_response
        assert len(self.response_placeholder.markdown_calls) > 0
        assert "Hello World" in self.response_placeholder.markdown_calls[-1]
    
    def test_handle_reasoning_event(self):
        """Reasoning events should append to the running text."""
        # Build a fake status object
        mock_status = Mock()
        mock_status.empty.return_value = Mock()
        
        # Patch container context manager to avoid Streamlit calls
        self.status_placeholder.container = Mock()
        self.status_placeholder.container.return_value.__enter__ = Mock(return_value=Mock())
        self.status_placeholder.container.return_value.__exit__ = Mock(return_value=None)
        
        # Patch st.status to return the mock
        ui_handlers_module.st = Mock()
        ui_handlers_module.st.status.return_value = mock_status
        
        # Process a reasoning event
        event = {"reasoningText": "Thinking..."}
        self.handler.handle(event)
        
        # Reasoning text should accumulate
        assert "Thinking..." in self.ui_state.reasoning_text
    
    def test_handle_force_stop_event(self):
        """Force-stop events should store the error message."""
        event = {"force_stop": True, "force_stop_reason": "Test error"}
        self.handler.handle(event)
        
        # Verify the error was captured and rendered
        assert self.ui_state.force_stop_error == "Error: Test error"
        assert len(self.response_placeholder.markdown_calls) > 0
        assert "Test error" in self.response_placeholder.markdown_calls[-1]
    
    def test_placeholder_none_handling(self):
        """Handler should safely skip None placeholders."""
        # Drop the placeholder reference
        self.ui_state.response_placeholder = None
        
        # Process data without raising
        event = {"data": "Test data"}
        result = self.handler.handle(event)
        
        # Handler should return None (meaning handled internally)
        assert result is None
        # No state update occurs without a placeholder
        assert "Test data" not in self.ui_state.raw_response


class TestBedrockAgentIntegration:
    """Integration-style tests around BedrockAgent."""
    
    def setup_method(self):
        """Instantiate the agent for each test."""
        self.agent = BedrockAgent()
    
    def test_ui_state_persistence(self):
        """The agent should reuse the same UI state instance."""
        # Keep the original reference ID
        initial_ui_state = self.agent.get_ui_state()
        initial_id = id(initial_ui_state)
        
        # Register placeholders on the handler
        response_placeholder = MockPlaceholder("response")
        for handler in self.agent.event_registry._handlers:
            if hasattr(handler, 'set_placeholders'):
                handler.set_placeholders(
                    MockPlaceholder("status"),
                    MockPlaceholder("tool"),
                    MockPlaceholder("chain"),
                    response_placeholder
                )
                break
        
        # Simulate the reset step of the stream
        self.agent.ui_state.reset()
        
        # The identity stays the same and placeholders remain
        assert id(self.agent.get_ui_state()) == initial_id
        assert self.agent.get_ui_state().response_placeholder is response_placeholder
    
    def test_handler_registration(self):
        """Verify all core handlers are registered."""
        handler_types = [type(h).__name__ for h in self.agent.event_registry._handlers]
        
        # Confirm the expected handler types are present
        assert "StreamlitUIHandler" in handler_types
        assert "LifecycleHandler" in handler_types
        assert "ReasoningHandler" in handler_types
        assert "LoggingHandler" in handler_types
        assert "DebugHandler" in handler_types
    
    def test_event_processing_flow(self):
        """Processing a data event should update the UI state."""
        # Attach placeholders before processing
        response_placeholder = MockPlaceholder("response")
        for handler in self.agent.event_registry._handlers:
            if hasattr(handler, 'set_placeholders'):
                handler.set_placeholders(
                    MockPlaceholder("status"),
                    MockPlaceholder("tool"),
                    MockPlaceholder("chain"),
                    response_placeholder
                )
                break
        
        # Process a synthetic streaming event
        test_event = {"data": "Test streaming text"}
        results = self.agent.event_registry.process_event(test_event)
        
        # Ensure raw response and placeholder were updated
        ui_state = self.agent.get_ui_state()
        assert "Test streaming text" in ui_state.raw_response
        assert len(response_placeholder.markdown_calls) > 0


class TestEventRegistry:
    """Tests for EventRegistry helpers."""
    
    def test_event_type_extraction(self):
        """Event type extraction should respect the priority order."""
        from handlers.event_handlers import EventRegistry
        
        registry = EventRegistry()
        
        # Validate extraction order
        assert registry._extract_event_type({"data": "text", "other": "value"}) == "data"
        assert registry._extract_event_type({"current_tool_use": {}, "event": {}}) == "current_tool_use"
        assert registry._extract_event_type({"unknown": "value"}) == "unknown"


if __name__ == "__main__":
    # Execute a lightweight manual test run
    import sys
    
    def run_tests():
        """Execute the test methods without pytest."""
        test_classes = [
            TestStreamlitUIState,
            TestStreamlitUIHandler, 
            TestBedrockAgentIntegration,
            TestEventRegistry
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for test_class in test_classes:
            instance = test_class()

            # Run setup_method if the class defines one
            if hasattr(instance, 'setup_method'):
                instance.setup_method()

            # Execute every test_* method
            for method_name in dir(instance):
                if method_name.startswith('test_'):
                    total_tests += 1
                    try:
                        method = getattr(instance, method_name)
                        method()
                        passed_tests += 1
                    except Exception as e:
                        pass

        return passed_tests == total_tests
    
    success = run_tests()
    sys.exit(0 if success else 1)
