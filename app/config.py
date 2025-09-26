"""Application configuration settings."""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class AppConfig:
    """Central configuration for the Streamlit application."""

    # Streamlit page configuration
    page_config: Dict[str, Any] = None

    # Available models
    available_models: List[str] = None

    # Default model
    default_model: str = "us.amazon.nova-pro-v1:0"

    # UI settings
    app_title: str = "🤖 Amazon Bedrock Agent Chat"
    sidebar_header: str = "🔧 Model Settings"
    chat_input_placeholder: str = "Ask me anything..."

    def __post_init__(self):
        if self.page_config is None:
            self.page_config = {
                "page_title": "Strands Agent Chat",
                "page_icon": "🤖",
                "layout": "wide",
            }

        if self.available_models is None:
            self.available_models = [
                "us.amazon.nova-pro-v1:0",
                "us.anthropic.claude-sonnet-4-20250514-v1:0",
                "openai.gpt-oss-120b-1:0",
                "openai.gpt-oss-20b-1:0",
            ]

    def get_default_model_index(self) -> int:
        """Get the index of the default model in the available models list."""
        try:
            return self.available_models.index(self.default_model)
        except ValueError:
            return 0