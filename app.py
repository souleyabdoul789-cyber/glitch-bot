from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, RichLog

class GlitchApp(App):
    CSS = """
    #sidebar { width: 20; border: solid green; }
    #chat { border: solid cyan; }
    """

    def compose(self) -> ComposeResult:
        yield Header()  # zone du haut, pour tes notifications
        with Horizontal():
            with Vertical(id="sidebar"):
                yield ListView(
                    ListItem(Label("glitch-general")),
                    ListItem(Label("projet-asp")),
                )
            with Vertical(id="chat"):
                yield RichLog(id="messages")  # les messages du salon actif
                yield Input(placeholder="Écris ton message...")
        yield Footer()

if __name__ == "__main__":
    GlitchApp().run()
