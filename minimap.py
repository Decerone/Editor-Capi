from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QMouseEvent

class CodeMinimap(QPlainTextEdit):
    def __init__(self, parent_editor):
        super().__init__()
        self.parent_editor = parent_editor
        self.setReadOnly(True)
        self.setFixedWidth(120)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        font = QFont("Consolas", 4)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFocusPolicy(Qt.NoFocus)  # Importante: no toma foco

        self.parent_editor.verticalScrollBar().valueChanged.connect(self.on_parent_scroll)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._sync_content)
        self.parent_editor.textChanged.connect(self.delayed_sync)
        self._updating_scroll = False

    def delayed_sync(self):
        self.update_timer.start(200)

    def _sync_content(self):
        self.setPlainText(self.parent_editor.toPlainText())
        self.sync_scroll_from_parent()

    def sync_with_parent(self):
        self._sync_content()

    def on_parent_scroll(self, value):
        if self._updating_scroll:
            return
        self._updating_scroll = True
        self.sync_scroll_from_parent()
        self._updating_scroll = False

    def sync_scroll_from_parent(self):
        parent_scroll = self.parent_editor.verticalScrollBar()
        if parent_scroll.maximum() <= 0:
            return
        ratio = parent_scroll.value() / parent_scroll.maximum()
        my_scroll = self.verticalScrollBar()
        if my_scroll.maximum() > 0:
            my_scroll.setValue(int(ratio * my_scroll.maximum()))

    def mousePressEvent(self, event: QMouseEvent):
        cursor = self.cursorForPosition(event.pos())
        line = cursor.blockNumber()
        editor = self.parent_editor
        if editor:
            doc = editor.document()
            block = doc.findBlockByNumber(line)
            if block.isValid():
                cursor = editor.textCursor()
                cursor.setPosition(block.position())
                editor.setTextCursor(cursor)
                editor.centerCursor()
                editor.setFocus()  # Devolver foco al editor
        event.accept()  # No propagar

    def apply_theme(self, colors):
        bg = colors.get('bg', '#1e1e1e')
        fg = colors.get('fg', '#d4d4d4')
        line_bg = colors.get('line_bg', '#333')
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-left: 1px solid {line_bg};
            }}
        """)