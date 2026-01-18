import sys
import os
import json

# --- IMPORTACIONES DE QT ---
from PySide6.QtCore import (QSize, Qt, QRect, QTimer, QFileInfo, QDir)
from PySide6.QtGui import (QAction, QActionGroup, QColor, QTextCharFormat, QFont, QFontMetricsF,
                           QSyntaxHighlighter, QTextCursor, QPainter, QIcon, QKeySequence)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPlainTextEdit, QSplitter, QFileDialog, QMessageBox, 
                               QFileSystemModel, QTabWidget, QMenu, QTextEdit, 
                               QLabel, QLineEdit, QPushButton, QFrame, QDialog, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog)

# --- IMPORTACIONES DE PYGMENTS ---
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound

# --- IMPORTACIONES LOCALES ---
try:
    from utils import THEMES, resource_path
    from sidebar import FileSidebar, EmojiFileSystemModel 
    from terminal import EditorTerminal
    from autocomplete import AutoCompleter
    from minimap import CodeMinimap
except ImportError as e:
    print(f"ERROR CRÍTICO: Faltan archivos locales.\nDetalle: {e}")
    sys.exit(1)

SESSION_FILE = "session.json"
CONFIG_FILE = "config.json"

# =========================================================================
#  AUXILIARES
# =========================================================================

def get_data_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.getcwd()
    return os.path.join(base_path, filename)

def get_tab_emoji(file_path):
    if not file_path: return "📝" 
    ext = os.path.splitext(file_path)[1].lower()
    emoji_map = {
        '.py': '🐍', '.pyw': '🐍', '.php': '🐘', '.html': '🌐', '.htm': '🌐',
        '.css': '🎨', '.js': '📜', '.json': '🔧', '.sql': '🗄️', 
        '.txt': '📄', '.md': '📝', '.c': '🇨', '.cpp': '🇨', '.h': '🇨', '.rs': '🦀',
        '.java': '☕', '.sh': '💻', '.bash': '💻', '.zip': '📦'
    }
    return emoji_map.get(ext, "📄")

def get_keyword_key(file_path):
    if not file_path: return "text"
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        '.py': 'python', '.pyw': 'python', '.js': 'javascript', '.rs': 'rust',
        '.html': 'html', '.htm': 'html', '.css': 'css', '.php': 'php',
        '.sql': 'sql', '.java': 'java', '.c': 'cpp', '.cpp': 'cpp', '.h': 'cpp',
        '.json': 'json'
    }
    return mapping.get(ext, ext.replace('.', ''))

# =========================================================================
#  CLASES DEL EDITOR
# =========================================================================

class PySideHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, language="text", theme_name="Dark"):
        super().__init__(parent)
        self.language = language
        self.theme_name = theme_name
        self.formats = {}
        self.setup_formats()

    def setup_formats(self):
        colors = THEMES.get(self.theme_name, THEMES['Dark'])['tags']
        self.formats = {}
        for tag, hex_color in colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(hex_color))
            if tag in ['keyword', 'class']: fmt.setFontWeight(QFont.Bold)
            if tag == 'comment': fmt.setFontItalic(True)
            self.formats[tag] = fmt

    def highlightBlock(self, text):
        try:
            options = {}
            if 'php' in self.language: options['startinline'] = True
            lexer = get_lexer_by_name(self.language, **options)
        except ClassNotFound: return

        self.setFormat(0, len(text), QTextCharFormat()) 
        text_index = 0
        for token_type, value in lexer.get_tokens(text):
            tag_name = self._get_tag_for_token(token_type)
            if tag_name and tag_name in self.formats:
                self.setFormat(text_index, len(value), self.formats[tag_name])
            text_index += len(value)

    def _get_tag_for_token(self, token_type):
        if token_type in Token.Name.Variable: return "variable"
        if token_type in Token.Keyword.Type: return "class"
        if token_type in Token.Operator.Word: return "keyword"
        if token_type in Token.Name.Builtin: return "function"
        if token_type in Token.Keyword: return "keyword"
        if token_type in Token.Keyword.Declaration: return "keyword"
        if token_type in Token.Literal.String: return "string"
        if token_type in Token.Literal.Number: return "number"
        if token_type in Token.Comment: return "comment"
        if token_type in Token.Name.Class: return "class"
        if token_type in Token.Name.Function: return "function"
        if token_type in Token.Operator or token_type in Token.Punctuation: return "operator"
        if token_type in Token.Name.Decorator: return "function"
        return None

    def set_language(self, language):
        self.language = language
        self.rehighlight()

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.setup_formats()
        self.rehighlight()

class SearchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setVisible(False)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setStyleSheet("background-color: #252526; border-top: 1px solid #3e3e42;")
        
        self.label_find = QLabel("Buscar:")
        self.label_find.setStyleSheet("color: #cccccc; border: none;")
        self.input_find = QLineEdit()
        self.input_find.setStyleSheet("background-color: #3c3c3c; color: white; border: 1px solid #3e3e42;")
        self.input_find.setFixedWidth(200)
        self.input_find.returnPressed.connect(lambda: self.parent().parent().find_text(True))
        
        self.btn_next = QPushButton("↓")
        self.btn_prev = QPushButton("↑")
        self.btn_next.setFixedWidth(30); self.btn_prev.setFixedWidth(30)
        
        self.label_replace = QLabel("Reemplazar:")
        self.label_replace.setStyleSheet("color: #cccccc; border: none; margin-left: 10px;")
        self.input_replace = QLineEdit()
        self.input_replace.setStyleSheet("background-color: #3c3c3c; color: white; border: 1px solid #3e3e42;")
        self.input_replace.setFixedWidth(200)
        
        self.btn_replace = QPushButton("Reemplazar")
        self.btn_replace_all = QPushButton("Todo")
        
        style = "QPushButton { background-color: #0e639c; color: white; border: none; padding: 4px; } QPushButton:hover { background-color: #1177bb; }"
        for btn in [self.btn_next, self.btn_prev, self.btn_replace, self.btn_replace_all]: btn.setStyleSheet(style)
        
        self.btn_close = QPushButton("X")
        self.btn_close.setStyleSheet("background-color: transparent; color: #cccccc; font-weight: bold; border: none;")
        self.btn_close.clicked.connect(self.hide)

        layout.addWidget(self.label_find); layout.addWidget(self.input_find)
        layout.addWidget(self.btn_prev); layout.addWidget(self.btn_next)
        layout.addWidget(self.label_replace); layout.addWidget(self.input_replace)
        layout.addWidget(self.btn_replace); layout.addWidget(self.btn_replace_all)
        layout.addStretch(); layout.addWidget(self.btn_close)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    def sizeHint(self): return QSize(self.editor.lineNumberAreaWidth(), 0)
    def paintEvent(self, event): self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit): 
    def __init__(self, parent=None, theme_name="Dark", font_size=12, tab_width=4):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.highlighter = PySideHighlighter(self.document(), "text", theme_name)
        self.theme_name = theme_name; self.font_size = font_size; self.tab_width = tab_width
        self.autocompleter = AutoCompleter(self); self.autocompleter.setup("text")
        self.update_font_settings(); self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0); self.apply_theme(theme_name)

    def keyPressEvent(self, event):
        if self.autocompleter.completer and self.autocompleter.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore(); return
        if (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space):
            self.show_completion(); return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            indentation = ""
            for char in self.textCursor().block().text():
                if char in [' ', '\t']: indentation += char
                else: break
            if self.textCursor().block().text().rstrip().endswith((':', '{', '(')): indentation += "    " 
            super().keyPressEvent(event); self.insertPlainText(indentation); return
        super().keyPressEvent(event)
        if event.text().strip(): self.show_completion()

    def show_completion(self):
        prefix = self.textCursor().selectedText() or self.textCursor().block().text().split()[-1] if self.textCursor().block().text().split() else ""
        if len(prefix) < 1: self.autocompleter.completer.popup().hide(); return
        if prefix != self.autocompleter.completer.completionPrefix():
            self.autocompleter.completer.setCompletionPrefix(prefix)
            self.autocompleter.completer.popup().setCurrentIndex(self.autocompleter.completer.completionModel().index(0, 0))
        cr = self.cursorRect()
        cr.setWidth(self.autocompleter.completer.popup().sizeHintForColumn(0) + self.autocompleter.completer.popup().verticalScrollBar().sizeHint().width())
        self.autocompleter.completer.complete(cr)

    def update_font_settings(self):
        font = QFont("Consolas", self.font_size); self.setFont(font)
        self.setTabStopDistance(self.tab_width * QFontMetricsF(font).horizontalAdvance(' '))

    def lineNumberAreaWidth(self):
        digits = 1; max_value = max(1, self.blockCount())
        while max_value >= 10: max_value /= 10; digits += 1
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy: self.lineNumberArea.scroll(0, dy)
        else: self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()): self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        colors = THEMES.get(self.theme_name, THEMES['Dark'])
        painter.fillRect(event.rect(), QColor(colors['line_bg'])) 
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(colors['fg'] if blockNumber == self.textCursor().block().blockNumber() else colors['line_fg']))
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, int(self.fontMetrics().height()), Qt.AlignRight, str(blockNumber + 1))
            block = block.next(); top = bottom; bottom = top + self.blockBoundingRect(block).height(); blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(THEMES.get(self.theme_name, THEMES['Dark'])['select_bg']).darker(110))
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor(); selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def apply_theme(self, theme_name):
        self.theme_name = theme_name
        c = THEMES.get(theme_name, THEMES['Dark'])
        self.setStyleSheet(f"QPlainTextEdit {{ background-color: {c['bg']}; color: {c['fg']}; selection-background-color: {c['select_bg']}; selection-color: {c['fg']}; }}")
        self.highlighter.set_theme(theme_name); self.highlightCurrentLine()

class EditorTab(QWidget):
    def __init__(self, parent, file_path=None, content="", theme_name="Dark", font_size=12, tab_width=4, show_minimap=True):
        super().__init__(parent)
        self.file_path = file_path; self.saved = True; self.is_welcome = False
        layout = QHBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        
        self.editor = CodeEditor(self, theme_name, font_size, tab_width)
        self.editor.setPlainText(content)
        
        self.minimap = CodeMinimap(self.editor)
        self.minimap.sync_with_parent()
        self.minimap.setVisible(show_minimap)
        
        colors = THEMES.get(theme_name, THEMES['Dark'])
        self.minimap.apply_theme(colors)
        
        layout.addWidget(self.editor); layout.addWidget(self.minimap)
        self.editor.textChanged.connect(self.mark_as_modified)
        self.editor.textChanged.connect(self.minimap.sync_with_parent)
        self.editor.verticalScrollBar().valueChanged.connect(lambda v: self.minimap.update_scroll(v, self.editor.verticalScrollBar().maximum()))

    def get_title(self): return os.path.basename(self.file_path) if self.file_path else "Sin título"
    def mark_as_modified(self):
        if self.saved:
            self.saved = False
            try: self.window().update_tab_title(self)
            except: pass

class ShortcutsDialog(QDialog):
    def __init__(self, shortcuts_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atajos"); self.setMinimumSize(600, 450)
        self.setStyleSheet("QDialog { background-color: #1e1e1e; color: white; } QTableWidget { background-color: #252526; color: white; }")
        layout = QVBoxLayout(self)
        self.table = QTableWidget(); self.table.setColumnCount(3); self.table.setHorizontalHeaderLabels(["Categoría", "Acción", "Atajo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, item in enumerate(shortcuts_data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item.get("category", "General")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("action", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("keys", "")))
        layout.addWidget(self.table)

# =========================================================================
#  APP PRINCIPAL
# =========================================================================

class PySideEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "Dark"; self.font_size = 12; self.tab_width = 4
        self.root_dir = os.getcwd(); self.autosave_enabled = True; self.minimap_enabled = True
        self.config_data = self._load_config()
        
        # Titulo desde config
        app_name = self.config_data.get('app_settings', {}).get('app_name', 'Editor Capi')
        app_ver = self.config_data.get('app_settings', {}).get('app_version', 'v1.8')
        self.setWindowTitle(f"{app_name} {app_ver}")
        self.setGeometry(100, 100, 1000, 600)
        
        self.setup_ui(); self.setup_status_bar(); self.create_actions(); self.create_menus(); self.load_session()
        self.autosave_timer = QTimer(self); self.autosave_timer.timeout.connect(self.perform_autosave); self.autosave_timer.start(2000)
        if self.notebook.count() == 0: self.show_welcome_tab()

    def _load_config(self):
        path = resource_path(CONFIG_FILE)
        # --- FIX: CARGA SEGURA PARA EVITAR CRASH SI EL JSON TIENE ERRORES ---
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando config: {e}")
        return {
            "app_settings": {"app_name": "Editor Capi", "app_version": "v1.8"},
            "welcome_screen": {"welcome_title": "Bienvenido", "features_list": []},
            "shortcuts_guide": []
        }

    def setup_ui(self):
        main_splitter = QSplitter(Qt.Horizontal); self.setCentralWidget(main_splitter)
        self.file_model = EmojiFileSystemModel()
        # --- FIX: ESTABLECER ROOTPATH GENERAL PARA QUE EL ÁRBOL CARGUE CORRECTAMENTE ---
        self.file_model.setRootPath(QDir.rootPath()) 
        self.tree_view = FileSidebar(self); self.tree_view.setModel(self.file_model)
        # --- FIX: MOSTRAR CARPETA RAÍZ EN EL ÁRBOL ---
        self.update_sidebar_root(self.root_dir)
        
        for i in range(1, self.file_model.columnCount()): self.tree_view.hideColumn(i)
        self.tree_view.clicked.connect(lambda idx: self._open_file(self.file_model.filePath(idx)) if os.path.isfile(self.file_model.filePath(idx)) else None)
        self.tree_view.setFixedWidth(250)
        main_splitter.addWidget(self.tree_view)

        self.editor_console_splitter = QSplitter(Qt.Vertical); main_splitter.addWidget(self.editor_console_splitter)
        self.notebook = QTabWidget(); self.notebook.setTabsClosable(True)
        self.notebook.tabCloseRequested.connect(self.close_tab)
        self.notebook.currentChanged.connect(self.on_tab_change)
        self.editor_console_splitter.addWidget(self.notebook)

        self.search_widget = SearchWidget(self)
        self.editor_console_splitter.addWidget(self.search_widget)

        self.console = EditorTerminal(self, THEMES['Dark']); self.console.hide()
        self.editor_console_splitter.addWidget(self.console)
        self.editor_console_splitter.setStretchFactor(0, 1)

    def update_sidebar_root(self, path):
        """
        Actualiza el sidebar para mostrar SOLO la carpeta del proyecto.
        Usa un QTimer para esperar a que el modelo cargue los archivos del disco.
        """
        if not path or not os.path.exists(path):
            return

        self.root_dir = path
        parent_dir = os.path.dirname(path)
        
        # 1. Establecemos la ruta en el modelo y la raíz visual en el padre
        self.file_model.setRootPath(parent_dir)
        parent_idx = self.file_model.index(parent_dir)
        self.tree_view.setRootIndex(parent_idx)

        # 2. Función interna que aplicará el filtro una vez cargados los datos
        def apply_filter():
            model = self.tree_view.model()
            # Iteramos por los elementos del padre (Escritorio)
            for i in range(model.rowCount(parent_idx)):
                child_idx = model.index(i, 0, parent_idx)
                child_path = model.filePath(child_idx)
                
                # Si el archivo/carpeta no es nuestro proyecto, lo escondemos
                if child_path != path:
                    self.tree_view.setRowHidden(i, parent_idx, True)
                else:
                    self.tree_view.setRowHidden(i, parent_idx, False)
            
            # Expandimos automáticamente nuestra carpeta de proyecto
            self.tree_view.expand(self.file_model.index(path))

        # 3. Ejecutamos el filtro con un pequeño retraso (200 milisegundos)
        # Esto evita que rowCount devuelva 0 al darle tiempo al modelo a cargar.
        QTimer.singleShot(200, apply_filter)
        """Actualiza el sidebar para que muestre SOLO la carpeta del proyecto."""
        if not path or not os.path.exists(path): return
        
        # Obtenemos el padre para que la carpeta del proyecto sea visible como nodo
        parent_dir = os.path.dirname(path)
        parent_idx = self.file_model.index(parent_dir)
        self.tree_view.setRootIndex(parent_idx)
        
        # Filtro: Escondemos todo lo que no sea nuestro proyecto en el Escritorio
        model = self.tree_view.model()
        for i in range(model.rowCount(parent_idx)):
            child_idx = model.index(i, 0, parent_idx)
            child_path = model.filePath(child_idx)
            if child_path != path:
                self.tree_view.setRowHidden(i, parent_idx, True)
            else:
                self.tree_view.setRowHidden(i, parent_idx, False)

        self.tree_view.expand(self.file_model.index(path))
        self.root_dir = path

    def toggle_console(self):
        if self.console.isVisible(): self.console.hide()
        else:
            self.console.show()
            sizes = self.editor_console_splitter.sizes()
            total = sum(sizes)
            self.editor_console_splitter.setSizes([total - sizes[1] - 150, sizes[1], 150])

    def setup_status_bar(self):
        self.status_bar = self.statusBar(); self.status_bar.setStyleSheet("background-color: #007acc; color: white;")
        self.lbl_cursor = QLabel("Ln 1, Col 1"); self.status_bar.addPermanentWidget(self.lbl_cursor)
    
    def update_status_bar(self):
        t = self.notebook.currentWidget()
        if t and not t.is_welcome:
            c = t.editor.textCursor()
            self.lbl_cursor.setText(f"Ln {c.blockNumber()+1}, Col {c.columnNumber()+1}")

    def create_actions(self):
        self.new_action = QAction("Nuevo Archivo", self, shortcut="Ctrl+N", triggered=lambda: self.add_new_tab())
        self.new_folder_action = QAction("Nueva Carpeta...", self, triggered=self.create_new_folder_global)
        self.open_folder_action = QAction("Abrir Carpeta...", self, triggered=self.select_folder)
        self.open_action = QAction("Abrir Archivo...", self, shortcut="Ctrl+O", triggered=lambda: self._open_file())
        self.save_action = QAction("Guardar", self, shortcut="Ctrl+S", triggered=self.save_current_file)
        self.save_as_action = QAction("Guardar como...", self, triggered=self.save_file_as)
        self.exit_action = QAction("Salir", self, shortcut="Ctrl+Q", triggered=self.close)
        
        self.undo_act = QAction("Deshacer", self, shortcut="Ctrl+Z", triggered=lambda: self.notebook.currentWidget().editor.undo() if self.notebook.currentWidget() else None)
        self.redo_act = QAction("Rehacer", self, shortcut="Ctrl+Y", triggered=lambda: self.notebook.currentWidget().editor.redo() if self.notebook.currentWidget() else None)
        self.cut_act = QAction("Cortar", self, shortcut="Ctrl+X", triggered=lambda: self.notebook.currentWidget().editor.cut() if self.notebook.currentWidget() else None)
        self.copy_act = QAction("Copiar", self, shortcut="Ctrl+C", triggered=lambda: self.notebook.currentWidget().editor.copy() if self.notebook.currentWidget() else None)
        self.paste_act = QAction("Pegar", self, shortcut="Ctrl+V", triggered=lambda: self.notebook.currentWidget().editor.paste() if self.notebook.currentWidget() else None)
        self.sel_all_act = QAction("Seleccionar Todo", self, shortcut="Ctrl+A", triggered=lambda: self.notebook.currentWidget().editor.selectAll() if self.notebook.currentWidget() else None)
        
        self.find_act = QAction("Buscar y Reemplazar", self, shortcut="Ctrl+F", triggered=self.toggle_search)
        self.goto_line_action = QAction("Ir a Línea...", self, shortcut="Ctrl+G", triggered=self.go_to_line)
        
        self.run_act = QAction("Ejecutar Archivo", self, shortcut="F5", triggered=self.run_current_file)
        self.console_act = QAction("Mostrar/Ocultar Terminal", self, triggered=self.toggle_console)
        
        self.toggle_minimap_action = QAction("Mostrar/Ocultar Minimapa", self, triggered=self.toggle_minimap_global)
        self.autosave_action = QAction("Activar Auto-Guardado", self, checkable=True)
        self.autosave_action.setChecked(self.autosave_enabled)
        self.autosave_action.triggered.connect(self.toggle_autosave)
        
        self.shortcuts_action = QAction("Ver Lista de Atajos", self, shortcut="Ctrl+Shift+B", triggered=self.show_shortcuts_dialog)

    def create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        file_menu.addAction(self.new_action); file_menu.addAction(self.new_folder_action); file_menu.addSeparator()
        file_menu.addAction(self.open_folder_action); file_menu.addAction(self.open_action); file_menu.addSeparator()
        file_menu.addAction(self.save_action); file_menu.addAction(self.save_as_action); file_menu.addSeparator(); file_menu.addAction(self.exit_action)

        edit_menu = menu_bar.addMenu("&Editar")
        edit_menu.addAction(self.undo_act); edit_menu.addAction(self.redo_act); edit_menu.addSeparator()
        edit_menu.addAction(self.cut_act); edit_menu.addAction(self.copy_act); edit_menu.addAction(self.paste_act); edit_menu.addSeparator()
        edit_menu.addAction(self.sel_all_act); edit_menu.addSeparator(); edit_menu.addAction(self.find_act); edit_menu.addAction(self.goto_line_action)
        
        view_menu = menu_bar.addMenu("&Ver")
        view_menu.addAction(self.toggle_minimap_action)
        
        settings_menu = menu_bar.addMenu("&Configuración")
        settings_menu.addAction(self.autosave_action); settings_menu.addSeparator()
        
        font_menu = settings_menu.addMenu("Tamaño de Fuente")
        font_group = QActionGroup(self)
        for size in [10, 12, 14, 16, 18, 20]:
            action = font_menu.addAction(f"{size} pt"); action.setCheckable(True)
            if size == self.font_size: action.setChecked(True)
            action.triggered.connect(lambda c, s=size: self.change_font_size(s))
            font_group.addAction(action)

        tab_menu = settings_menu.addMenu("Ancho de Tabulación")
        tab_group = QActionGroup(self)
        for width in [2, 4, 8]:
            action = tab_menu.addAction(f"{width} Espacios"); action.setCheckable(True)
            if width == self.tab_width: action.setChecked(True)
            action.triggered.connect(lambda c, w=width: self.change_tab_width(w))
            tab_group.addAction(action)

        run_menu = menu_bar.addMenu("&Ejecutar")
        run_menu.addAction(self.run_act); run_menu.addAction(self.console_act)
            
        theme_menu = menu_bar.addMenu("&Tema")
        for theme_name in THEMES:
            action = theme_menu.addAction(theme_name)
            action.triggered.connect(lambda checked, name=theme_name: self.apply_theme(name))

        help_menu = menu_bar.addMenu("&Ayuda")
        help_menu.addAction(self.shortcuts_action)

    def toggle_search(self):
        if self.search_widget.isVisible(): self.search_widget.hide()
        else: self.search_widget.show(); self.search_widget.input_find.setFocus()

    def find_text(self, forward=True):
        t = self.notebook.currentWidget()
        if not t: return
        flag = QTextEdit.FindFlags()
        if not forward: flag |= QTextEdit.FindBackward
        if not t.editor.find(self.search_widget.input_find.text(), flag):
            c = t.editor.textCursor(); c.movePosition(QTextCursor.Start if forward else QTextCursor.End)
            t.editor.setTextCursor(c); t.editor.find(self.search_widget.input_find.text(), flag)

    def replace_text(self):
        t = self.notebook.currentWidget()
        if t and t.editor.textCursor().hasSelection(): t.editor.insertPlainText(self.search_widget.input_replace.text())
        self.find_text()

    def replace_all_text(self):
        t = self.notebook.currentWidget()
        if t: t.editor.setPlainText(t.editor.toPlainText().replace(self.search_widget.input_find.text(), self.search_widget.input_replace.text()))

    def add_new_tab(self, file_path=None, content=""):
        if self.notebook.count() == 1 and isinstance(self.notebook.widget(0), EditorTab) and self.notebook.widget(0).is_welcome:
            self.notebook.removeTab(0)
        
        tab = EditorTab(self.notebook, file_path, content, self.current_theme, self.font_size, self.tab_width, self.minimap_enabled)
        
        title_text = f"{get_tab_emoji(file_path)} {os.path.basename(file_path) if file_path else 'Sin título'}"
        idx = self.notebook.addTab(tab, title_text)
        self.notebook.setCurrentIndex(idx)
        
        tab.editor.cursorPositionChanged.connect(self.update_status_bar)
        
        if file_path:
            try: 
                lexer = get_lexer_for_filename(file_path)
                tab.editor.highlighter.set_language(lexer.aliases[0])
            except: pass
            
            key_for_json = get_keyword_key(file_path)
            tab.editor.autocompleter.update_model(key_for_json)
            
        return tab

    def show_welcome_tab(self):
        welcome_info = self.config_data.get('welcome_screen', {})
        txt = welcome_info.get('welcome_title', "Bienvenido") + "\n\n"
        txt += "\n".join(welcome_info.get('features_list', []))
        
        tab = EditorTab(self.notebook, content=txt, theme_name=self.current_theme)
        tab.is_welcome = True; tab.editor.setReadOnly(True)
        self.notebook.addTab(tab, "Inicio")

    def close_tab(self, index):
        tab = self.notebook.widget(index)
        if not tab.saved and not tab.is_welcome:
            if QMessageBox.warning(self, "Guardar", "Archivo no guardado. ¿Desea guardarlo?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                if not self.save_current_file(): return
        self.notebook.removeTab(index)

    def on_tab_change(self, index):
        t = self.notebook.currentWidget()
        if t: 
            self.update_tab_title(t); self.update_status_bar()
            t.editor.apply_theme(self.current_theme)

    def update_tab_title(self, tab):
        idx = self.notebook.indexOf(tab)
        if idx != -1: self.notebook.setTabText(idx, f"{'*' if not tab.saved else ''}{get_tab_emoji(tab.file_path)} {tab.get_title()}")

    def _open_file(self, path=None):
        if not path: path, _ = QFileDialog.getOpenFileName(self, "Abrir")
        if not path: return
        for i in range(self.notebook.count()):
            if self.notebook.widget(i).file_path == path: self.notebook.setCurrentIndex(i); return
        try:
            with open(path, 'r', encoding='utf-8') as f: self.add_new_tab(path, f.read())
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def save_current_file(self):
        t = self.notebook.currentWidget()
        if not t or t.is_welcome: return
        if t.file_path: return self._write_file(t.file_path, t.editor.toPlainText())
        return self.save_file_as()

    def save_file_as(self):
        t = self.notebook.currentWidget()
        if not t or t.is_welcome: return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar como...", t.get_title())
        if path:
            t.file_path = path
            self._write_file(path, t.editor.toPlainText())
            self.update_tab_title(t)
            try: t.editor.highlighter.set_language(get_lexer_for_filename(path).aliases[0])
            except: pass
            key_for_json = get_keyword_key(path)
            t.editor.autocompleter.update_model(key_for_json)
            return True
        return False

    def _write_file(self, path, content):
        try:
            with open(path, 'w', encoding='utf-8') as f: f.write(content)
            self.notebook.currentWidget().saved = True
            self.update_tab_title(self.notebook.currentWidget())
            return True
        except Exception as e: QMessageBox.critical(self, "Error", str(e)); return False

    def run_current_file(self):
        self.save_current_file()
        t = self.notebook.currentWidget()
        if t and t.file_path:
            if not self.console.isVisible(): self.toggle_console()
            self.console.run_script(t.file_path)

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        colors = THEMES.get(theme_name, THEMES['Dark'])
        self.console.update_theme(colors)
        if hasattr(self, 'tree_view'): self.tree_view.update_theme(colors)
        for i in range(self.notebook.count()): 
            tab = self.notebook.widget(i)
            if isinstance(tab, EditorTab):
                tab.editor.apply_theme(theme_name)
                # --- FIX: ACTUALIZAR TEMA DEL MINIMAPA ---
                tab.minimap.apply_theme(colors)
        self.save_session()
    
    def perform_autosave(self):
        t = self.notebook.currentWidget()
        if t and t.file_path and not t.saved: self._write_file(t.file_path, t.editor.toPlainText())

    def toggle_autosave(self, checked):
        self.autosave_enabled = checked
        if checked: self.autosave_timer.start(2000)
        else: self.autosave_timer.stop()

    def toggle_minimap_global(self):
        self.minimap_enabled = not self.minimap_enabled
        for i in range(self.notebook.count()):
            widget = self.notebook.widget(i)
            if isinstance(widget, EditorTab):
                widget.minimap.setVisible(self.minimap_enabled)
        self.save_session()

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", self.root_dir)
        if path:
            self.update_sidebar_root(path)
            self.save_session()

    def create_new_folder_global(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            path = self.file_model.filePath(index)
            is_dir = self.file_model.isDir(index)
        else: path = self.root_dir; is_dir = True
        self.tree_view.create_item(path if is_dir else os.path.dirname(path), "folder")

    def change_font_size(self, size): self.font_size = size; self.update_all_editors()
    def change_tab_width(self, width): self.tab_width = width; self.update_all_editors()
    def update_all_editors(self):
        for i in range(self.notebook.count()):
            widget = self.notebook.widget(i)
            if isinstance(widget, EditorTab):
                widget.editor.font_size = self.font_size; widget.editor.tab_width = self.tab_width; widget.editor.update_font_settings()
        self.save_session()
    
    def go_to_line(self):
        tab = self.notebook.currentWidget()
        if not tab: return
        max_lines = tab.editor.blockCount()
        line_num, ok = QInputDialog.getInt(self, "Ir a Línea", f"Número de línea (1 - {max_lines}):", 1, 1, max_lines, 1)
        if ok:
            cursor = tab.editor.textCursor()
            cursor.setPosition(0)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_num - 1)
            tab.editor.setTextCursor(cursor)
            tab.editor.centerCursor()
            tab.editor.setFocus()

    def show_shortcuts_dialog(self):
        shortcuts = self.config_data.get("shortcuts_guide", [])
        dialog = ShortcutsDialog(shortcuts, self)
        dialog.exec()

    def save_session(self):
        open_files = []
        for i in range(self.notebook.count()):
            widget = self.notebook.widget(i)
            if isinstance(widget, EditorTab) and widget.file_path and not widget.is_welcome:
                open_files.append(widget.file_path)
        
        data = {
            "root_dir": self.root_dir,
            "open_files": open_files,
            "theme": self.current_theme,
            "font_size": self.font_size,
            "tab_width": self.tab_width,
            "minimap_enabled": self.minimap_enabled
        }
        
        try:
            path = get_data_path(SESSION_FILE)
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception: pass

    def load_session(self):
        path = get_data_path(SESSION_FILE)
        if not os.path.exists(path): return
        try:
            with open(path, 'r') as f: data = json.load(f)
            
            self.font_size = data.get('font_size', 12)
            self.tab_width = data.get('tab_width', 4)
            self.current_theme = data.get('theme', 'Dark')
            self.minimap_enabled = data.get('minimap_enabled', True)
            
            self.apply_theme(self.current_theme)
            
            if 'root_dir' in data and os.path.isdir(data['root_dir']):
                self.update_sidebar_root(data['root_dir'])
            
            if 'open_files' in data:
                for file_path in data['open_files']:
                    if os.path.exists(file_path):
                        self._open_file(file_path)
        except Exception: pass
    
    def closeEvent(self, event):
        self.save_session()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = PySideEditor()
    editor.show()
    sys.exit(app.exec())