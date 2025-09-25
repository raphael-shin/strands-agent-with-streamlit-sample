"""Lifecycle and logging-related event handlers."""
from typing import Any, Dict, Optional

from .event_handlers import EventHandler, EventType


class LifecycleHandler(EventHandler):
    """Handle lifecycle events emitted by the agent."""

    @property
    def priority(self) -> int:
        return 50  # Medium priority

    def can_handle(self, event_type: str) -> bool:
        """Handle lifecycle-related event types only."""
        lifecycle_events = {
            EventType.INIT_EVENT_LOOP.value,
            EventType.START_EVENT_LOOP.value,
            EventType.START.value,
            EventType.MESSAGE.value,
            EventType.EVENT.value,
            EventType.COMPLETE.value,
        }
        return event_type in lifecycle_events
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a lifecycle event and return metadata."""
        event_type = next(iter(event.keys()))

        return {"lifecycle_processed": event_type}


class ReasoningHandler(EventHandler):
    """Handle reasoning-related events."""
    
    @property
    def priority(self) -> int:
        return 30  # Higher priority than lifecycle
    
    def can_handle(self, event_type: str) -> bool:
        """React only to reasoning events."""
        reasoning_events = {
            EventType.REASONING.value,
            EventType.REASONING_TEXT.value,
            EventType.REASONING_SIGNATURE.value,
            EventType.REDACTED_CONTENT.value,
        }
        return event_type in reasoning_events
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record the reasoning event."""
        event_type = next(iter(event.keys()))

        return {"reasoning_processed": event_type}


class LoggingHandler(EventHandler):
    """Structured logging handler for every event."""

    def __init__(self, log_level: str = "INFO"):
        pass

    @property
    def priority(self) -> int:
        return 80  # Lower priority so other handlers execute first

    def can_handle(self, event_type: str) -> bool:
        """Log every event regardless of type."""
        return True
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log the event with structured metadata."""
        # Debug: print all events to see structure
        print(f"🔍 Event received: {list(event.keys())}")
        
        # Print complete response when it's finished
        if "complete" in event:
            complete_data = event["complete"]
            print(f"🔍 Complete data keys: {list(complete_data.keys()) if isinstance(complete_data, dict) else type(complete_data)}")
            if isinstance(complete_data, dict) and "result" in complete_data:
                result = complete_data["result"]
                print(f"🔍 Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    print(f"🔍 Content type: {type(content)}")
                    if isinstance(content, list) and len(content) > 0:
                        # Extract the full text content including all tags
                        full_text = content[0].get("text", "")
                        if full_text:
                            print("\n" + "="*80)
                            print("🤖 COMPLETE MODEL RESPONSE:")
                            print("="*80)
                            print(full_text)
                            print("="*80 + "\n")
        
        # Also check for other event types that might contain the full response
        for key, value in event.items():
            if isinstance(value, dict) and "content" in value:
                print(f"🔍 Found content in {key}: {type(value['content'])}")
        
        return None


class DebugHandler(EventHandler):
    """Simplified debugging handler that stores recent events."""
    
    def __init__(self, debug_enabled: bool = False):
        self.debug_enabled = debug_enabled
        self.event_log = []
    
    @property
    def priority(self) -> int:
        return 95  # Lowest priority
    
    def can_handle(self, event_type: str) -> bool:
        """Only process events when debug mode is enabled."""
        return self.debug_enabled
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect lightweight debug information."""
        if not self.debug_enabled:
            return None
        
        event_type = next(iter(event.keys()))
        
        # Append a shallow copy for debugging purposes
        self.event_log.append({
            "event_type": event_type,
            "event_data": event.copy(),
        })

        # Limit to the latest 100 events
        if len(self.event_log) > 100:
            self.event_log.pop(0)

        return None
