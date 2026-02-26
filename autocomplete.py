from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem

class AutoCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchStartsWith)
        
        self.model = QStandardItemModel(self)
        self.setModel(self.model)

    def load_keywords(self, keywords_list):
        """Carga una lista estática de palabras (para JS, HTML, etc)"""
        self.model.clear()
        for word in sorted(keywords_list):
            item = QStandardItem(word)
            item.setData(" [kw] ", Qt.ToolTipRole)
            self.model.appendRow(item)

    def update_jedi_completions(self, completions):
        """Carga sugerencias dinámicas de Python (Jedi)"""
        self.model.clear()
        for data in sorted(completions, key=lambda x: x['name']):
            item = QStandardItem(data['name'])
            kind = data.get('type', '')
            icon_text = " [ƒ] " if kind == 'function' else " [c] " if kind == 'class' else " [v] "
            item.setData(icon_text, Qt.ToolTipRole)
            self.model.appendRow(item)