"""Main Streamlit chat application."""

from .config import AppConfig
from .session_manager import SessionManager
from .ui_manager import UIManager
from .chat_handler import ChatHandler


class StreamlitChatApp:
    """Main Streamlit chat application class."""

    def __init__(self):
        self.config = AppConfig()
        self.session_manager = SessionManager()
        self.ui_manager = UIManager(self.config)
        self.chat_handler = ChatHandler(self.session_manager)

    def run(self) -> None:
        """Run the Streamlit chat application."""
        # Setup page configuration
        self.ui_manager.setup_page()

        # Render sidebar and handle model selection
        selected_model = self.ui_manager.render_sidebar()
        self.session_manager.handle_model_change(selected_model)

        # Render main interface
        current_model = self.session_manager.current_model or selected_model
        self.ui_manager.render_header(current_model)

        # Render chat history
        self.ui_manager.render_chat_history(self.session_manager.messages)

        # Handle new user input
        if prompt := self.ui_manager.get_user_input():
            self.chat_handler.handle_user_input(prompt)