#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de barra lateral (Sidebar) para Capi Editor Pro.
Proporciona un explorador de archivos con árbol, botón de proyecto,
menús contextuales en español, iconos personalizados por extensión,
solo vista de nombres y movimiento de archivos al arrastrar.
"""

import os
import shutil

from PySide6.QtCore import Qt, QModelIndex, Signal, QSortFilterProxyModel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QToolButton, QMenu,
    QFileSystemModel, QMessageBox
)


class MovableFileSystemModel(QFileSystemModel):
    """
    Modelo de sistema de archivos que permite mover archivos al arrastrar.
    Se reimplementan los métodos necesarios para soportar acciones de copiar y mover.
    """

    def supportedDropActions(self):
        """Indica que se soportan acciones de copiar y mover."""
        return Qt.CopyAction | Qt.MoveAction

    def dropMimeData(self, data, action, row, column, parent):
        """
        Reimplementado para que MoveAction mueva los archivos en lugar de copiarlos.
        """
        if action == Qt.MoveAction:
            urls = data.urls()
            if not urls:
                return False

            dest_path = self.filePath(parent) if parent.isValid() else self.rootPath()
            if not dest_path or not os.path.isdir(dest_path):
                return False

            success = True
            for url in urls:
                src_path = url.toLocalFile()
                if not src_path or not os.path.exists(src_path):
                    continue
                # Evitar mover sobre sí mismo (mismo directorio)
                if os.path.dirname(src_path) == dest_path:
                    continue
                dest_file = os.path.join(dest_path, os.path.basename(src_path))
                try:
                    shutil.move(src_path, dest_file)
                except Exception as e:
                    print(f"Error moviendo {src_path} a {dest_file}: {e}")
                    success = False
            return success
        else:
            return super().dropMimeData(data, action, row, column, parent)


class FileSystemProxyModel(QSortFilterProxyModel):
    """
    Modelo proxy que personaliza los iconos según la extensión del archivo.
    Para las extensiones no incluidas en el mapa, se usa el icono por defecto del sistema.
    """

    def __init__(self, icon_map=None, parent=None):
        super().__init__(parent)
        self.icon_map = icon_map or {}

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            source_index = self.mapToSource(index)
            file_path = self.sourceModel().filePath(source_index)
            if not os.path.isdir(file_path):
                ext = os.path.splitext(file_path)[1].lower().lstrip('.')
                if ext in self.icon_map:
                    return self.icon_map[ext]
        return super().data(index, role)


class ProjectSidebar(QWidget):
    """
    Barra lateral que muestra el árbol de archivos del proyecto actual.
    Incluye un botón con el nombre de la raíz, menús contextuales (clic derecho)
    y operaciones de archivo/carpeta.
    """

    projectChanged = Signal(str)

    def __init__(self, parent, no_project_message="No hay proyecto asignado"):
        super().__init__(parent)
        self.parent = parent
        self.no_project_message = no_project_message
        self.current_root = None
        self.source_model = None
        self.proxy_model = None
        self.clipboard_path = None
        self.cut_mode = False
        self.icon_map = {}

        self.load_icons()
        self.setup_ui()
        self.setup_connections()

    def load_icons(self):
        basedir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(basedir, "icons")
        if not os.path.isdir(icons_dir):
            try:
                os.mkdir(icons_dir)
                print(f"📁 Creada carpeta 'icons' en {basedir}. Coloca ahí tus iconos (ej: py.png, php.png).")
            except Exception as e:
                print(f"⚠️ No se pudo crear la carpeta 'icons': {e}")
            return

        for file in os.listdir(icons_dir):
            file_path = os.path.join(icons_dir, file)
            if os.path.isfile(file_path):
                name, ext = os.path.splitext(file)
                icon = QIcon(file_path)
                if not icon.isNull():
                    self.icon_map[name.lower()] = icon
                    print(f"✅ Icono cargado para extensión .{name.lower()}")
                else:
                    print(f"⚠️ No se pudo cargar el icono: {file_path}")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.project_btn = QToolButton()
        self.project_btn.setText(self.no_project_message)
        self.project_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.project_btn.setPopupMode(QToolButton.InstantPopup)
        self.project_btn.setAutoRaise(True)
        self.project_btn.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.project_btn)

        self._tree_view = QTreeView()
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setEditTriggers(QTreeView.EditKeyPressed)
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self._tree_view.setDragEnabled(True)
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDropIndicatorShown(True)
        self._tree_view.setDefaultDropAction(Qt.MoveAction)  # Acción por defecto: mover
        layout.addWidget(self._tree_view)

        # Usar modelo con soporte de movimiento
        self.source_model = MovableFileSystemModel()
        self.source_model.setReadOnly(False)

        self.proxy_model = FileSystemProxyModel(self.icon_map, self)
        self.proxy_model.setSourceModel(self.source_model)

        self._tree_view.setModel(self.proxy_model)

    def setup_connections(self):
        self._tree_view.customContextMenuRequested.connect(self.show_context_menu)

    # ----------------------------------------------------------------------
    # API pública
    # ----------------------------------------------------------------------
    def set_project_path(self, path):
        self.current_root = path

        if path and os.path.isdir(path):
            self.source_model.setRootPath(path)
            root_index = self.source_model.index(path)
            proxy_root = self.proxy_model.mapFromSource(root_index)
            self._tree_view.setRootIndex(proxy_root)

            for col in range(1, self.source_model.columnCount()):
                self._tree_view.setColumnHidden(col, True)

            self.project_btn.setText(os.path.basename(path))
            self._tree_view.expand(proxy_root)
        else:
            self._tree_view.setRootIndex(QModelIndex())
            self.project_btn.setText(self.no_project_message)

        self.projectChanged.emit(path if path else "")

    def update_theme(self, colors):
        style = f"""
            QWidget {{
                background-color: {colors.get('window_bg', '#252526')};
                color: {colors.get('fg', '#d4d4d4')};
            }}
            QToolButton {{
                background-color: {colors.get('bg', '#1e1e1e')};
                color: {colors.get('fg', '#d4d4d4')};
                border: none;
                padding: 6px;
                text-align: left;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {colors.get('line_bg', '#2d2d30')};
            }}
            QTreeView {{
                background-color: {colors.get('bg', '#1e1e1e')};
                color: {colors.get('fg', '#d4d4d4')};
                border: none;
                outline: none;
            }}
            QTreeView::item:selected {{
                background-color: {colors.get('select_bg', '#094771')};
                color: {colors.get('fg', '#d4d4d4')};
            }}
            QTreeView::item:hover {{
                background-color: {colors.get('line_bg', '#2d2d30')};
            }}
            QMenu {{
                background-color: {colors.get('window_bg', '#252526')};
                color: {colors.get('fg', '#d4d4d4')};
                border: 1px solid {colors.get('splitter', '#3e3e42')};
            }}
            QMenu::item:selected {{
                background-color: {colors.get('select_bg', '#094771')};
                color: {colors.get('fg', '#d4d4d4')};
            }}
        """
        self.setStyleSheet(style)

    # ----------------------------------------------------------------------
    # Menú contextual
    # ----------------------------------------------------------------------
    def show_context_menu(self, pos):
        proxy_index = self._tree_view.indexAt(pos)
        if not proxy_index.isValid() and self.current_root is None:
            return

        menu = QMenu(self)

        new_file_action = QAction("Nuevo archivo", self)
        new_file_action.triggered.connect(lambda: self.new_item(self.get_target_dir(proxy_index), is_dir=False))
        menu.addAction(new_file_action)

        new_folder_action = QAction("Nueva carpeta", self)
        new_folder_action.triggered.connect(lambda: self.new_item(self.get_target_dir(proxy_index), is_dir=True))
        menu.addAction(new_folder_action)

        menu.addSeparator()

        if proxy_index.isValid():
            source_index = self.proxy_model.mapToSource(proxy_index)
            path = self.source_model.filePath(source_index)
            is_dir = self.source_model.isDir(source_index)

            copy_action = QAction("Copiar", self)
            copy_action.triggered.connect(lambda: self.copy_path(path))
            menu.addAction(copy_action)

            cut_action = QAction("Cortar", self)
            cut_action.triggered.connect(lambda: self.cut_path(path))
            menu.addAction(cut_action)

            if self.clipboard_path is not None:
                paste_action = QAction("Pegar", self)
                paste_action.triggered.connect(lambda: self.paste_into(self.get_target_dir(proxy_index)))
                menu.addAction(paste_action)

            menu.addSeparator()

            rename_action = QAction("Renombrar", self)
            rename_action.triggered.connect(lambda: self._tree_view.edit(proxy_index))
            menu.addAction(rename_action)

            delete_action = QAction("Eliminar", self)
            delete_action.triggered.connect(lambda: self.delete_path(path))
            menu.addAction(delete_action)

            menu.addSeparator()

            if is_dir:
                open_terminal_action = QAction("Abrir en terminal", self)
                if hasattr(self.parent, 'term') and hasattr(self.parent.term, 'change_directory'):
                    open_terminal_action.triggered.connect(lambda: self.parent.term.change_directory(path))
                menu.addAction(open_terminal_action)

        menu.exec(self._tree_view.viewport().mapToGlobal(pos))

    def get_target_dir(self, proxy_index):
        if self.current_root is None:
            return None
        if proxy_index.isValid():
            source_index = self.proxy_model.mapToSource(proxy_index)
            path = self.source_model.filePath(source_index)
            if self.source_model.isDir(source_index):
                return path
            else:
                return os.path.dirname(path)
        else:
            return self.current_root

    # ----------------------------------------------------------------------
    # Operaciones de archivo
    # ----------------------------------------------------------------------
    def new_item(self, parent_path, is_dir=False):
        if not parent_path or not os.path.isdir(parent_path):
            return

        if is_dir:
            base_name = "nueva_carpeta"
            folder_name = base_name
            counter = 1
            while os.path.exists(os.path.join(parent_path, folder_name)):
                folder_name = f"{base_name}_{counter}"
                counter += 1

            source_parent = self.source_model.index(parent_path)
            new_source_index = self.source_model.mkdir(source_parent, folder_name)
            if new_source_index.isValid():
                new_proxy_index = self.proxy_model.mapFromSource(new_source_index)
                self._tree_view.edit(new_proxy_index)
        else:
            base_name = "nuevo_archivo.txt"
            file_name = base_name
            counter = 1
            while os.path.exists(os.path.join(parent_path, file_name)):
                name, ext = os.path.splitext(base_name)
                file_name = f"{name}_{counter}{ext}"
                counter += 1

            file_path = os.path.join(parent_path, file_name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                source_index = self.source_model.index(file_path)
                if source_index.isValid():
                    proxy_index = self.proxy_model.mapFromSource(source_index)
                    self._tree_view.edit(proxy_index)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el archivo:\n{e}")

    def copy_path(self, path):
        self.clipboard_path = path
        self.cut_mode = False

    def cut_path(self, path):
        self.clipboard_path = path
        self.cut_mode = True

    def paste_into(self, target_dir):
        if not self.clipboard_path or not target_dir or not os.path.exists(self.clipboard_path):
            return

        src = self.clipboard_path
        dst = os.path.join(target_dir, os.path.basename(src))

        if os.path.exists(dst):
            reply = QMessageBox.question(
                self, "Confirmar",
                f"El archivo o carpeta '{os.path.basename(dst)}' ya existe.\n¿Sobrescribir?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            try:
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el destino:\n{e}")
                return

        try:
            if self.cut_mode:
                shutil.move(src, dst)
                self.clipboard_path = None
            else:
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo pegar:\n{e}")

    def delete_path(self, path):
        if not os.path.exists(path):
            return

        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro de eliminar '{os.path.basename(path)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    # ----------------------------------------------------------------------
    # Integración con el core
    # ----------------------------------------------------------------------
    def new_item_at_root(self, is_dir=False):
        if self.current_root:
            self.new_item(self.current_root, is_dir)

    @property
    def tree_view(self):
        return self._tree_view