import os
import shutil
from PySide6.QtCore import Qt, QDir
from PySide6.QtWidgets import (QFileSystemModel, QTreeView, QMenu, QInputDialog,
                               QMessageBox, QWidget, QVBoxLayout, QPushButton,
                               QSizePolicy, QLabel)
from PySide6.QtGui import QFont

class FileSystemModel(QFileSystemModel):
    """Modelo con iconos emoji para archivos."""
    def __init__(self):
        super().__init__()
        self.icon_map = {
            ".py": "🐍", ".pyw": "🐍", ".js": "📜", ".json": "📋",
            ".html": "🌐", ".css": "🎨", ".md": "📝", ".txt": "📄",
            ".cpp": "⚙️", ".c": "⚙️", ".java": "☕", ".php": "🐘",
            ".git": "🛑"
        }

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            return None
        if role == Qt.DisplayRole:
            original = super().data(index, role)
            info = self.fileInfo(index)
            if info.isDir():
                return f"📂 {original}"
            ext = info.suffix().lower()
            icon = self.icon_map.get(f".{ext}", "📄")
            return f"{icon} {original}"
        return super().data(index, role)


class FileTreeView(QTreeView):
    """Vista de árbol personalizada."""
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
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectRows)
        self.setFocusPolicy(Qt.StrongFocus)

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        model = self.model()
        if not model:
            return
        path = model.filePath(index) if index.isValid() else model.rootPath()
        if os.path.isfile(path):
            path = os.path.dirname(path)

        menu = QMenu()
        menu.addAction("📄 Nuevo Archivo", lambda: self.new_item(path, False))
        menu.addAction("📁 Nueva Carpeta", lambda: self.new_item(path, True))
        menu.addSeparator()
        if index.isValid():
            menu.addAction("✏️ Renombrar", lambda: self.rename_item(model.filePath(index)))
            menu.addAction("🗑️ Eliminar", lambda: self.delete_item(model.filePath(index)))
        menu.exec(self.viewport().mapToGlobal(pos))

    def new_item(self, path, is_folder):
        tipo = "carpeta" if is_folder else "archivo"
        name, ok = QInputDialog.getText(self, f"Nuevo {tipo}", f"Nombre del {tipo}:")
        if ok and name:
            try:
                full = os.path.join(path, name)
                if is_folder:
                    os.makedirs(full, exist_ok=True)
                else:
                    with open(full, 'a'): pass
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def rename_item(self, path):
        old = os.path.basename(path)
        new, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=old)
        if ok and new:
            try:
                os.rename(path, os.path.join(os.path.dirname(path), new))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_item(self, path):
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {os.path.basename(path)}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def update_theme(self, colors):
        """Aplica los colores del tema al árbol."""
        self.setStyleSheet(f"""
            QTreeView {{
                background-color: {colors['bg']};
                color: {colors['fg']};
                border: none;
                font-size: 13px;
            }}
            QTreeView::item {{
                padding: 4px;
            }}
            QTreeView::item:hover {{
                background-color: {colors['line_bg']};
            }}
            QTreeView::item:selected {{
                background-color: {colors['select_bg']};
                color: white;
            }}
            QTreeView::item:selected:!active {{
                background-color: {colors['select_bg']};
                color: white;
            }}
        """)


class ProjectSidebar(QWidget):
    """Widget lateral que contiene el árbol y el botón de toggle."""
    def __init__(self, parent=None, no_project_message="No hay proyecto asignado"):
        super().__init__(parent)
        self.no_project_message = no_project_message
        self.root_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Botón de toggle (sin foco)
        self.toggle_btn = QPushButton("▼ Proyecto")
        self.toggle_btn.setObjectName("toggleButton")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setToolTip("Ocultar/Mostrar archivos")
        self.toggle_btn.setMinimumHeight(35)
        font = QFont()
        font.setBold(True)
        self.toggle_btn.setFont(font)
        self.toggle_btn.setFocusPolicy(Qt.NoFocus)
        self.toggle_btn.clicked.connect(self.toggle_view)
        self.toggle_btn.setStyleSheet("""
            QPushButton#toggleButton {
                text-align: left;
                padding-left: 8px;
                padding-right: 8px;
                border: none;
                background-color: #2d2d2d;
                color: white;
                font-weight: bold;
            }
            QPushButton#toggleButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton#toggleButton:pressed {
                background-color: #1d1d1d;
            }
        """)

        # Árbol de archivos
        self.tree_view = FileTreeView()
        self.tree_view.setVisible(False)

        # Etiqueta para cuando no hay proyecto
        self.no_project_label = QLabel(self.no_project_message)
        self.no_project_label.setAlignment(Qt.AlignCenter)
        self.no_project_label.setWordWrap(True)
        self.no_project_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        self.no_project_label.setVisible(True)

        # Espaciador (para cuando el árbol está oculto con proyecto)
        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.spacer.setVisible(False)

        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.tree_view)
        layout.addWidget(self.no_project_label)
        layout.addWidget(self.spacer)

        self.model = None

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
            self.tree_view.setFocus()

    def set_project_path(self, path):
        if path is None:
            self.root_path = None
            self.tree_view.setModel(None)
            self.tree_view.hide()
            self.spacer.hide()
            self.no_project_label.show()
            self.toggle_btn.setText("No project")
            self.toggle_btn.setEnabled(False)
            return

        self.root_path = os.path.abspath(path)
        self.toggle_btn.setEnabled(True)
        self.no_project_label.hide()

        self.model = FileSystemModel()
        self.model.setRootPath(self.root_path)
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        self.model.setNameFilters(["!__pycache__", "!*.pyc", ".*"])

        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        for i in range(1, 4):
            self.tree_view.hideColumn(i)

        self.spacer.hide()
        self.tree_view.show()
        self.toggle_btn.setText(f"▼ {os.path.basename(self.root_path)}")
        self.tree_view.setFocus()

    def update_theme(self, colors):
        self.tree_view.update_theme(colors)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton#toggleButton {{
                text-align: left;
                padding-left: 8px;
                padding-right: 8px;
                border: none;
                background-color: {colors['bg']};
                color: {colors['fg']};
                font-weight: bold;
                border-bottom: 1px solid {colors['splitter']};
            }}
            QPushButton#toggleButton:hover {{
                background-color: {colors['line_bg']};
            }}
            QPushButton#toggleButton:pressed {{
                background-color: {colors['select_bg']};
                color: white;
            }}
        """)
        self.no_project_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['fg']};
                background-color: {colors['bg']};
                font-size: 14px;
                padding: 20px;
                border: none;
            }}
        """)
