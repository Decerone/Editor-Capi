import os
import shutil
from PySide6.QtCore import Qt, QDir
from PySide6.QtWidgets import (QFileSystemModel, QTreeView, QMenu, QInputDialog, 
                               QMessageBox, QWidget, QVBoxLayout, QPushButton, 
                               QSizePolicy, QLabel)
from PySide6.QtGui import QFont

# =========================================================================
#  1. MODELO DE DATOS 2.0
# =========================================================================
class EmojiFileSystemModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.icon_map = {
            ".py": "🐍", ".pyw": "🐍", ".js": "📜", ".json": "📋",
            ".html": "🌐", ".css": "🎨", ".md": "📝", ".txt": "📄",
            ".cpp": "⚙️", ".c": "⚙️", ".java": "☕", ".php": "🐘",
            ".git": "🛑"
        }

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole: return None 
        if role == Qt.DisplayRole:
            original = super().data(index, role)
            info = self.fileInfo(index)
            if info.isDir(): return f"📂 {original}"
            icon = self.icon_map.get(f".{info.suffix().lower()}", "📄")
            return f"{icon} {original}"
        return super().data(index, role)

# =========================================================================
#  2. ÁRBOL DE ARCHIVOS
# =========================================================================
class FileSidebar(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setHeaderHidden(True)
        self.setIndentation(15)
        self.setAnimated(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setEditTriggers(QTreeView.NoEditTriggers)

    def update_theme(self, c):
        self.setStyleSheet(f"""
            QTreeView {{ background-color: {c['bg']}; color: {c['fg']}; border: none; font-size: 13px; }}
            QTreeView::item {{ padding: 4px; }}
            QTreeView::item:hover {{ background-color: {c['line_bg']}; }}
            QTreeView::item:selected {{ background-color: {c['select_bg']}; color: white; }}
        """)

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        model = self.model()
        if not model: return
        
        path = model.filePath(index) if index.isValid() else model.rootPath()
        if os.path.isfile(path): path = os.path.dirname(path)

        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #2d2d2d; color: white; border: 1px solid #454545; }")
        menu.addAction("📄 Nuevo Archivo", lambda: self.new_item(path, False))
        menu.addAction("📁 Nueva Carpeta", lambda: self.new_item(path, True))
        menu.addSeparator()
        if index.isValid():
            menu.addAction("✏️ Renombrar", lambda: self.rename_item(model.filePath(index)))
            menu.addAction("🗑️ Eliminar", lambda: self.delete_item(model.filePath(index)))
        menu.exec(self.viewport().mapToGlobal(pos))

    def new_item(self, path, is_folder):
        t = "Carpeta" if is_folder else "Archivo"
        name, ok = QInputDialog.getText(self, f"Nueva {t}", f"Nombre:")
        if ok and name:
            try:
                p = os.path.join(path, name)
                if is_folder: os.makedirs(p, exist_ok=True)
                else: open(p, 'a').close()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def rename_item(self, path):
        old = os.path.basename(path); new, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=old)
        if ok and new:
            try: os.rename(path, os.path.join(os.path.dirname(path), new))
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def delete_item(self, path):
        if QMessageBox.question(self, "Eliminar", f"¿Borrar {os.path.basename(path)}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            try: 
                if os.path.isdir(path): shutil.rmtree(path)
                else: os.remove(path)
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

# =========================================================================
#  3. WRAPPER (MODIFICADO: Recibe mensaje personalizado)
# =========================================================================
class ProjectSidebarWrapper(QWidget):
    def __init__(self, parent=None, no_project_message="No hay proyecto asignado"):
        super().__init__(parent)
        self.no_project_message = no_project_message  # Guardar mensaje
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Botón de toggle
        self.toggle_btn = QPushButton("▼ Proyecto")
        self.toggle_btn.setObjectName("btn_project")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setToolTip("Ocultar/Mostrar archivos")
        self.toggle_btn.setMinimumHeight(35)
        font = QFont()
        font.setBold(True)
        self.toggle_btn.setFont(font)
        
        self.toggle_btn.setStyleSheet("""
            QPushButton#btn_project {
                text-align: left;
                padding-left: 8px;
                padding-right: 8px;
                border: none;
                background-color: #2d2d2d;
                color: white;
                font-weight: bold;
            }
            QPushButton#btn_project:hover {
                background-color: #3d3d3d;
            }
            QPushButton#btn_project:pressed {
                background-color: #1d1d1d;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_view)
        
        self.tree_view = FileSidebar()
        
        # Label para cuando no hay proyecto
        self.no_project_label = QLabel(self.no_project_message)  # Usar mensaje
        self.no_project_label.setAlignment(Qt.AlignCenter)
        self.no_project_label.setWordWrap(True)
        self.no_project_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
                padding: 20px;
            }
        """)
        self.no_project_label.hide()
        
        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.spacer.hide()
        
        self.layout.addWidget(self.toggle_btn)
        self.layout.addWidget(self.tree_view)
        self.layout.addWidget(self.no_project_label)
        self.layout.addWidget(self.spacer)
        
        self.root_path = None
        self.f_model = None

    def toggle_view(self):
        if self.root_path is None:
            return
        if self.tree_view.isVisible():
            self.tree_view.hide()
            self.spacer.show()
            self.toggle_btn.setText(f"▶ {os.path.basename(self.root_path)}")
        else:
            self.spacer.hide()
            self.tree_view.show()
            self.toggle_btn.setText(f"▼ {os.path.basename(self.root_path)}")

    def set_project_path(self, path):
        if path is None:
            self.root_path = None
            self.tree_view.setModel(None)
            self.tree_view.hide()
            self.spacer.hide()
            self.no_project_label.setText(self.no_project_message)  # Actualizar por si cambió
            self.no_project_label.show()
            self.toggle_btn.setText("No project")
            self.toggle_btn.setEnabled(False)
            return
        
        self.root_path = os.path.abspath(path)
        self.toggle_btn.setEnabled(True)
        self.no_project_label.hide()
        
        self.f_model = EmojiFileSystemModel()
        self.f_model.setRootPath(self.root_path)
        self.f_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        self.f_model.setNameFilters(["!__pycache__", "!*.pyc", ".*"])
        
        self.tree_view.setModel(self.f_model)
        for i in range(1, 4): 
            self.tree_view.hideColumn(i)
        
        self.f_model.directoryLoaded.connect(lambda p: self.on_directory_loaded(p))
        
        self.spacer.hide()
        self.tree_view.show()
        self.toggle_btn.setText(f"▼ {os.path.basename(self.root_path)}")

    def on_directory_loaded(self, loaded_path):
        if self.root_path and os.path.abspath(loaded_path) == self.root_path:
            idx = self.f_model.index(self.root_path)
            if idx.isValid(): 
                self.tree_view.setRootIndex(idx)

    def update_theme(self, c):
        self.tree_view.update_theme(c)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton#btn_project {{
                text-align: left;
                padding-left: 8px;
                padding-right: 8px;
                border: none;
                background-color: {c['bg']};
                color: {c['fg']};
                font-weight: bold;
                border-bottom: 1px solid {c['splitter']};
            }}
            QPushButton#btn_project:hover {{
                background-color: {c['line_bg']};
            }}
            QPushButton#btn_project:pressed {{
                background-color: {c['select_bg']};
                color: {c.get('select_fg', 'white')};
            }}
        """)
        self.no_project_label.setStyleSheet(f"""
            QLabel {{
                color: {c['fg']};
                background-color: {c['bg']};
                font-size: 14px;
                padding: 20px;
                border: none;
            }}
        """)