import os
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QIcon, QTextDocument
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
                               QDialog, QListWidget, QListWidgetItem, QLabel, QCheckBox,
                               QMessageBox, QApplication, QStyle)

class SearchWidget(QWidget):
    """Barra de búsqueda local con reemplazo y contador de coincidencias."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedHeight(80)  # Aumentado para dar espacio al reemplazo
        self.hide()

        # Variables de estado
        self.current_match = 0
        self.total_matches = 0
        self.match_positions = []  # Lista de posiciones (cursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # --- Primera fila: búsqueda ---
        row1 = QHBoxLayout()
        self.btn_close = QPushButton()
        self.btn_close.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.btn_close.setFixedSize(25, 25)
        self.btn_close.clicked.connect(self.hide)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Buscar...")
        self.input_search.textChanged.connect(self.update_search)
        self.input_search.returnPressed.connect(self.find_next)

        self.label_match = QLabel("0/0")
        self.label_match.setFixedWidth(50)
        self.label_match.setAlignment(Qt.AlignCenter)

        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        self.btn_prev.setToolTip("Anterior (Shift+Enter)")
        self.btn_prev.clicked.connect(self.find_prev)

        self.btn_next = QPushButton()
        self.btn_next.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.btn_next.setToolTip("Siguiente (Enter)")
        self.btn_next.clicked.connect(self.find_next)

        row1.addWidget(self.btn_close)
        row1.addWidget(self.input_search, 1)
        row1.addWidget(self.label_match)
        row1.addWidget(self.btn_prev)
        row1.addWidget(self.btn_next)

        # --- Segunda fila: reemplazo ---
        row2 = QHBoxLayout()
        self.input_replace = QLineEdit()
        self.input_replace.setPlaceholderText("Reemplazar con...")
        self.input_replace.returnPressed.connect(self.replace_current)

        self.btn_replace = QPushButton()
        self.btn_replace.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btn_replace.setText("Reemplazar")
        self.btn_replace.clicked.connect(self.replace_current)

        self.btn_replace_all = QPushButton()
        self.btn_replace_all.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.btn_replace_all.setText("Reemplazar todo")
        self.btn_replace_all.clicked.connect(self.replace_all)

        # Opciones de búsqueda (opcional)
        self.case_sensitive = QCheckBox("Mayúsculas")
        self.case_sensitive.toggled.connect(self.update_search)

        row2.addWidget(self.input_replace, 1)
        row2.addWidget(self.btn_replace)
        row2.addWidget(self.btn_replace_all)
        row2.addWidget(self.case_sensitive)

        layout.addLayout(row1)
        layout.addLayout(row2)

        self.setStyleSheet("""
            QWidget { background-color: #252526; border-top: 1px solid #3e3e42; }
            QLineEdit { padding: 4px; border: 1px solid #3e3e42; background-color: #1e1e1e; color: #d4d4d4; }
            QPushButton { background-color: #2d2d2d; border: 1px solid #3e3e42; color: #d4d4d4; padding: 4px; }
            QPushButton:hover { background-color: #3d3d3d; }
            QLabel { color: #d4d4d4; }
        """)

    def get_active_editor(self):
        """Devuelve el editor activo o None."""
        if hasattr(self.main_window, 'tabs') and self.main_window.tabs.currentWidget():
            return self.main_window.tabs.currentWidget().editor
        return None

    def update_search(self):
        """Actualiza la lista de coincidencias y resalta."""
        editor = self.get_active_editor()
        if not editor:
            return
        text = self.input_search.text()
        if not text:
            self.clear_matches()
            return

        # Configurar flags de búsqueda
        flags = QTextDocument.FindFlags()
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        # Recorrer todo el documento y guardar posiciones
        self.match_positions = []
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        while True:
            cursor = editor.document().find(text, cursor, flags)
            if cursor.isNull():
                break
            self.match_positions.append(cursor.position())
            # Mover un poco para evitar bucle infinito
            cursor.setPosition(cursor.position() + 1)

        self.total_matches = len(self.match_positions)
        self.current_match = 0
        self.update_label()

        # Resaltar todas las coincidencias (opcional)
        self.highlight_matches()

        if self.total_matches > 0:
            self.go_to_match(0)

    def clear_matches(self):
        self.match_positions = []
        self.total_matches = 0
        self.current_match = 0
        self.update_label()
        # Limpiar resaltado (opcional)
        editor = self.get_active_editor()
        if editor:
            editor.setExtraSelections([])

    def highlight_matches(self):
        """Resalta todas las coincidencias (puedes implementarlo si deseas)."""
        # Por simplicidad, no lo implementamos ahora, pero se puede añadir.
        pass

    def go_to_match(self, index):
        """Mueve el cursor a la coincidencia índice."""
        if index < 0 or index >= self.total_matches:
            return
        editor = self.get_active_editor()
        if not editor:
            return
        pos = self.match_positions[index] - 1  # -1 porque al buscar se posiciona al inicio de la palabra
        cursor = editor.textCursor()
        cursor.setPosition(pos)
        # Seleccionar la palabra
        text = self.input_search.text()
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(text))
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()
        self.current_match = index
        self.update_label()

    def find_next(self):
        if self.total_matches == 0:
            return
        self.current_match = (self.current_match + 1) % self.total_matches
        self.go_to_match(self.current_match)

    def find_prev(self):
        if self.total_matches == 0:
            return
        self.current_match = (self.current_match - 1) % self.total_matches
        self.go_to_match(self.current_match)

    def update_label(self):
        self.label_match.setText(f"{self.current_match+1}/{self.total_matches}" if self.total_matches else "0/0")

    def replace_current(self):
        """Reemplaza la coincidencia actual."""
        if self.total_matches == 0:
            return
        editor = self.get_active_editor()
        if not editor:
            return
        replace_text = self.input_replace.text()
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replace_text)
            # Actualizar la lista de coincidencias después del reemplazo
            self.update_search()
            # Si todavía hay coincidencias, mostrar la siguiente
            if self.total_matches > 0:
                self.find_next()

    def replace_all(self):
        """Reemplaza todas las coincidencias."""
        if self.total_matches == 0:
            return
        reply = QMessageBox.question(self, "Reemplazar todo",
                                     f"¿Reemplazar todas las {self.total_matches} coincidencias?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        editor = self.get_active_editor()
        if not editor:
            return
        text = self.input_search.text()
        replace_text = self.input_replace.text()
        flags = QTextDocument.FindFlags()
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        while True:
            cursor = editor.document().find(text, cursor, flags)
            if cursor.isNull():
                break
            cursor.insertText(replace_text)
        cursor.endEditBlock()
        # Actualizar después del reemplazo
        self.update_search()


class GlobalSearchDialog(QDialog):
    """Diálogo de búsqueda global con navegación a línea exacta."""
    def __init__(self, root_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Búsqueda Global")
        self.resize(700, 500)
        self.root_dir = root_dir
        self.main_window = parent  # Guardamos referencia explícita

        layout = QVBoxLayout(self)

        # Entrada de búsqueda
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Buscar en todo el proyecto (Enter)...")
        self.input_line.returnPressed.connect(self.do_search)

        # Opciones (simples)
        self.case_sensitive = QCheckBox("Mayúsculas")

        # Lista de resultados
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.open_file)

        layout.addWidget(self.input_line)
        layout.addWidget(self.case_sensitive)
        layout.addWidget(self.results_list)

    def do_search(self):
        text = self.input_line.text()
        if not text:
            return
        self.results_list.clear()

        # Exclusiones por defecto
        exclude = {'.git', '__pycache__', 'node_modules', 'venv', '.env', '.idea', 'build', 'dist'}

        # Extensiones de archivo soportadas (puedes ampliar)
        extensions = ('.py', '.js', '.html', '.css', '.json', '.txt', '.md', '.cpp', '.c', '.h', '.php')

        for root, dirs, files in os.walk(self.root_dir):
            # Filtrar directorios excluidos
            dirs[:] = [d for d in dirs if d not in exclude]

            for file in files:
                if file.endswith(extensions):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                # Búsqueda con/sin sensibilidad a mayúsculas
                                if self.case_sensitive.isChecked():
                                    match = text in line
                                else:
                                    match = text.lower() in line.lower()
                                if match:
                                    # Encontrar la posición de la primera ocurrencia en la línea
                                    if self.case_sensitive.isChecked():
                                        col = line.find(text)
                                    else:
                                        col = line.lower().find(text.lower())
                                    # Guardar datos: ruta, línea, columna, texto
                                    rel_path = os.path.relpath(full_path, self.root_dir)
                                    display = f"{rel_path}:{line_num} → {line.strip()[:80]}"
                                    item = QListWidgetItem(display)
                                    item.setData(Qt.UserRole, (full_path, line_num, col, len(text)))
                                    self.results_list.addItem(item)
                    except Exception as e:
                        # Ignorar archivos problemáticos
                        pass

        if self.results_list.count() == 0:
            self.results_list.addItem("No hay resultados.")

    def open_file(self, item):
        """Abre el archivo y posiciona el cursor en la línea y columna exactas."""
        data = item.data(Qt.UserRole)
        if not data:
            return
        path, line, col, length = data
        # Llamar al método de la ventana principal para abrir el archivo
        if hasattr(self.main_window, 'open_file'):
            self.main_window.open_file(path)
            # Obtener el editor activo (el archivo recién abierto)
            editor = None
            if hasattr(self.main_window, 'tabs') and self.main_window.tabs.currentWidget():
                editor = self.main_window.tabs.currentWidget().editor
            if editor:
                # Mover el cursor a la línea y columna
                cursor = editor.textCursor()
                cursor.movePosition(QTextCursor.Start)
                # Saltar a la línea
                cursor.movePosition(QTextCursor.Down, n=line-1)
                # Mover a la columna (si es necesario)
                cursor.movePosition(QTextCursor.Right, n=col)
                # Seleccionar la palabra encontrada
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, n=length)
                editor.setTextCursor(cursor)
                editor.ensureCursorVisible()
                editor.setFocus()
        self.accept()