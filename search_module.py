import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                               QDialog, QVBoxLayout, QListWidget, QListWidgetItem)

class SearchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent 
        self.setFixedHeight(50)
        self.hide() 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(25, 25)
        self.btn_close.clicked.connect(self.hide)
        
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Buscar en este archivo...")
        self.input_search.returnPressed.connect(self.find_next)
        
        self.btn_prev = QPushButton("⬆")
        self.btn_next = QPushButton("⬇")
        self.btn_prev.clicked.connect(self.find_prev)
        self.btn_next.clicked.connect(self.find_next)
        
        layout.addWidget(self.btn_close)
        layout.addWidget(self.input_search)
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.btn_next)
        self.setStyleSheet("background-color: #252526; border-top: 1px solid #3e3e42;")

    def get_active_editor(self):
        if hasattr(self.main_window, 'tabs') and self.main_window.tabs.currentWidget():
            return self.main_window.tabs.currentWidget().editor
        return None

    def find_next(self):
        editor = self.get_active_editor()
        if editor:
            found = editor.find(self.input_search.text())
            if not found: # Loop al inicio
                editor.moveCursor(editor.textCursor().Start)
                editor.find(self.input_search.text())

    def find_prev(self):
        editor = self.get_active_editor()
        if editor:
            editor.find(self.input_search.text(), QTextDocument.FindBackward)

class GlobalSearchDialog(QDialog):
    def __init__(self, root_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Búsqueda Global")
        self.resize(700, 500)
        self.root_dir = root_dir
        
        layout = QVBoxLayout(self)
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Buscar en todo el proyecto (Enter)...")
        self.input_line.returnPressed.connect(self.do_search)
        
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.open_file)
        
        layout.addWidget(self.input_line)
        layout.addWidget(self.results_list)

    def do_search(self):
        text = self.input_line.text().lower()
        if not text: return
        self.results_list.clear()
        
        # EXCLUSIONES PARA VELOCIDAD
        exclude = {'.git', '__pycache__', 'node_modules', 'venv', '.env'}
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude] # Filtrar carpetas pesadas
            
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css', '.json', '.txt', '.md')):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f):
                                if text in line.lower():
                                    rel_path = os.path.relpath(full_path, self.root_dir)
                                    item = QListWidgetItem(f"{rel_path}:{i+1} -> {line.strip()[:80]}")
                                    item.setData(Qt.UserRole, (full_path, i+1))
                                    self.results_list.addItem(item)
                    except: pass
        
        if self.results_list.count() == 0:
            self.results_list.addItem("No hay resultados.")

    def open_file(self, item):
        path, line = item.data(Qt.UserRole)
        self.parent().open_file(path)
        # Aquí podrías añadir lógica para ir a la línea específica
        self.accept()