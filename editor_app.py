import sys, os, json, shutil
from PySide6.QtCore import (Qt, QTimer, QDir, QSize, QRect, QPoint, QModelIndex, QUrl)
from PySide6.QtGui import (QAction, QColor, QTextCharFormat, QFont, QFontMetricsF,
                           QSyntaxHighlighter, QTextCursor, QPainter, QTextDocument, 
                           QIcon, QPixmap, QTextFormat, QCloseEvent, QDesktopServices) 
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPlainTextEdit, QSplitter, QFileDialog, QMessageBox, 
                               QTabWidget, QMenu, QInputDialog, QLabel, QDialog, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QTextEdit, QSizePolicy, QFrame, QAbstractItemView)

# --- IMPORTS DE PYGMENTS ---
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound

try:
    from utils import THEMES, resource_path
    from terminal import EditorTerminal
    from autocomplete import AutoCompleter
    from minimap import CodeMinimap
    from search_module import SearchWidget, GlobalSearchDialog
    from menu_module import MenuBuilder
    from sidebar_module import ProjectSidebarWrapper
except ImportError as e:
    print(f"Error crítico en módulos base: {e}"); sys.exit(1)

# --- IMPORT DE ATAJOS SEGURO ---
try:
    from shortcuts import SHORTCUTS_DATA
except ImportError:
    print("Advertencia: shortcuts.py no encontrado. Usando datos por defecto.")
    SHORTCUTS_DATA = {"Error": [("No se encontró shortcuts.py", "Revise la carpeta")]}

CONFIG_FILE = "config.json"

# =========================================================================
#  1. CLASES AUXILIARES (Editor, Dialogos)
# =========================================================================

# --- CLASE CORREGIDA: SHORTCUTS DIALOG ---
class ShortcutsDialog(QDialog):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Referencia de Atajos")
        self.resize(500, 600)
        
        # --- FIX KEYERROR: Extraer 'tags' de forma segura ---
        # Si 'tags' no existe (por si acaso), usamos un diccionario vacío
        tags = colors.get('tags', {}) 
        
        # Definimos colores seguros (Fallback si falla el tema)
        kw_color = tags.get('keyword', colors.get('fg', '#ffffff')) 
        str_color = tags.get('string', '#ffff00')
        
        # Estilo del Diálogo
        self.setStyleSheet(f"""
            QDialog {{ background-color: {colors['window_bg']}; color: {colors['fg']}; }}
            QTableWidget {{ background-color: {colors['bg']}; color: {colors['fg']}; border: 1px solid {colors['splitter']}; gridline-color: {colors['line_bg']}; }}
            QHeaderView::section {{ background-color: {colors['line_bg']}; color: {colors['fg']}; padding: 4px; border: none; }}
            QLabel {{ font-weight: bold; font-size: 16px; margin-bottom: 10px; color: {kw_color}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⌨️ Atajos de Teclado"))
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Acción", "Atajo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        # Pasamos 'tags' explícitamente a populate_table
        self.populate_table(colors, tags, kw_color, str_color)
        layout.addWidget(self.table)
        
        btn = QPushButton("Cerrar")
        btn.clicked.connect(self.accept)
        btn.setStyleSheet(f"background-color: {colors['line_bg']}; color: {colors['fg']}; border: none; padding: 8px; font-weight: bold;")
        layout.addWidget(btn)

    def populate_table(self, colors, tags, kw_color, str_color):
        row = 0
        for category, items in SHORTCUTS_DATA.items():
            self.table.insertRow(row)
            self.table.setSpan(row, 0, 1, 2) 
            cat_item = QTableWidgetItem(category)
            cat_item.setTextAlignment(Qt.AlignCenter)
            cat_item.setBackground(QColor(colors['line_bg']))
            # Usamos el color corregido
            cat_item.setForeground(QColor(kw_color))
            cat_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, cat_item)
            row += 1
            for action, keys in items:
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(action))
                key_item = QTableWidgetItem(keys)
                key_item.setTextAlignment(Qt.AlignCenter)
                # Usamos el color corregido
                key_item.setForeground(QColor(str_color))
                self.table.setItem(row, 1, key_item)
                row += 1

# =========================================================================
#  CLASE ACTUALIZADA: ABOUT DIALOG
# =========================================================================
class AboutDialog(QDialog):
    def __init__(self, config, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de")
        self.setFixedSize(400, 400)
        
        # 1. Extraer info del config.json de forma segura
        info = config.get("about", {})
        app_name = info.get("app_name", "CAPI EDITOR")
        version = info.get("version", "v1.0.8 Gold")
        desc = info.get("description", "Editor modular potente.")
        author = info.get("author", "Decerone")
        year = info.get("year", "2026")
        icon_file = info.get("icon_name", "icon.png")

        # 2. Extracción segura de colores de sintaxis desde el diccionario modular
        # Buscamos en 'tags', si no existe usamos fallbacks
        tags = colors.get('tags', {})
        kw_color = tags.get('keyword', colors.get('fg', '#569cd6'))
        str_color = tags.get('string', '#ce9178')
        comment_color = tags.get('comment', '#6a9955')

        # 3. Estilo CSS dinámico basado en el tema actual
        self.setStyleSheet(f"""
            QDialog {{ background-color: {colors['window_bg']}; color: {colors['fg']}; border: 1px solid {colors['splitter']}; }}
            QLabel {{ color: {colors['fg']}; }}
            QLabel#title {{ font-size: 20px; font-weight: bold; color: {kw_color}; }}
            QLabel#version {{ font-size: 12px; color: {str_color}; font-style: italic; }}
            QPushButton {{ 
                background-color: {colors['line_bg']}; 
                color: {colors['fg']}; 
                border: 1px solid {colors['splitter']}; 
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {colors['select_bg']}; color: white; }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # 4. Carga de Icono (Uso de la función global de forma explícita)
        try:
            # Importamos aquí localmente por si la referencia global falla
            from utils import resource_path
            path_al_icono = resource_path(icon_file)
            
            if os.path.exists(path_al_icono):
                lbl_icon = QLabel()
                pix = QPixmap(path_al_icono)
                lbl_icon.setPixmap(pix.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl_icon.setAlignment(Qt.AlignCenter)
                layout.addWidget(lbl_icon)
        except Exception as e:
            print(f"No se pudo cargar el icono en 'Acerca de': {e}")

        # 5. Componentes de Texto
        lbl_title = QLabel(app_name)
        lbl_title.setObjectName("title")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_ver = QLabel(f"Edición: {version}")
        lbl_ver.setObjectName("version")
        lbl_ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_ver)

        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setStyleSheet("margin: 5px 30px;")
        layout.addWidget(lbl_desc)

        lbl_copy = QLabel(f"© {year} {author}")
        lbl_copy.setAlignment(Qt.AlignCenter)
        lbl_copy.setStyleSheet(f"color: {comment_color}; font-size: 11px;")
        layout.addWidget(lbl_copy)

        # 6. Botón de Cierre
        layout.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)
        layout.addSpacing(15)

class LineNumberArea(QWidget):
    def __init__(self, editor): super().__init__(editor); self.editor = editor
    def sizeHint(self): return QSize(self.editor.line_number_area_width(), 0)
    def paintEvent(self, event): self.editor.lineNumberAreaPaintEvent(event)

class PySideHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, language="text", theme_name="Dark"):
        super().__init__(parent); self.language = language; self.theme_name = theme_name; self.formats = {}; self.setup_formats()
    def setup_formats(self):
        colors = THEMES.get(self.theme_name, THEMES['Dark'])['tags']
        self.formats = {}
        for tag, hex_color in colors.items():
            fmt = QTextCharFormat(); fmt.setForeground(QColor(hex_color))
            if tag in ['keyword', 'class']: fmt.setFontWeight(QFont.Bold)
            if tag == 'comment': fmt.setFontItalic(True)
            self.formats[tag] = fmt
    def highlightBlock(self, text):
        try:
            options = {}
            if 'php' in self.language: options['startinline'] = True
            try: lexer = get_lexer_by_name(self.language, **options)
            except ClassNotFound: lexer = get_lexer_by_name("text")
        except: return
        self.setFormat(0, len(text), QTextCharFormat()); text_index = 0
        for token_type, value in lexer.get_tokens(text):
            tag_name = self._get_tag_for_token(token_type); length = len(value)
            if tag_name and tag_name in self.formats: self.setFormat(text_index, length, self.formats[tag_name])
            text_index += length
    def _get_tag_for_token(self, token_type):
        if token_type in Token.Keyword: return "keyword"
        if token_type in Token.Name.Builtin: return "keyword"
        if token_type in Token.Literal.String: return "string"
        if token_type in Token.Literal.Number: return "number"
        if token_type in Token.Comment: return "comment"
        if token_type in Token.Name.Function: return "function"
        if token_type in Token.Name.Class: return "class"
        if token_type in Token.Operator: return "keyword"
        return None
    def set_language(self, l): self.language = l; self.rehighlight()
    def set_theme(self, t): self.theme_name = t; self.setup_formats(); self.rehighlight()

class CodeEditor(QPlainTextEdit): 
    def __init__(self, parent, theme, size, tabs):
        super().__init__(parent)
        self.theme_name = theme
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PySideHighlighter(self.document(), "text", theme)
        self.autocompleter = AutoCompleter(self); self.autocompleter.setup("text")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.update_font(size, tabs)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0); self.apply_theme(theme)
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        undo = menu.addAction("↩️ Deshacer"); undo.triggered.connect(self.undo); undo.setEnabled(self.document().isUndoAvailable())
        redo = menu.addAction("↪️ Rehacer"); redo.triggered.connect(self.redo); redo.setEnabled(self.document().isRedoAvailable())
        menu.addSeparator()
        cut = menu.addAction("✂️ Cortar"); cut.triggered.connect(self.cut); cut.setEnabled(self.textCursor().hasSelection())
        copy = menu.addAction("📋 Copiar"); copy.triggered.connect(self.copy); copy.setEnabled(self.textCursor().hasSelection())
        paste = menu.addAction("📥 Pegar"); paste.triggered.connect(self.paste); paste.setEnabled(self.canPaste())
        menu.addSeparator(); menu.addAction("🔍 Seleccionar Todo", self.selectAll); menu.exec(event.globalPos())
    def line_number_area_width(self):
        digits = 1; max_num = max(1, self.blockCount())
        while max_num >= 10: max_num //= 10; digits += 1
        return 40 + self.fontMetrics().horizontalAdvance('9') * digits
    def update_line_number_area_width(self, _): self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    def update_line_number_area(self, rect, dy):
        if dy: self.line_number_area.scroll(0, dy)
        else: self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()): self.update_line_number_area_width(0)
    def resizeEvent(self, event): super().resizeEvent(event); cr = self.contentsRect(); self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area); c = THEMES.get(self.theme_name, THEMES['Dark']); painter.fillRect(event.rect(), QColor(c['line_bg']))
        block = self.firstVisibleBlock(); block_number = block.blockNumber(); top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top(); bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(c['line_fg'])); painter.drawText(0, int(top), self.line_number_area.width()-5, self.fontMetrics().height(), Qt.AlignRight, str(block_number+1))
            block = block.next(); top = bottom; bottom = top + self.blockBoundingRect(block).height(); block_number += 1
    def highlight_current_line(self):
        extra = []; 
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection(); sel.format.setBackground(QColor(THEMES.get(self.theme_name, THEMES['Dark'])['line_bg']).lighter(120)); sel.format.setProperty(QTextFormat.FullWidthSelection, True); sel.cursor = self.textCursor(); sel.cursor.clearSelection(); extra.append(sel)
        self.setExtraSelections(extra)
    def keyPressEvent(self, e):
        if self.autocompleter.completer.popup().isVisible() and e.key() in (Qt.Key_Enter, Qt.Key_Tab): e.ignore(); return
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Space: self.show_completion(); return
        if e.key() == Qt.Key_Return:
            indent = "".join([c for c in self.textCursor().block().text() if c in [' ', '\t']] or []); super().keyPressEvent(e); self.insertPlainText(indent); return
        super().keyPressEvent(e); 
        if e.text().strip(): self.show_completion()
    def show_completion(self):
        c = self.textCursor(); c.select(QTextCursor.WordUnderCursor); p = c.selectedText()
        if p: self.autocompleter.completer.setCompletionPrefix(p); self.autocompleter.completer.complete(self.cursorRect())
    def update_font(self, s, t): f = QFont("Consolas", s); self.setFont(f); self.setTabStopDistance(t * QFontMetricsF(f).horizontalAdvance(' '))
    def apply_theme(self, n):
        self.theme_name = n; c = THEMES[n]; self.setStyleSheet(f"background-color: {c['bg']}; color: {c['fg']}; selection-background-color: {c['select_bg']};")
        self.highlighter.set_theme(n); self.update_line_number_area_width(0); self.highlight_current_line()

class EditorTab(QWidget):
    def __init__(self, parent, path=None, content="", theme="Dark", size=12, tabs=4):
        super().__init__(parent)
        self.file_path, self.saved = path, True
        ly = QHBoxLayout(self); ly.setContentsMargins(0,0,0,0); ly.setSpacing(0)
        self.editor = CodeEditor(self, theme, size, tabs); self.editor.setPlainText(content)
        self.minimap = CodeMinimap(self.editor); self.minimap.apply_theme(THEMES[theme])
        ly.addWidget(self.editor); ly.addWidget(self.minimap)
        self.editor.textChanged.connect(self._mod); self.editor.textChanged.connect(self.minimap.sync_with_parent)
    def _mod(self):
        if self.saved: self.saved = False; self.window().update_tab_title(self)
    def get_title(self): return os.path.basename(self.file_path) if self.file_path else "Sin título"

# =========================================================================
#  2. APP PRINCIPAL
# =========================================================================
class PySideEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.current_theme = "Dark"; self.font_size = 12; self.tab_width = 4
        self.autosave_enabled = True; self.minimap_enabled = True
        self.all_themes = list(THEMES.keys())
        self.root_dir = os.path.abspath(os.getcwd())

        s = self.config.get('app_settings', {})
        self.setWindowTitle(f"{s.get('app_name', 'Capi Editor')} - {self.root_dir}")
        self.setGeometry(100, 100, 1200, 800)
        
        main = QSplitter(Qt.Horizontal); self.setCentralWidget(main)
        
        # --- USAMOS EL SIDEBAR MODULAR ---
        self.sidebar_widget = ProjectSidebarWrapper(self)
        self.sidebar_widget.tree_view.clicked.connect(self.on_file_click)
        main.addWidget(self.sidebar_widget)
        
        # --- RESTO UI ---
        ctr = QWidget(); vbox = QVBoxLayout(ctr); vbox.setContentsMargins(0,0,0,0)
        self.v_split = QSplitter(Qt.Vertical)
        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab); self.tabs.currentChanged.connect(self.on_tab_change)
        self.v_split.addWidget(self.tabs)
        
        self.search = SearchWidget(self); self.v_split.addWidget(self.search)
        self.term = EditorTerminal(self); self.v_split.addWidget(self.term); self.term.hide()
        vbox.addWidget(self.v_split); main.addWidget(ctr); main.setStretchFactor(1, 1)

        self.setup_status_bar(); self.menu_b = MenuBuilder(self); self.menu_b.setup_menus()
        self.load_session()
        self.init_sidebar_for_path(self.root_dir)

        if self.tabs.count() == 0: self.show_welcome_tab()
        self.as_timer = QTimer(self); self.as_timer.timeout.connect(self.auto_save); self.as_timer.start(5000)

    # --- DIALOGOS ---
    def show_shortcuts_dialog(self):
        d = ShortcutsDialog(THEMES[self.current_theme], self)
        d.exec()

    def show_about(self): AboutDialog(self.config, THEMES[self.current_theme], self).exec()
    def show_global_search(self): GlobalSearchDialog(self.root_dir, self).exec()

    # --- SIDEBAR CONTROL ---
    def init_sidebar_for_path(self, path):
        self.root_dir = os.path.abspath(path)
        self.sidebar_widget.set_project_path(self.root_dir)
        self.setWindowTitle(f"Capi Editor - {os.path.basename(self.root_dir)}")

    def select_folder(self): 
        p = QFileDialog.getExistingDirectory(self, "Abrir Proyecto")
        if p: self.init_sidebar_for_path(p); self.save_session()
        
    def create_new_folder_global(self): self.sidebar_widget.tree_view.new_item(self.root_dir, True)
    def create_new_file_global(self): self.sidebar_widget.tree_view.new_item(self.root_dir, False)

    # --- CORE ---
    def show_welcome_tab(self):
        ws = self.config.get('welcome_screen', {})
        txt = f"{ws.get('welcome_title', 'Bienvenido a Capi Editor')}\n\n" + "\n".join(ws.get('features_list', []))
        t = self.add_tab(None, txt); t.is_welcome = True; t.editor.setReadOnly(True); t.saved = True
        self.tabs.setTabText(self.tabs.indexOf(t), "Inicio")

    def auto_save(self): 
        if self.autosave_enabled:
            for i in range(self.tabs.count()):
                t = self.tabs.widget(i)
                if not getattr(t, 'is_welcome', False) and t.file_path and not t.saved:
                    try:
                        with open(t.file_path, 'w', encoding='utf-8') as f: f.write(t.editor.toPlainText())
                        t.saved = True; self.update_tab_title(t)
                    except: pass
    
    def load_config(self):
        try:
            p = resource_path(CONFIG_FILE)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
        return {}
    def setup_status_bar(self):
        self.status_bar = self.statusBar(); self.lbl_lang = QLabel("Texto"); self.lbl_enc = QLabel("UTF-8"); self.lbl_cursor = QLabel("Ln 1, Col 1")
        for l in [self.lbl_lang, self.lbl_enc, self.lbl_cursor]: l.setStyleSheet("padding: 0 10px;"); self.status_bar.addPermanentWidget(l)
    def update_status_bar(self):
        t = self.tabs.currentWidget()
        if t and not getattr(t, 'is_welcome', False):
            c = t.editor.textCursor(); self.lbl_cursor.setText(f"Ln {c.blockNumber()+1}, Col {c.columnNumber()+1}")
            ext = os.path.splitext(t.file_path)[1].lower() if t.file_path else ""
            self.lbl_lang.setText({'.py':'Python','.js':'JavaScript','.html':'HTML','.css':'CSS','.json':'JSON'}.get(ext, "Texto"))
        else: self.lbl_cursor.setText(""); self.lbl_lang.setText("")
    def on_tab_change(self, i): 
        t = self.tabs.currentWidget(); 
        if t: self.update_tab_title(t); t.editor.apply_theme(self.current_theme); self.update_status_bar()
            
    def on_file_click(self, i): 
        model = self.sidebar_widget.tree_view.model()
        if model:
            p = model.filePath(i)
            if os.path.isfile(p): self.open_file(p)
            
    def open_file(self, path=None):
        if not path: path, _ = QFileDialog.getOpenFileName(self, "Abrir")
        if not path: return
        for i in range(self.tabs.count()):
            if getattr(self.tabs.widget(i), 'file_path', None) == path: self.tabs.setCurrentIndex(i); return
        if self.tabs.count() == 1 and getattr(self.tabs.widget(0), 'is_welcome', False): self.tabs.removeTab(0)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                t = self.add_tab(path, f.read())
                try: t.editor.highlighter.set_language(get_lexer_for_filename(path).aliases[0])
                except: t.editor.highlighter.set_language("text")
        except Exception as e: QMessageBox.critical(self, "Error", f"No se pudo abrir: {e}")
    def add_tab(self, path=None, content=""):
        if self.tabs.count() == 1 and getattr(self.tabs.widget(0), 'is_welcome', False): self.tabs.removeTab(0)
        t = EditorTab(self.tabs, path, content, self.current_theme, self.font_size, self.tab_width)
        i = self.tabs.addTab(t, t.get_title()); self.tabs.setCurrentIndex(i)
        t.editor.cursorPositionChanged.connect(self.update_status_bar); self.update_status_bar(); return t
    def save_current_file(self):
        t = self.tabs.currentWidget()
        if not t or getattr(t, 'is_welcome', False): return
        if t.file_path: 
            try:
                with open(t.file_path, 'w', encoding='utf-8') as f: f.write(t.editor.toPlainText()); t.saved = True; self.update_tab_title(t)
            except Exception as e: QMessageBox.critical(self, "Error", f"Error: {e}")
        elif t: self.save_file_as()
    def save_file_as(self):
        t = self.tabs.currentWidget()
        if not t or getattr(t, 'is_welcome', False): return
        p, _ = QFileDialog.getSaveFileName(self, "Guardar", self.root_dir)
        if p: 
            t.file_path = p; self.save_current_file(); self.update_status_bar()
            try: t.editor.highlighter.set_language(get_lexer_for_filename(p).aliases[0])
            except: pass
    def close_current_tab(self, i=None):
        idx = i if i is not None else self.tabs.currentIndex(); 
        if idx == -1: return
        t = self.tabs.widget(idx)
        if not t.saved and not getattr(t, 'is_welcome', False):
             res = QMessageBox.question(self, "Guardar", f"¿Guardar '{t.get_title()}'?", QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
             if res == QMessageBox.Yes: self.save_current_file()
             elif res == QMessageBox.Cancel: return False
        self.tabs.removeTab(idx); return True
    def closeEvent(self, e):
        for i in range(self.tabs.count()-1, -1, -1):
            if not self.close_current_tab(i): e.ignore(); return
        if hasattr(self, 'term'): self.term.stop_process()
        self.save_session(); e.accept()

    # --- MENU HOOKS ---
    def toggle_console(self): 
        if self.term.isVisible(): self.term.stop_process(); self.term.hide()
        else: self.term.show(); self.term.start_process()
    def toggle_local_search(self): self.search.setVisible(not self.search.isVisible())
    def run_current_file(self):
        self.save_current_file(); t = self.tabs.currentWidget()
        if t and t.file_path and not getattr(t, 'is_welcome', False):
            if not self.term.isVisible(): self.toggle_console()
            self.term.run_script(t.file_path)
    def toggle_autosave(self, c): self.autosave_enabled = c
    def change_font_size(self, s): self.font_size = s; self.refresh_tabs()
    def change_tab_width(self, w): self.tab_width = w; self.refresh_tabs()
    def refresh_tabs(self): 
        for i in range(self.tabs.count()): self.tabs.widget(i).editor.update_font(self.font_size, self.tab_width)
    def go_to_line(self): 
        t = self.tabs.currentWidget()
        if t and not getattr(t, 'is_welcome', False):
            v, ok = QInputDialog.getInt(self, "Ir a", "Línea:", 1, 1, t.editor.blockCount())
            if ok: c=t.editor.textCursor(); c.movePosition(QTextCursor.Start); c.movePosition(QTextCursor.Down, n=v-1); t.editor.setTextCursor(c); t.editor.centerCursor(); t.editor.setFocus()
    def zoom_in(self): t=self.tabs.currentWidget(); t.editor.zoomIn(1) if t else None
    def zoom_out(self): t=self.tabs.currentWidget(); t.editor.zoomOut(1) if t else None
    def toggle_minimap_global(self):
        self.minimap_enabled = not self.minimap_enabled
        for i in range(self.tabs.count()): self.tabs.widget(i).minimap.setVisible(self.minimap_enabled)
    def update_tab_title(self, t): 
        if not getattr(t, 'is_welcome', False): self.tabs.setTabText(self.tabs.indexOf(t), f"{'*' if not t.saved else ''}{t.get_title()}")
    def apply_theme(self, n):
        self.current_theme = n; c = THEMES[n]
        self.setStyleSheet(f"""
            QMainWindow, QDialog {{ background-color: {c['window_bg']}; color: {c['fg']}; }} 
            QMenu {{ background-color: {c['window_bg']}; color: {c['fg']}; border: 1px solid {c['splitter']}; }} 
            QMenu::item:selected {{ background-color: {c['select_bg']}; }} 
            QTabWidget::pane {{ border: 1px solid {c['splitter']}; }} 
            QTabBar::tab {{ background: {c['window_bg']}; color: {c['fg']}; padding: 8px 15px; border-right: 1px solid {c['splitter']}; }} 
            QTabBar::tab:selected {{ background: {c['bg']}; border-bottom: 2px solid {c['fg']}; }}
            
            QPushButton#btn_project {{
                text-align: left;
                padding-left: 15px;
                padding-top: 5px;
                padding-bottom: 5px;
                font-weight: bold;
                background-color: {c['bg']};
                color: {c['fg']};
                border: none;
                border-bottom: 1px solid {c['splitter']};
            }}
            QPushButton#btn_project:hover {{ background-color: {c['line_bg']}; }}
            
            QStatusBar {{ background-color: {c['window_bg']}; color: {c['fg']}; }}
            QStatusBar QLabel {{ color: {c['fg']}; }}
        """)
        self.sidebar_widget.update_theme(c)
        self.term.update_theme(c)
        for i in range(self.tabs.count()): self.tabs.widget(i).editor.apply_theme(n); self.tabs.widget(i).minimap.apply_theme(c)
        self.save_session()
    def save_session(self):
        d = {"root": self.root_dir, "theme": self.current_theme, "font": self.font_size}
        try:
            with open(resource_path("session.json"), 'w') as f: json.dump(d, f)
        except: pass
    def load_session(self):
        try:
            with open(resource_path("session.json"), 'r') as f:
                d = json.load(f); self.apply_theme(d.get('theme', 'Dark'))
                self.init_sidebar_for_path(d.get('root', os.getcwd()))
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv); w = PySideEditor(); w.show(); sys.exit(app.exec())