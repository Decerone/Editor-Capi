import sys, os, json, shutil
from PySide6.QtCore import (Qt, QTimer, QDir, QSize, QRect, QPoint, QThread, Signal)
from PySide6.QtGui import (QAction, QColor, QTextCharFormat, QFont, QFontMetricsF,
                           QSyntaxHighlighter, QTextCursor, QPainter, QKeyEvent, QIcon, QPixmap, QTextFormat) 
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPlainTextEdit, QSplitter, QFileDialog, QMessageBox, 
                               QTabWidget, QMenu, QInputDialog, QLabel, QDialog, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QTextEdit) 

# --- FUNCIÓN DE RUTAS SEGURA ---
def get_app_path(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

# --- JEDI ---
import jedi

# --- CARGAR KEYWORDS.JSON ---
KEYWORDS_DB = {}
try:
    path_kw = get_app_path("keywords.json")
    if os.path.exists(path_kw):
        with open(path_kw, 'r', encoding='utf-8') as f:
            KEYWORDS_DB = json.load(f)
        print(f"✅ Keywords: {path_kw}")
    else:
        print(f"⚠️ No encontrado: {path_kw}")
except Exception as e:
    print(f"❌ Error keywords: {e}")

# --- PYGMENTS ---
from pygments.lexers import get_lexer_for_filename
from pygments.token import Token

# --- MÓDULOS LOCALES ---
try:
    from utils import THEMES
    from terminal import EditorTerminal
    from autocomplete import AutoCompleter
    from minimap import CodeMinimap
    from search_module import SearchWidget, GlobalSearchDialog
    from menu_module import MenuBuilder
    from sidebar_module import ProjectSidebarWrapper
    from shortcuts import SHORTCUTS_DATA
except ImportError as e:
    print(f"Error crítico: {e}"); sys.exit(1)

CONFIG_FILE = "config.json"

# ================= CLASES DE UTILIDAD =================

class ShortcutsDialog(QDialog):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atajos")
        self.resize(500, 600)
        self.setStyleSheet(f"background-color: {colors['window_bg']}; color: {colors['fg']};")
        ly = QVBoxLayout(self)
        self.tbl = QTableWidget(0, 2); self.tbl.setHorizontalHeaderLabels(["Acción", "Atajo"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ly.addWidget(self.tbl)
        for cat, items in SHORTCUTS_DATA.items():
            for act, key in items:
                r = self.tbl.rowCount(); self.tbl.insertRow(r)
                self.tbl.setItem(r, 0, QTableWidgetItem(act)); self.tbl.setItem(r, 1, QTableWidgetItem(key))

class AboutDialog(QDialog):
    def __init__(self, config, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de")
        self.setFixedSize(350, 300)
        self.setStyleSheet(f"QDialog {{ background: {colors['window_bg']}; color: {colors['fg']}; }} QPushButton {{ background: {colors['bg']}; color: {colors['fg']}; border: 1px solid {colors['splitter']}; padding: 5px; }}")
        ly = QVBoxLayout(self); ly.setAlignment(Qt.AlignCenter)
        info = config.get("about", {})
        try:
            ic = get_app_path(info.get("icon_name", "icon.png"))
            if os.path.exists(ic): ly.addWidget(QLabel(pixmap=QPixmap(ic).scaled(80,80,Qt.KeepAspectRatio)), alignment=Qt.AlignCenter)
        except: pass
        ly.addWidget(QLabel(info.get("app_name", "Capi Editor Pro")), alignment=Qt.AlignCenter)
        ly.addWidget(QLabel(f"v{info.get('version', '1.0')}"), alignment=Qt.AlignCenter)
        btn = QPushButton("Cerrar"); btn.clicked.connect(self.accept); ly.addWidget(btn)

class LineNumberArea(QWidget):
    def __init__(self, editor): super().__init__(editor); self.editor = editor
    def sizeHint(self): return QSize(self.editor.line_number_area_width(), 0)
    def paintEvent(self, event): self.editor.lineNumberAreaPaintEvent(event)

class PySideHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, language="text", theme_name="Dark"):
        super().__init__(parent); self.language = language; self.theme_name = theme_name; self.formats = {}; self.setup_formats()
    def setup_formats(self):
        colors = THEMES.get(self.theme_name, THEMES['Dark']).get('tags', {})
        self.formats = {}
        for tag, hex_color in colors.items():
            fmt = QTextCharFormat(); fmt.setForeground(QColor(hex_color))
            if tag in ['keyword', 'class']: fmt.setFontWeight(QFont.Bold)
            if tag == 'comment': fmt.setFontItalic(True)
            self.formats[tag] = fmt
    def highlightBlock(self, text):
        try:
            from pygments.lexers import get_lexer_by_name
            options = {'startinline': True} if 'php' in self.language else {}
            try: lexer = get_lexer_by_name(self.language, **options)
            except: lexer = get_lexer_by_name("text")
        except: return
        self.setFormat(0, len(text), QTextCharFormat()); text_index = 0
        for token_type, value in lexer.get_tokens(text):
            tag_name = self._get_tag_for_token(token_type); length = len(value)
            if tag_name and tag_name in self.formats: self.setFormat(text_index, length, self.formats[tag_name])
            text_index += length
    def _get_tag_for_token(self, token_type):
        if token_type in Token.Keyword: return "keyword"
        if token_type in Token.Literal.String: return "string"
        if token_type in Token.Comment: return "comment"
        if token_type in Token.Name.Function: return "function"
        if token_type in Token.Name.Class: return "class"
        return None
    def set_language(self, l): self.language = l; self.rehighlight()
    def set_theme(self, t): self.theme_name = t; self.setup_formats(); self.rehighlight()

class JediWorker(QThread):
    finished = Signal(list)
    def __init__(self, code, line, col, path):
        super().__init__()
        self.code, self.line, self.col, self.path = code, line, col, path
    def run(self):
        try:
            script = jedi.Script(code=self.code, path=self.path)
            completions = script.complete(self.line, self.col)
            self.finished.emit([{'name': c.name, 'type': c.type} for c in completions])
        except: self.finished.emit([])

# ================= CLASE CODE EDITOR =================

class CodeEditor(QPlainTextEdit): 
    def __init__(self, parent, theme, size, tabs):
        super().__init__(parent)
        self.theme_name = theme
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PySideHighlighter(self.document(), "text", theme)
        self.completer = AutoCompleter(self)
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insert_completion)
        self.tab_width = tabs
        self.file_path = None
        self.current_lang = "text"
        self.auto_pairs = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}
        self.worker = None
        self.timer_jedi = QTimer()
        self.timer_jedi.setSingleShot(True)
        self.timer_jedi.timeout.connect(self.run_jedi_analysis)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.update_font(size, tabs)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.apply_theme(theme)

    def set_code_language(self, lang_alias):
        self.current_lang = lang_alias.lower()
        self.highlighter.set_language(self.current_lang)
        if self.current_lang != 'python':
            cw = []
            if self.current_lang == 'php': 
                cw = KEYWORDS_DB.get('php', []) + KEYWORDS_DB.get('html', [])
            elif self.current_lang in ['html', 'htm']: 
                cw = KEYWORDS_DB.get('html', []) + KEYWORDS_DB.get('css', []) + KEYWORDS_DB.get('javascript', [])
            else:
                k = self.current_lang
                if k == 'js': k = 'javascript'
                cw = KEYWORDS_DB.get(k, [])
            if cw: self.completer.load_keywords(sorted(list(set(cw))))

    def keyPressEvent(self, e: QKeyEvent):
        if self.completer.popup().isVisible() and e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab, Qt.Key_Escape): 
            e.ignore()
            return
        if e.text() in self.auto_pairs:
            c = self.textCursor()
            c.insertText(e.text() + self.auto_pairs[e.text()])
            c.movePosition(QTextCursor.Left)
            self.setTextCursor(c)
            return
        super().keyPressEvent(e)
        if self.current_lang == 'python':
            if e.text().isalnum() or e.text() == "." or ((e.modifiers() & Qt.ControlModifier) and e.key() == Qt.Key_Space): 
                self.timer_jedi.start(200)
        elif e.text().isalnum() or ((e.modifiers() & Qt.ControlModifier) and e.key() == Qt.Key_Space): 
            self.show_static_suggestions()

    def show_static_suggestions(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        prefix = tc.selectedText()
        if len(prefix) < 1: 
            self.completer.popup().hide()
            return
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() > 0:
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 30)
            self.completer.complete(cr)

    def run_jedi_analysis(self):
        if self.worker and self.worker.isRunning(): return
        c = self.textCursor()
        self.worker = JediWorker(self.toPlainText(), c.blockNumber()+1, c.columnNumber(), self.file_path)
        self.worker.finished.connect(self.handle_jedi_results)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def handle_jedi_results(self, r):
        if not r: return
        self.completer.update_jedi_completions(r)
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        prefix = tc.selectedText()
        self.completer.setCompletionPrefix(prefix)
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 30)
        self.completer.complete(cr)

    def insert_completion(self, c):
        tc = self.textCursor()
        p = self.completer.completionPrefix()
        tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(p))
        tc.removeSelectedText()
        tc.insertText(c)
        self.setTextCursor(tc)

    def update_font(self, s, t): 
        f = QFont("Consolas", s)
        self.setFont(f)
        self.setTabStopDistance(t * QFontMetricsF(f).horizontalAdvance(' '))

    def apply_theme(self, n):
        self.theme_name = n
        c = THEMES.get(n, THEMES['Dark'])
        self.setStyleSheet(f"background-color: {c['bg']}; color: {c['fg']}; selection-background-color: {c['select_bg']}; border: none;")
        self.highlighter.set_theme(n)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    # --- CORRECCIÓN INDENTACIÓN Y LÓGICA ---
    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 40 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _): 
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, r, dy):
        if dy: self.line_number_area.scroll(0, dy)
        else: self.line_number_area.update(0, r.y(), self.line_number_area.width(), r.height())
        if r.contains(self.viewport().rect()): 
            self.update_line_number_area_width(0)

    def resizeEvent(self, e): 
        super().resizeEvent(e)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        p = QPainter(self.line_number_area)
        c = THEMES.get(self.theme_name, THEMES['Dark'])
        p.fillRect(event.rect(), QColor(c['line_bg']))
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(QColor(c['line_fg']))
                p.drawText(0, int(top), self.line_number_area.width()-5, self.fontMetrics().height(), Qt.AlignRight, str(num+1))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            num += 1

    def highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            bg_color = QColor(THEMES.get(self.theme_name, THEMES['Dark'])['line_bg'])
            # Ajuste de color para que sea visible en modo Light
            if self.theme_name == 'Light':
                sel.format.setBackground(bg_color)
            else:
                sel.format.setBackground(bg_color.lighter(120))
            
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

# ================= APP PRINCIPAL =================

class EditorTab(QWidget):
    def __init__(self, parent, path=None, content="", theme="Dark", size=12, tabs=4):
        super().__init__(parent)
        self.file_path, self.saved = path, True
        ly = QHBoxLayout(self); ly.setContentsMargins(0,0,0,0); ly.setSpacing(0)
        self.editor = CodeEditor(self, theme, size, tabs); self.editor.setPlainText(content)
        self.editor.file_path = path 
        self.minimap = CodeMinimap(self.editor); self.minimap.apply_theme(THEMES.get(theme, THEMES['Dark']))
        ly.addWidget(self.editor); ly.addWidget(self.minimap)
        self.editor.textChanged.connect(self._mod); self.editor.textChanged.connect(self.minimap.sync_with_parent)
    def _mod(self):
        if self.saved: self.saved = False; self.window().update_tab_title(self)
    def get_title(self): return os.path.basename(self.file_path) if self.file_path else "Sin título"

class CapiEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.current_theme = "Dark"
        self.font_size = 12
        self.tab_width = 4
        self.autosave_enabled = True
        self.minimap_enabled = True
        self.root_dir = os.path.abspath(os.getcwd())
        self.all_themes = list(THEMES.keys())
        
        self.setWindowTitle("Capi Editor Pro")
        self.resize(1200, 800)
        main = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main)
        
        self.sidebar_widget = ProjectSidebarWrapper(self)
        self.sidebar_widget.tree_view.clicked.connect(self.on_file_click)
        main.addWidget(self.sidebar_widget)
        
        ctr = QWidget()
        vbox = QVBoxLayout(ctr)
        vbox.setContentsMargins(0,0,0,0)
        self.v_split = QSplitter(Qt.Vertical)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.on_tab_change)
        self.v_split.addWidget(self.tabs)
        
        self.search = SearchWidget(self)
        self.v_split.addWidget(self.search)
        self.term = EditorTerminal(self)
        self.v_split.addWidget(self.term)
        self.term.hide()
        vbox.addWidget(self.v_split)
        main.addWidget(ctr)
        main.setStretchFactor(1, 1)

        self.setup_status_bar()
        self.init_sidebar_for_path(self.root_dir)
        self.load_session()

        self.menu_b = MenuBuilder(self)
        self.menu_b.setup_menus()
        
        if self.tabs.count() == 0: self.show_welcome_tab()
        self.as_timer = QTimer(self)
        self.as_timer.timeout.connect(self.auto_save)
        self.as_timer.start(5000)

    # --- CONFIGURACIÓN Y SESIÓN ---
    def load_config(self):
        try:
            with open(get_app_path("config.json"), 'r', encoding='utf-8') as f: 
                self.config = json.load(f)
        except: self.config = {}

    def load_session(self):
        try:
            with open(get_app_path("session.json"), 'r', encoding='utf-8') as f:
                d = json.load(f)
                self.apply_theme(d.get('theme', 'Dark'))
                root = d.get('root', os.getcwd())
                if os.path.exists(root): self.init_sidebar_for_path(root)
        except: pass

    def save_session(self):
        try:
            with open(get_app_path("session.json"), 'w') as f:
                json.dump({"root": self.root_dir, "theme": self.current_theme}, f)
        except: pass

    # --- RESTO DE FUNCIONES ---
    def create_new_file_global(self):
        if hasattr(self.sidebar_widget, 'tree_view'): self.sidebar_widget.tree_view.new_item(self.root_dir, False)
    def create_new_folder_global(self):
        if hasattr(self.sidebar_widget, 'tree_view'): self.sidebar_widget.tree_view.new_item(self.root_dir, True)
    def select_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Abrir Proyecto")
        if p: self.init_sidebar_for_path(p); self.save_session()
    def init_sidebar_for_path(self, path):
        self.root_dir = os.path.abspath(path)
        self.sidebar_widget.set_project_path(self.root_dir)
        self.setWindowTitle(f"Capi Editor - {os.path.basename(self.root_dir)}")
    def on_file_click(self, i): 
        p = self.sidebar_widget.tree_view.model().filePath(i)
        if os.path.isfile(p): self.open_file(p)
    def open_file(self, path=None):
        if not path: path, _ = QFileDialog.getOpenFileName(self, "Abrir")
        if not path: return
        for i in range(self.tabs.count()):
            if getattr(self.tabs.widget(i), 'file_path', None) == path:
                self.tabs.setCurrentIndex(i); return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                t = self.add_tab(path, f.read())
                try:
                    from pygments.lexers import get_lexer_for_filename
                    lexer = get_lexer_for_filename(path)
                    t.editor.set_code_language(lexer.aliases[0])
                except: t.editor.set_code_language("text")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def add_tab(self, path=None, content=""):
        if self.tabs.count() == 1 and getattr(self.tabs.widget(0), 'is_welcome', False): self.tabs.removeTab(0)
        t = EditorTab(self.tabs, path, content, self.current_theme, self.font_size, self.tab_width)
        i = self.tabs.addTab(t, t.get_title()); self.tabs.setCurrentIndex(i)
        t.editor.cursorPositionChanged.connect(self.update_status)
        return t
    def update_status(self):
        t = self.tabs.currentWidget()
        if t and not getattr(t, 'is_welcome', False):
            c = t.editor.textCursor()
            self.lbl_cursor.setText(f"Ln {c.blockNumber()+1}, Col {c.columnNumber()+1}")
            self.lbl_lang.setText(t.editor.current_lang.upper())
    def setup_status_bar(self):
        self.status_bar = self.statusBar(); self.lbl_lang = QLabel("Texto"); self.lbl_cursor = QLabel("Ln 1, Col 1")
        self.status_bar.addPermanentWidget(self.lbl_lang); self.status_bar.addPermanentWidget(self.lbl_cursor)
    def show_welcome_tab(self):
        ws = self.config.get('welcome_screen', {})
        t = self.add_tab(None, f"{ws.get('welcome_title', 'Bienvenido')}\n\n" + "\n".join(ws.get('features_list', [])))
        t.is_welcome = True; t.editor.setReadOnly(True); t.saved = True; self.tabs.setTabText(self.tabs.indexOf(t), "Inicio")
    def auto_save(self): 
        for i in range(self.tabs.count()):
            t = self.tabs.widget(i)
            if not getattr(t, 'is_welcome', False) and t.file_path and not t.saved:
                try:
                    with open(t.file_path, 'w', encoding='utf-8') as f: f.write(t.editor.toPlainText()); t.saved = True; self.update_tab_title(t)
                except: pass
    def update_tab_title(self, t): self.tabs.setTabText(self.tabs.indexOf(t), f"{'*' if not t.saved else ''}{t.get_title()}")
    def close_current_tab(self, i=None): 
        idx = i if i is not None else self.tabs.currentIndex()
        if idx != -1: self.tabs.removeTab(idx)
    def on_tab_change(self, i): 
        t = self.tabs.currentWidget(); 
        if t: t.editor.apply_theme(self.current_theme); self.update_status()
    def save_current_file(self): self.auto_save()
    def save_file_as(self):
        t = self.tabs.currentWidget()
        if not t: return
        p, _ = QFileDialog.getSaveFileName(self, "Guardar", self.root_dir)
        if p:
            t.file_path = p; self.save_current_file(); t.editor.file_path = p; self.update_tab_title(t)
            try: from pygments.lexers import get_lexer_for_filename; t.editor.set_code_language(get_lexer_for_filename(p).aliases[0])
            except: pass
    def show_shortcuts_dialog(self): ShortcutsDialog(THEMES.get(self.current_theme, {}), self).exec()
    def show_about(self): AboutDialog(self.config, THEMES.get(self.current_theme, {}), self).exec()
    def show_global_search(self): GlobalSearchDialog(self.root_dir, self).exec()
    def toggle_console(self): self.term.hide() if self.term.isVisible() else self.term.show()
    def run_current_file(self):
        t = self.tabs.currentWidget()
        if t and t.file_path: self.term.run_script(t.file_path)
    def toggle_autosave(self, e): self.autosave_enabled = e
    def toggle_local_search(self): self.search.setVisible(not self.search.isVisible())
    def change_font_size(self, s): 
        self.font_size = s
        for i in range(self.tabs.count()): self.tabs.widget(i).editor.update_font(s, self.tab_width)
    def zoom_in(self): t = self.tabs.currentWidget(); t.editor.zoomIn(1) if t else None
    def zoom_out(self): t = self.tabs.currentWidget(); t.editor.zoomOut(1) if t else None
    def go_to_line(self):
        t = self.tabs.currentWidget()
        if t:
            l, ok = QInputDialog.getInt(self, "Ir a", "Línea:", 1, 1, t.editor.blockCount())
            if ok: c = t.editor.textCursor(); c.movePosition(QTextCursor.Start); c.movePosition(QTextCursor.Down, n=l-1); t.editor.setTextCursor(c); t.editor.centerCursor(); t.editor.setFocus()
    def toggle_minimap_global(self):
        self.minimap_enabled = not self.minimap_enabled
        for i in range(self.tabs.count()): self.tabs.widget(i).minimap.setVisible(self.minimap_enabled)

    # --- APLICACIÓN DE TEMA COMPLETO ---
    def apply_theme(self, n):
        self.current_theme = n
        c = THEMES.get(n, THEMES['Dark'])
        
        # Generar CSS
        style = f"""
            /* VENTANA Y DIALOGOS */
            QMainWindow, QDialog {{ 
                background-color: {c['window_bg']}; 
                color: {c['fg']}; 
            }}
            
            /* MENÚS */
            QMenuBar {{ background-color: {c['window_bg']}; color: {c['fg']}; }}
            QMenuBar::item:selected {{ background-color: {c['select_bg']}; color: {c['bg']}; }}
            QMenu {{ background-color: {c['window_bg']}; color: {c['fg']}; border: 1px solid {c['splitter']}; }}
            QMenu::item:selected {{ background-color: {c['select_bg']}; color: {c['bg']}; }}
            
            /* TABS */
            QTabWidget::pane {{ border: 1px solid {c['splitter']}; }}
            QTabBar::tab {{ 
                background: {c['window_bg']}; 
                color: {c['fg']}; 
                padding: 6px 14px; 
                border: 1px solid {c['splitter']};
            }}
            QTabBar::tab:selected {{ 
                background: {c['bg']}; 
                border-bottom: 2px solid {c['select_bg']}; 
                font-weight: bold;
            }}

            /* BARRA DE ESTADO */
            QStatusBar {{ 
                background-color: {c['select_bg']}; 
                color: {c['bg'] if n == 'Light' else c['fg']}; 
            }}
            QStatusBar QLabel {{ color: {c['bg'] if n == 'Light' else c['fg']}; }}

            /* BOTONES */
            QPushButton {{ 
                background-color: {c['bg']}; 
                color: {c['fg']}; 
                border: 1px solid {c['splitter']}; 
                padding: 4px; 
            }}
            QPushButton:hover {{ background-color: {c['line_bg']}; }}
        """
        self.setStyleSheet(style)
        
        self.sidebar_widget.update_theme(c)
        self.term.update_theme(c)
        for i in range(self.tabs.count()):
            self.tabs.widget(i).editor.apply_theme(n)
            self.tabs.widget(i).minimap.apply_theme(c)
        self.save_session()
        
    def closeEvent(self, e):
        if hasattr(self, 'term'): self.term.stop_process()
        self.save_session(); e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CapiEditor()
    window.show()
    sys.exit(app.exec())