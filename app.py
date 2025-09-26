"""Streamlit application entry point."""

from app.main import StreamlitChatApp


def main() -> None:
    """Main entry point for the Streamlit application."""
    app = StreamlitChatApp()
    app.run()


if __name__ == "__main__":
    main()
