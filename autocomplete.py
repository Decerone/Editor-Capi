import json
import os
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtWidgets import QCompleter
from PySide6.QtGui import QTextCursor
from utils import resource_path  # Importamos la ruta segura

KEYWORDS_FILE = "keywords.json"

class AutoCompleter:
    def __init__(self, editor):
        self.editor = editor
        self.completer = None
        self.model = QStringListModel()
        self.keywords_data = self._load_keywords()

    def _load_keywords(self):
        # Usamos resource_path para encontrar el JSON al compilar
        path = resource_path(KEYWORDS_FILE)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}

    def setup(self, language="text"):
        words = self.keywords_data.get(language, [])
        self.completer = QCompleter(words, self.editor)
        self.completer.setModel(self.model)
        self.model.setStringList(words)
        self.completer.setWidget(self.editor)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion, Qt.QueuedConnection)

    def update_model(self, language):
        if language == 'py': language = 'python'
        if language == 'js': language = 'javascript'
        words = self.keywords_data.get(language, [])
        self.model.setStringList(words)

    def insert_completion(self, text):
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        cursor.insertText(text)
        self.editor.setTextCursor(cursor)