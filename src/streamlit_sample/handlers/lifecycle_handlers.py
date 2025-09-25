"""Lifecycle and logging-related event handlers."""
import logging
from typing import Any, Dict, Optional

from .event_handlers import EventHandler, EventType

# Configure module-level logger
logger = logging.getLogger("strands_agent")


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
        
        # Currently log only; hook for future expansion
        logger.debug(f"Lifecycle event: {event_type}")

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
        
        # Currently log only; leaving room for analysis enhancements
        logger.debug(f"Reasoning event: {event_type}")

        return {"reasoning_processed": event_type}


class LoggingHandler(EventHandler):
    """Structured logging handler for every event."""

    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("strands_agent.events")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Attach a console handler if none is present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @property
    def priority(self) -> int:
        return 80  # Lower priority so other handlers execute first

    def can_handle(self, event_type: str) -> bool:
        """Log every event regardless of type."""
        return True
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log the event with structured metadata."""
        event_type = next(iter(event.keys()))
        event_data = event[event_type]
        
        # Adjust log levels based on event category
        if event_type in [EventType.DATA.value, EventType.DELTA.value]:
            # Text streaming should not spam higher levels
            self.logger.debug(f"Stream: {event_type} - {len(str(event_data))} chars")
        elif event_type in [EventType.CURRENT_TOOL_USE.value, EventType.TOOL_RESULT.value]:
            # Tool usage is valuable at INFO level
            tool_name = event_data.get("name", "unknown") if isinstance(event_data, dict) else "unknown"
            self.logger.info(f"Tool: {event_type} - {tool_name}")
        elif event_type == EventType.FORCE_STOP.value:
            # Force-stop events are treated as errors
            reason = event.get("force_stop_reason", "unknown")
            self.logger.error(f"Error: {event_type} - {reason}")
        else:
            # Everything else lands at INFO level
            self.logger.info(f"Event: {event_type}")

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
