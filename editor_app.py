#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================================
#  CAPI EDITOR PRO - VERSIÓN FINAL (CORREGIDA Y COMPLETA)
# ==============================================================================

import sys
import os
import json
import re
import traceback

from PySide6.QtCore import (Qt, QTimer, QSize, QRect, QThread, Signal, QEvent)
from PySide6.QtGui import (QColor, QTextCharFormat, QFont, QFontMetricsF,
                           QSyntaxHighlighter, QTextCursor, QPainter, QKeyEvent,
                           QIcon, QPixmap, QTextFormat)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPlainTextEdit, QSplitter, QFileDialog, QMessageBox,
                               QTabWidget, QMenu, QInputDialog, QLabel, QDialog,
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QTextEdit, QCompleter)

# --- IMPORTACIONES EXTERNAS ---
try:
    import jedi
    from pygments import lexers
    from pygments.token import Token
except ImportError as e:
    print(f"❌ Error faltan librerías externas: {e}")

# ==============================================================================
#  CONFIGURACIÓN Y RUTAS
# ==============================================================================

basedir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(basedir, "icon.png")

def get_app_path(filename):
    return os.path.join(basedir, filename)

# Cargar Keywords
KEYWORDS_DB = {}
try:
    path_kw = get_app_path("keywords.json")
    if os.path.exists(path_kw):
        with open(path_kw, 'r', encoding='utf-8') as f:
            KEYWORDS_DB = json.load(f)
except Exception as e:
    print(f"❌ Error keywords: {e}")

# ==============================================================================
#  CARGA DE MÓDULOS LOCALES
# ==============================================================================
try:
    from utils import THEMES
    from terminal import EditorTerminal
    from autocomplete import AutoCompleter
    from minimap import CodeMinimap
    from search_module import SearchWidget, GlobalSearchDialog
    from menu_module import MenuBuilder
    from sidebar_module import ProjectSidebar
    from shortcuts import SHORTCUTS_DATA
except Exception as e:
    traceback.print_exc()
    sys.exit(1)


# ==============================================================================
#  CLASES DE UTILIDAD
# ==============================================================================

class ShortcutsDialog(QDialog):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atajos de Teclado")
        self.resize(600, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['window_bg']};
                color: {colors['fg']};
            }}
            QTableWidget {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                gridline-color: {colors['splitter']};
                selection-background-color: {colors['select_bg']};
            }}
            QHeaderView::section {{
                background-color: {colors['line_bg']};
                color: {colors['fg']};
                padding: 4px;
                border: none;
            }}
            QPushButton {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                border: 1px solid {colors['splitter']};
                padding: 5px 15px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {colors['line_bg']};
            }}
        """)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Acción", "Atajo"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        for category, items in SHORTCUTS_DATA.items():
            for action, key in items:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(action))
                self.table.setItem(row, 1, QTableWidgetItem(key))

        layout.addWidget(self.table)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)


class AboutDialog(QDialog):
    def __init__(self, config, colors, fallback_icon_path, parent=None):
        super().__init__(parent)
        about_data = config.get('about', {})
        app_settings = config.get('app_settings', {})

        app_name = about_data.get('app_name', 'Capi Editor Pro')
        app_version = about_data.get('version', 'Versión 2.0')
        app_desc = about_data.get('app_desc', 'Un editor de código moderno y ligero')
        app_author = about_data.get('app_author', 'Capi Dev')
        app_year = about_data.get('app_year', '2026')

        json_icon_name = app_settings.get("icon_path", "")
        if json_icon_name:
            final_icon_path = os.path.join(basedir, json_icon_name)
        else:
            final_icon_path = fallback_icon_path

        self.setWindowTitle(f"Acerca de {app_name}")
        self.setFixedSize(350, 280)
        self.setWindowIcon(QIcon(final_icon_path))

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.get('window_bg', '#252526')};
                color: {colors.get('fg', '#d4d4d4')};
            }}
            QLabel {{
                color: {colors.get('fg', '#d4d4d4')};
            }}
            QPushButton {{
                background-color: {colors.get('bg', '#1e1e1e')};
                color: {colors.get('fg', '#d4d4d4')};
                border: 1px solid {colors.get('splitter', '#3e3e42')};
                padding: 5px 15px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('line_bg', '#2d2d30')};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        icon_label = QLabel()
        pixmap = QPixmap(final_icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("📝")
            icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel(app_name)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel(app_version)
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        desc = QLabel(app_desc)
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        rights = QLabel(f"© {app_year} {app_author}")
        rights.setAlignment(Qt.AlignCenter)
        layout.addWidget(rights)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


# ==============================================================================
#  CLASE: HIGHLIGHTER
# ==============================================================================

class PySideHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, language="text", theme_name="Dark"):
        super().__init__(parent)
        self.language = language
        self.theme_name = theme_name
        self.formats = {}
        self.setup_formats()

    def setup_formats(self):
        theme_tags = THEMES.get(self.theme_name, THEMES['Dark']).get('tags', {})
        self.formats = {}
        for tag, hex_color in theme_tags.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(hex_color))
            if tag in ['keyword', 'class']:
                fmt.setFontWeight(QFont.Bold)
            if tag == 'comment':
                fmt.setFontItalic(True)
            self.formats[tag] = fmt

    def set_language(self, l):
        self.language = l.lower()
        self.rehighlight()

    def set_theme(self, t):
        self.theme_name = t
        self.setup_formats()
        self.rehighlight()

    def highlightBlock(self, text):
        if not text:
            return
        try:
            from pygments.lexers import get_lexer_by_name
            if self.language in ['php', 'html', 'htm', 'blade']:
                lexer = get_lexer_by_name("php", startinline=True)
            else:
                lexer = get_lexer_by_name(self.language)
        except:
            return

        for index, token_type, value in lexer.get_tokens_unprocessed(text):
            length = len(value)
            tag = self._get_tag_for_token(token_type)
            if tag and tag in self.formats:
                self.setFormat(index, length, self.formats[tag])

    def _get_tag_for_token(self, token_type):
        if token_type in Token.Keyword:
            return "keyword"
        if token_type in Token.Name.Tag:
            return "tag"
        if token_type in Token.Name.Attribute:
            return "attribute"
        if token_type in Token.Literal.String:
            return "string"
        if token_type in Token.Name.Builtin:
            return "builtin"
        if token_type in Token.Name.Variable:
            return "variable"
        if token_type in Token.Comment:
            return "comment"
        if token_type in Token.Operator:
            return "operator"
        if token_type in Token.Literal.Number:
            return "number"
        if token_type in Token.Name.Function:
            return "function"
        if token_type in Token.Name.Class:
            return "class"
        if token_type in Token.Name:
            return "attribute"
        return None


# ==============================================================================
#  CLASE: JEDI WORKER
# ==============================================================================

class JediWorker(QThread):
    finished = Signal(list)

    def __init__(self, code, line, col, path):
        super().__init__()
        self.code = code
        self.line = line
        self.col = col
        self.path = path

    def run(self):
        try:
            script = jedi.Script(code=self.code, path=self.path)
            completions = script.complete(self.line, self.col)
            results = [{'name': c.name, 'type': c.type} for c in completions]
            self.finished.emit(results)
        except:
            self.finished.emit([])


# ==============================================================================
#  CLASE PRINCIPAL: CODE EDITOR
# ==============================================================================

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent, theme, size, tabs):
        super().__init__(parent)
        self.theme_name = theme
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PySideHighlighter(self.document(), "text", theme)

        self.completer = AutoCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.activated.connect(self.insert_completion)
        self.installEventFilter(self)

        self.tab_width = tabs
        self.file_path = None
        self.current_lang = "text"
        self.base_keywords = []

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
        if lang_alias in ['js', 'javascript']:
            lang = 'javascript'
        elif lang_alias in ['py', 'python']:
            lang = 'python'
        elif lang_alias in ['html', 'htm']:
            lang = 'html'
        elif lang_alias in ['php']:
            lang = 'php'
        elif lang_alias in ['css']:
            lang = 'css'
        else:
            lang = 'text'

        self.current_lang = lang
        self.highlighter.set_language(self.current_lang)

        self.base_keywords = []
        if self.current_lang != 'python':
            if self.current_lang == 'php':
                self.base_keywords = KEYWORDS_DB.get('php', []) + KEYWORDS_DB.get('html', [])
            elif self.current_lang == 'html':
                self.base_keywords = KEYWORDS_DB.get('html', []) + KEYWORDS_DB.get('css', []) + KEYWORDS_DB.get('javascript', [])
            else:
                self.base_keywords = KEYWORDS_DB.get(self.current_lang, [])

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and self.completer.popup().isVisible():
            key = event.key()
            if key == Qt.Key_Tab:
                popup = self.completer.popup()
                current_index = popup.currentIndex()
                if not current_index.isValid():
                    current_index = popup.model().index(0, 0)
                if current_index.isValid():
                    text_to_insert = current_index.data(Qt.DisplayRole)
                    if text_to_insert:
                        self.insert_completion(text_to_insert)
                        popup.hide()
                        return True
                popup.hide()
                return False
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                popup = self.completer.popup()
                current_index = popup.currentIndex()
                if current_index.isValid():
                    text_to_insert = current_index.data(Qt.DisplayRole)
                    if text_to_insert:
                        self.insert_completion(text_to_insert)
                        popup.hide()
                        return True
                popup.hide()
                return False
            elif key == Qt.Key_Escape:
                self.completer.popup().hide()
                return True
            elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
                return False
        return super().eventFilter(obj, event)

    def insert_completion(self, completion):
        if not completion:
            return
        tc = self.textCursor()
        doc = self.document()
        pos = tc.position()
        text = doc.toPlainText()

        start_pos = pos
        while start_pos > 0:
            char = text[start_pos - 1]
            if char.isalnum() or char == '_':
                start_pos -= 1
            else:
                break

        tc.setPosition(start_pos)
        tc.setPosition(pos, QTextCursor.KeepAnchor)
        tc.insertText(completion)
        self.setTextCursor(tc)

    def get_dynamic_words(self):
        text = self.toPlainText()
        try:
            raw_words = re.findall(r'\b[a-zA-Z_]\w{2,}\b', text)
            return list(set(raw_words))
        except:
            return []

    def show_static_suggestions(self):
        tc = self.textCursor()
        line_text = tc.block().text()
        pos_in_block = tc.positionInBlock()
        text_before = line_text[:pos_in_block]

        match = re.search(r'([a-zA-Z0-9_]+)$', text_before)
        prefix = match.group(1) if match else ""

        if len(prefix) < 2:
            self.completer.popup().hide()
            return

        dynamic = self.get_dynamic_words()
        combined = list(set(self.base_keywords + dynamic))
        filtered = [w for w in combined if w.lower().startswith(prefix.lower())]
        filtered.sort(key=lambda x: (x.lower() != prefix.lower(), x.lower()))

        if not filtered:
            self.completer.popup().hide()
            return

        self.completer.load_keywords(filtered)
        self.completer.setCompletionPrefix(prefix)
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 40)
        self.completer.complete(cr)

    def keyPressEvent(self, e: QKeyEvent):
        if e.text() in ['(', '{', '[', '"', "'"]:
            pairs = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}
            c = self.textCursor()
            c.insertText(e.text() + pairs[e.text()])
            c.movePosition(QTextCursor.Left)
            self.setTextCursor(c)
            return

        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            pos = cursor.position()
            doc = self.document()
            if pos > 0 and pos < doc.characterCount():
                char_before = doc.characterAt(pos - 1)
                char_after = doc.characterAt(pos)
                if (char_before in ['{', '(', '['] and char_after in ['}', ')', ']']):
                    cursor.insertText("\n\n")
                    cursor.movePosition(QTextCursor.Up)
                    cursor.insertText(" " * self.tab_width)
                    self.setTextCursor(cursor)
                    return

        super().keyPressEvent(e)

        is_ctrl_space = (e.modifiers() & Qt.ControlModifier) and e.key() == Qt.Key_Space
        triggers = ['.', '#', '$', '@', '-', '_', '<', '/']

        if self.current_lang == 'python':
            if e.text().isalnum() or e.text() == "." or is_ctrl_space:
                self.timer_jedi.start(150)
        else:
            if e.text().isalnum() or e.text() in triggers or is_ctrl_space:
                self.show_static_suggestions()

    def run_jedi_analysis(self):
        if self.worker and self.worker.isRunning():
            return
        c = self.textCursor()
        self.worker = JediWorker(self.toPlainText(), c.blockNumber() + 1, c.columnNumber(), self.file_path)
        self.worker.finished.connect(self.handle_jedi_results)
        self.worker.start()

    def handle_jedi_results(self, r):
        if not r:
            self.completer.popup().hide()
            return
        self.completer.update_jedi_completions(r)
        tc = self.textCursor()
        self.completer.setCompletionPrefix("")
        line_text = tc.block().text()[:tc.positionInBlock()]
        match = re.search(r'([a-zA-Z0-9_\.]+)$', line_text)
        prefix = match.group(1) if match else ""
        self.completer.setCompletionPrefix(prefix)
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 40)
        self.completer.complete(cr)

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

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 5 + self.fontMetrics().horizontalAdvance('9') * digits
        return max(20, space)

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, r, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, r.y(), self.line_number_area.width(), r.height())
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
                p.drawText(2, int(top), self.line_number_area.width() - 4,
                           self.fontMetrics().height(), Qt.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            num += 1

    def highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            bg_color = QColor(THEMES.get(self.theme_name, THEMES['Dark'])['line_bg'])
            if self.theme_name == 'Light':
                sel.format.setBackground(bg_color)
            else:
                sel.format.setBackground(bg_color.lighter(120))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)


# ==============================================================================
#  CLASE: EDITOR TAB
# ==============================================================================

class EditorTab(QWidget):
    def __init__(self, parent, path=None, content="", theme="Dark", size=12, tabs=4):
        super().__init__(parent)
        self.file_path = path
        self.saved = True
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(0)
        self.editor = CodeEditor(self, theme, size, tabs)
        self.editor.setPlainText(content)
        self.editor.file_path = path
        self.minimap = CodeMinimap(self.editor)
        self.minimap.apply_theme(THEMES.get(theme, THEMES['Dark']))
        ly.addWidget(self.editor)
        ly.addWidget(self.minimap)
        self.editor.textChanged.connect(self._mod)
        self.editor.textChanged.connect(self.minimap.delayed_sync)

    def _mod(self):
        if self.saved:
            self.saved = False
            self.window().update_tab_title(self)

    def get_title(self):
        return os.path.basename(self.file_path) if self.file_path else "Sin título"


# ==============================================================================
#  CLASE PRINCIPAL: CAPI EDITOR
# ==============================================================================

class CapiEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_config()

        app_settings = self.config.get("app_settings", {})
        self.app_name = app_settings.get("app_name", "Capi Editor Pro")
        self.app_version = app_settings.get("app_version", "")
        self.no_project_message = app_settings.get("no_project_message", "No hay proyecto asignado")

        self.current_theme = "Dark"
        self.font_size = 12
        self.tab_width = 4
        self.autosave_enabled = True
        self.minimap_enabled = True
        self.root_dir = None

        self.all_themes = list(THEMES.keys())

        self.setWindowTitle(f"{self.app_name} {self.app_version}".strip())
        self.resize(1200, 800)
        main = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main)

        self.sidebar_widget = ProjectSidebar(self, no_project_message=self.no_project_message)
        self.sidebar_widget.tree_view.clicked.connect(self.on_file_click)
        self.sidebar_widget.tree_view.activated.connect(self.on_file_click)  # Navegación con Enter
        main.addWidget(self.sidebar_widget)

        ctr = QWidget()
        vbox = QVBoxLayout(ctr)
        vbox.setContentsMargins(0, 0, 0, 0)
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

        if self.tabs.count() == 0:
            self.show_welcome_tab()

        self.as_timer = QTimer(self)
        self.as_timer.timeout.connect(self.auto_save)
        self.as_timer.start(5000)

    # ----------------------------------------------------------------------
    #  CONFIGURACIÓN Y SESIÓN
    # ----------------------------------------------------------------------
    def load_config(self):
        try:
            config_path = get_app_path("config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"⚠️ No se pudo cargar config.json: {e}")
            self.config = {}

    def load_session(self):
        try:
            session_path = get_app_path("session.json")
            if not os.path.exists(session_path):
                return
            with open(session_path, 'r', encoding='utf-8') as f:
                d = json.load(f)

            theme = d.get('theme', 'Dark')
            self.apply_theme(theme)

            root = d.get('root')
            if root and os.path.exists(root):
                self.root_dir = root
            else:
                self.root_dir = None
            self.init_sidebar_for_path(self.root_dir)

            open_files = d.get('open_files', [])
            for file_path in open_files:
                if os.path.isfile(file_path):
                    self.open_file(file_path)

            current_tab = d.get('current_tab', 0)
            if 0 <= current_tab < self.tabs.count():
                self.tabs.setCurrentIndex(current_tab)
        except Exception as e:
            print(f"⚠️ Error al cargar sesión: {e}")

    def save_session(self):
        try:
            open_files = []
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if hasattr(tab, 'file_path') and tab.file_path and not getattr(tab, 'is_welcome', False):
                    open_files.append(tab.file_path)

            session_data = {
                "root": self.root_dir,
                "theme": self.current_theme,
                "open_files": open_files,
                "current_tab": self.tabs.currentIndex()
            }
            with open(get_app_path("session.json"), 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error al guardar sesión: {e}")

    # ----------------------------------------------------------------------
    #  SIDEBAR Y ARCHIVOS
    # ----------------------------------------------------------------------
    def init_sidebar_for_path(self, path):
        if path is None:
            self.root_dir = None
            self.sidebar_widget.set_project_path(None)
            self.setWindowTitle(f"{self.app_name} {self.app_version}".strip())
        else:
            self.root_dir = os.path.abspath(path)
            self.sidebar_widget.set_project_path(self.root_dir)
            self.setWindowTitle(f"{self.app_name} {self.app_version} - {os.path.basename(self.root_dir)}")

    def on_file_click(self, index):
        path = self.sidebar_widget.tree_view.model().filePath(index)
        if os.path.isfile(path):
            self.open_file(path)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Abrir Proyecto")
        if path:
            self.init_sidebar_for_path(path)
            self.save_session()

    # ----------------------------------------------------------------------
    #  PESTAÑAS DEL EDITOR
    # ----------------------------------------------------------------------
    def add_tab(self, path=None, content=""):
        """Añade una nueva pestaña con el editor."""
        if self.tabs.count() == 1 and getattr(self.tabs.widget(0), 'is_welcome', False):
            self.tabs.removeTab(0)
        t = EditorTab(self.tabs, path, content, self.current_theme, self.font_size, self.tab_width)
        i = self.tabs.addTab(t, t.get_title())
        self.tabs.setCurrentIndex(i)
        t.editor.cursorPositionChanged.connect(self.update_status)
        return t

    def open_file(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Abrir")
        if not path:
            return
        for i in range(self.tabs.count()):
            if getattr(self.tabs.widget(i), 'file_path', None) == path:
                self.tabs.setCurrentIndex(i)
                self.tabs.currentWidget().editor.setFocus()
                return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                t = self.add_tab(path, f.read())
                try:
                    from pygments.lexers import get_lexer_for_filename
                    lexer = get_lexer_for_filename(path)
                    t.editor.set_code_language(lexer.aliases[0])
                except:
                    t.editor.set_code_language("text")
                t.editor.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def close_current_tab(self, i=None):
        idx = i if i is not None else self.tabs.currentIndex()
        if idx != -1:
            self.tabs.removeTab(idx)

    def on_tab_change(self, i):
        t = self.tabs.currentWidget()
        if t:
            t.editor.apply_theme(self.current_theme)
            self.update_status()

    def update_tab_title(self, tab):
        self.tabs.setTabText(self.tabs.indexOf(tab), f"{'*' if not tab.saved else ''}{tab.get_title()}")

    def show_welcome_tab(self):
        ws = self.config.get('welcome_screen', {})
        title = ws.get('welcome_title', 'Bienvenido')
        features = ws.get('features_list', [])
        content = f"{title}\n\n" + "\n".join(features)
        t = self.add_tab(None, content)
        t.is_welcome = True
        t.editor.setReadOnly(True)
        t.saved = True
        self.tabs.setTabText(self.tabs.indexOf(t), "Inicio")

    # ----------------------------------------------------------------------
    #  BARRA DE ESTADO
    # ----------------------------------------------------------------------
    def setup_status_bar(self):
        self.status_bar = self.statusBar()
        self.lbl_lang = QLabel("Texto")
        self.lbl_cursor = QLabel("Ln 1, Col 1")
        self.status_bar.addPermanentWidget(self.lbl_lang)
        self.status_bar.addPermanentWidget(self.lbl_cursor)

    def update_status(self):
        t = self.tabs.currentWidget()
        if t and not getattr(t, 'is_welcome', False):
            c = t.editor.textCursor()
            self.lbl_cursor.setText(f"Ln {c.blockNumber() + 1}, Col {c.columnNumber() + 1}")
            self.lbl_lang.setText(t.editor.current_lang.upper())

    # ----------------------------------------------------------------------
    #  ACCIONES DE ARCHIVO
    # ----------------------------------------------------------------------
    def create_new_file_global(self):
        if hasattr(self.sidebar_widget, 'tree_view'):
            self.sidebar_widget.tree_view.new_item(self.root_dir, False)

    def create_new_folder_global(self):
        if hasattr(self.sidebar_widget, 'tree_view'):
            self.sidebar_widget.tree_view.new_item(self.root_dir, True)

    def save_current_file(self):
        self.auto_save()

    def save_file_as(self):
        t = self.tabs.currentWidget()
        if not t:
            return
        start_dir = self.root_dir if self.root_dir else ""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", start_dir)
        if path:
            t.file_path = path
            self.save_current_file()
            t.editor.file_path = path
            self.update_tab_title(t)
            try:
                from pygments.lexers import get_lexer_for_filename
                t.editor.set_code_language(get_lexer_for_filename(path).aliases[0])
            except:
                pass

    def auto_save(self):
        for i in range(self.tabs.count()):
            t = self.tabs.widget(i)
            if not getattr(t, 'is_welcome', False) and t.file_path and not t.saved:
                try:
                    with open(t.file_path, 'w', encoding='utf-8') as f:
                        f.write(t.editor.toPlainText())
                        t.saved = True
                        self.update_tab_title(t)
                except:
                    pass

    # ----------------------------------------------------------------------
    #  OTRAS FUNCIONALIDADES
    # ----------------------------------------------------------------------
    def show_shortcuts_dialog(self):
        dlg = ShortcutsDialog(THEMES.get(self.current_theme, {}), self)
        dlg.exec()

    def show_about(self):
        dlg = AboutDialog(self.config, THEMES.get(self.current_theme, {}), icon_path, self)
        dlg.exec()

    def show_global_search(self):
        GlobalSearchDialog(self.root_dir, self).exec()

    def toggle_console(self):
        if self.term.isVisible():
            self.term.hide()
        else:
            self.term.show()

    def run_current_file(self):
        t = self.tabs.currentWidget()
        if t and t.file_path:
            self.term.run_script(t.file_path)

    def toggle_autosave(self, enabled):
        self.autosave_enabled = enabled

    def toggle_local_search(self):
        self.search.setVisible(not self.search.isVisible())

    def change_font_size(self, size):
        self.font_size = size
        for i in range(self.tabs.count()):
            self.tabs.widget(i).editor.update_font(size, self.tab_width)

    def zoom_in(self):
        t = self.tabs.currentWidget()
        if t:
            t.editor.zoomIn(1)

    def zoom_out(self):
        t = self.tabs.currentWidget()
        if t:
            t.editor.zoomOut(1)

    def go_to_line(self):
        t = self.tabs.currentWidget()
        if t:
            line, ok = QInputDialog.getInt(self, "Ir a", "Línea:", 1, 1, t.editor.blockCount())
            if ok:
                c = t.editor.textCursor()
                c.movePosition(QTextCursor.Start)
                c.movePosition(QTextCursor.Down, n=line - 1)
                t.editor.setTextCursor(c)
                t.editor.centerCursor()
                t.editor.setFocus()

    def toggle_minimap_global(self):
        self.minimap_enabled = not self.minimap_enabled
        for i in range(self.tabs.count()):
            self.tabs.widget(i).minimap.setVisible(self.minimap_enabled)

    # ----------------------------------------------------------------------
    #  TEMAS
    # ----------------------------------------------------------------------
    def apply_theme(self, name):
        self.current_theme = name
        colors = THEMES.get(name, THEMES['Dark'])
        style = f"""
            QMainWindow, QDialog {{
                background-color: {colors['window_bg']};
                color: {colors['fg']};
            }}
            QMenuBar {{
                background-color: {colors['window_bg']};
                color: {colors['fg']};
            }}
            QMenuBar::item:selected {{
                background-color: {colors['select_bg']};
                color: {colors['bg']};
            }}
            QMenu {{
                background-color: {colors['window_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['splitter']};
            }}
            QMenu::item:selected {{
                background-color: {colors['select_bg']};
                color: {colors['bg']};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['splitter']};
            }}
            QTabBar::tab {{
                background: {colors['window_bg']};
                color: {colors['fg']};
                padding: 6px 14px;
                border: 1px solid {colors['splitter']};
            }}
            QTabBar::tab:selected {{
                background: {colors['bg']};
                border-bottom: 2px solid {colors['select_bg']};
                font-weight: bold;
            }}
            QStatusBar {{
                background-color: {colors['select_bg']};
                color: {colors['bg'] if name == 'Light' else colors['fg']};
            }}
            QStatusBar QLabel {{
                color: {colors['bg'] if name == 'Light' else colors['fg']};
            }}
            QPushButton {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                border: 1px solid {colors['splitter']};
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors['line_bg']};
            }}
            QInputDialog {{
                background-color: {colors['window_bg']};
                color: {colors['fg']};
            }}
            QInputDialog QLabel {{
                color: {colors['fg']};
            }}
            QInputDialog QLineEdit {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                border: 1px solid {colors['splitter']};
                padding: 2px;
            }}
            QInputDialog QPushButton {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                border: 1px solid {colors['splitter']};
                padding: 4px 10px;
            }}
            QInputDialog QPushButton:hover {{
                background-color: {colors['line_bg']};
            }}
            QMessageBox {{
                background-color: {colors['window_bg']};
                color: {colors['fg']};
            }}
            QMessageBox QLabel {{
                color: {colors['fg']};
            }}
            QMessageBox QPushButton {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                border: 1px solid {colors['splitter']};
                padding: 4px 10px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {colors['line_bg']};
            }}
        """
        self.setStyleSheet(style)
        QApplication.instance().setStyleSheet(style)

        self.sidebar_widget.update_theme(colors)
        self.term.update_theme(colors)
        for i in range(self.tabs.count()):
            self.tabs.widget(i).editor.apply_theme(name)
            self.tabs.widget(i).minimap.apply_theme(colors)

        self.save_session()

    # ----------------------------------------------------------------------
    #  CIERRE
    # ----------------------------------------------------------------------
    def closeEvent(self, e):
        if hasattr(self, 'term'):
            self.term.stop_process()
        self.save_session()
        e.accept()


# ==============================================================================
#  PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName("CapiEditor")
    app.setDesktopFileName("capi-editor")  # Sin .desktop

    try:
        with open(get_app_path("config.json"), 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            icon_name = cfg.get("app_settings", {}).get("icon_path", "capieditor.png")
            app.setWindowIcon(QIcon(get_app_path(icon_name)))
    except:
        app.setWindowIcon(QIcon(icon_path))

    window = CapiEditor()
    window.show()
    sys.exit(app.exec())