import os
import shutil
from PySide6.QtWidgets import QTreeView, QFileSystemModel, QMenu, QMessageBox, QInputDialog, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QAction

def get_file_emoji(file_name, is_dir):
    if is_dir: return "📁"
    ext = os.path.splitext(file_name)[1].lower()
    emoji_map = {
        '.py': '🐍', '.php': '🐘', '.html': '🌐', '.css': '🎨', '.js': '📜', 
        '.json': '🔧', '.sql': '🗄️', '.txt': '📄', '.md': '📝', '.c': '🇨', 
        '.cpp': '🇨', '.java': '☕', '.sh': '💻', '.png': '🖼️', '.zip': '📦', '.rs': '🦀'
    }
    return emoji_map.get(ext, "📄")

def emoji_to_icon(emoji_char):
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setFont(QFont("Segoe UI Emoji", 14)) 
    painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji_char)
    painter.end()
    return QIcon(pixmap)

class EmojiFileSystemModel(QFileSystemModel):
    def data(self, index, role):
        if role == Qt.DecorationRole and index.isValid():
            file_name = self.fileName(index)
            is_dir = self.isDir(index)
            # --- CORRECCIÓN: Si el nombre está vacío (raíz) o es dir, forzar carpeta ---
            if is_dir or not file_name:
                return emoji_to_icon("📁")
            return emoji_to_icon(get_file_emoji(file_name, is_dir))
        return super().data(index, role)

class FileSidebar(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.clipboard_path = None
        self.clipboard_action = None 
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def update_theme(self, colors):
        bg = colors.get('bg', '#252526')
        fg = colors.get('fg', '#cccccc')
        sel_bg = colors.get('select_bg', '#37373d')
        self.setStyleSheet(f"""
            QTreeView {{ background-color: {bg}; color: {fg}; border: none; font-size: 13px; outline: none; }}
            QTreeView::item {{ padding: 4px; }}
            QTreeView::item:hover {{ background-color: {sel_bg}80; }}
            QTreeView::item:selected {{ background-color: {sel_bg}; color: {fg}; }}
        """)

    def open_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid(): return
        path = self.model().filePath(index)
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #2d2d2d; color: white; border: 1px solid #3e3e42; } QMenu::item:selected { background-color: #094771; }")
        
        actions = [
            ("📄 Nuevo Archivo", lambda: self.new_file(path)),
            ("📁 Nueva Carpeta", lambda: self.new_folder(path)),
            ("sep", None),
            ("Cor&tar", lambda: self.cut_item_path(path)),
            ("Copi&ar", lambda: self.copy_item_path(path)),
            ("Pegar", lambda: self.paste_item(path)),
            ("sep", None),
            ("✏️ Renombrar", lambda: self.rename_item(index, path)),
            ("📋 Copiar Ruta", lambda: QApplication.clipboard().setText(path)),
            ("sep", None),
            ("🗑️ Eliminar", lambda: self.delete_item(index, path))
        ]

        for text, func in actions:
            if text == "sep": menu.addSeparator()
            else:
                act = QAction(text, self)
                act.triggered.connect(func)
                if text == "Pegar" and not self.clipboard_path: act.setEnabled(False)
                menu.addAction(act)
        
        menu.exec(self.viewport().mapToGlobal(position))

    def copy_item_path(self, path):
        self.clipboard_path = path; self.clipboard_action = 'copy'

    def cut_item_path(self, path):
        self.clipboard_path = path; self.clipboard_action = 'cut'

    def paste_item(self, target_path):
        if not self.clipboard_path or not os.path.exists(self.clipboard_path):
            return QMessageBox.warning(self, "Error", "Origen no existe.")
        dest_dir = os.path.dirname(target_path) if os.path.isfile(target_path) else target_path
        dest_path = os.path.join(dest_dir, os.path.basename(self.clipboard_path))
        if os.path.exists(dest_path): return QMessageBox.warning(self, "Alerta", "Ya existe.")
        try:
            if self.clipboard_action == 'copy':
                if os.path.isdir(self.clipboard_path): shutil.copytree(self.clipboard_path, dest_path)
                else: shutil.copy2(self.clipboard_path, dest_path)
            elif self.clipboard_action == 'cut':
                shutil.move(self.clipboard_path, dest_path)
                self.clipboard_path = None
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def new_file(self, path):
        dir_ = path if os.path.isdir(path) else os.path.dirname(path)
        name, ok = QInputDialog.getText(self, "Nuevo", "Nombre archivo:")
        if ok and name: open(os.path.join(dir_, name), 'w').close()

    def new_folder(self, path):
        dir_ = path if os.path.isdir(path) else os.path.dirname(path)
        name, ok = QInputDialog.getText(self, "Nuevo", "Nombre carpeta:")
        if ok and name: os.makedirs(os.path.join(dir_, name))

    def rename_item(self, index, path):
        name, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=os.path.basename(path))
        if ok and name: os.rename(path, os.path.join(os.path.dirname(path), name))

    def delete_item(self, index, path):
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {os.path.basename(path)}?") == QMessageBox.Yes:
            if os.path.isdir(path): shutil.rmtree(path)
            else: os.remove(path)