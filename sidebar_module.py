#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de barra lateral (Sidebar) para Capi Editor Pro.
Proporciona un explorador de archivos con árbol, botón de proyecto,
menús contextuales en español, iconos personalizados y solo vista de nombres.
"""

import os
import shutil

from PySide6.QtCore import Qt, QModelIndex, Signal, QSortFilterProxyModel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QToolButton, QMenu,
    QFileSystemModel, QMessageBox
)


class FileSystemProxyModel(QSortFilterProxyModel):
    """
    Modelo proxy que personaliza los iconos según la extensión del archivo.
    También puede filtrar si es necesario (aquí no se filtra).
    """

    def __init__(self, icon_map=None, parent=None):
        super().__init__(parent)
        self.icon_map = icon_map or {}

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            # Obtener la ruta del archivo desde el modelo fuente
            source_index = self.mapToSource(index)
            file_path = self.sourceModel().filePath(source_index)
            if not os.path.isdir(file_path):
                # Es archivo: obtener extensión
                ext = os.path.splitext(file_path)[1].lower().lstrip('.')
                if ext in self.icon_map:
                    return self.icon_map[ext]
        # Para cualquier otro rol, usar el modelo fuente
        return super().data(index, role)


class ProjectSidebar(QWidget):
    """
    Barra lateral que muestra el árbol de archivos del proyecto actual.
    Incluye un botón con el nombre de la raíz, menús contextuales (clic derecho)
    y operaciones de archivo/carpeta.
    """

    # Señal opcional para notificar cambios en el proyecto (no usada en core actual)
    projectChanged = Signal(str)

    def __init__(self, parent, no_project_message="No hay proyecto asignado"):
        super().__init__(parent)
        self.parent = parent
        self.no_project_message = no_project_message
        self.current_root = None
        self.source_model = None
        self.proxy_model = None
        self.clipboard_path = None      # Para copiar/cortar interno
        self.cut_mode = False            # True si es cortar, False si es copiar
        self.icon_map = {}                # Mapa extensión -> QIcon

        self.load_icons()
        self.setup_ui()
        self.setup_connections()

    def load_icons(self):
        """
        Escanea la carpeta 'icons' en el directorio base de la aplicación
        y carga los iconos disponibles. Se esperan archivos con nombre 'py.png',
        'txt.png', etc. (la extensión del archivo indica el tipo).
        """
        basedir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(basedir, "icons")
        if not os.path.isdir(icons_dir):
            # Si no existe la carpeta, no hay iconos personalizados
            return

        for file in os.listdir(icons_dir):
            file_path = os.path.join(icons_dir, file)
            if os.path.isfile(file_path):
                # El nombre del archivo (sin extensión) será la extensión a mapear
                name, ext = os.path.splitext(file)
                # Soportamos png, svg, ico, etc. (Qt puede cargar varios formatos)
                icon = QIcon(file_path)
                if not icon.isNull():
                    self.icon_map[name.lower()] = icon

    def setup_ui(self):
        """Crea los componentes visuales: botón y árbol."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Botón que muestra el nombre del proyecto
        self.project_btn = QToolButton()
        self.project_btn.setText(self.no_project_message)
        self.project_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.project_btn.setPopupMode(QToolButton.InstantPopup)  # Permite menú al hacer clic
        self.project_btn.setAutoRaise(True)
        self.project_btn.setFocusPolicy(Qt.NoFocus)  # El foco va al árbol
        layout.addWidget(self.project_btn)

        # Árbol de archivos
        self._tree_view = QTreeView()
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setEditTriggers(QTreeView.EditKeyPressed)  # F2 para renombrar
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self._tree_view.setDragEnabled(True)
        self._tree_view.setAcceptDrops(True)
        self._tree_view.setDropIndicatorShown(True)
        layout.addWidget(self._tree_view)

        # Crear modelo fuente (QFileSystemModel)
        self.source_model = QFileSystemModel()
        self.source_model.setReadOnly(False)   # Permitir operaciones de escritura

        # Crear modelo proxy con los iconos personalizados
        self.proxy_model = FileSystemProxyModel(self.icon_map, self)
        self.proxy_model.setSourceModel(self.source_model)

        # Asignar el modelo proxy al árbol (solo una vez)
        self._tree_view.setModel(self.proxy_model)

    def setup_connections(self):
        """Conecta señales internas."""
        self._tree_view.customContextMenuRequested.connect(self.show_context_menu)

    # ----------------------------------------------------------------------
    # API pública llamada desde el core
    # ----------------------------------------------------------------------
    def set_project_path(self, path):
        """
        Establece la ruta raíz del proyecto.
        Si path es None, limpia la vista y muestra el mensaje por defecto.
        """
        self.current_root = path

        if path and os.path.isdir(path):
            # Proyecto válido
            self.source_model.setRootPath(path)
            root_index = self.source_model.index(path)
            proxy_root = self.proxy_model.mapFromSource(root_index)
            self._tree_view.setRootIndex(proxy_root)

            # Ocultar todas las columnas excepto la primera (nombre)
            for col in range(1, self.source_model.columnCount()):
                self._tree_view.setColumnHidden(col, True)

            # Mostrar nombre de la carpeta en el botón
            self.project_btn.setText(os.path.basename(path))
            # Expandir nivel raíz opcionalmente
            self._tree_view.expand(proxy_root)
        else:
            # Sin proyecto: mantener el modelo pero sin raíz (vacío)
            self._tree_view.setRootIndex(QModelIndex())
            self.project_btn.setText(self.no_project_message)

        # Notificar cambio (opcional)
        self.projectChanged.emit(path if path else "")

    def update_theme(self, colors):
        """
        Aplica los colores del tema actual al sidebar y al árbol.
        colors es un diccionario con claves como 'bg', 'fg', 'select_bg', etc.
        """
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
    # Menú contextual (clic derecho)
    # ----------------------------------------------------------------------
    def show_context_menu(self, pos):
        """
        Muestra un menú contextual en español para el elemento bajo el cursor.
        """
        proxy_index = self._tree_view.indexAt(pos)
        if not proxy_index.isValid() and self.current_root is None:
            return  # Sin proyecto, no hay acciones

        menu = QMenu(self)

        # Acciones comunes (crear nuevo archivo/carpeta)
        new_file_action = QAction("Nuevo archivo", self)
        new_file_action.triggered.connect(lambda: self.new_item(self.get_target_dir(proxy_index), is_dir=False))
        menu.addAction(new_file_action)

        new_folder_action = QAction("Nueva carpeta", self)
        new_folder_action.triggered.connect(lambda: self.new_item(self.get_target_dir(proxy_index), is_dir=True))
        menu.addAction(new_folder_action)

        menu.addSeparator()

        # Si hay un elemento seleccionado, agregar acciones específicas
        if proxy_index.isValid():
            # Obtener la ruta real usando el modelo fuente
            source_index = self.proxy_model.mapToSource(proxy_index)
            path = self.source_model.filePath(source_index)
            is_dir = self.source_model.isDir(source_index)

            # Copiar / Cortar / Pegar
            copy_action = QAction("Copiar", self)
            copy_action.triggered.connect(lambda: self.copy_path(path))
            menu.addAction(copy_action)

            cut_action = QAction("Cortar", self)
            cut_action.triggered.connect(lambda: self.cut_path(path))
            menu.addAction(cut_action)

            # Pegar solo si hay algo en el portapapeles interno
            if self.clipboard_path is not None:
                paste_action = QAction("Pegar", self)
                paste_action.triggered.connect(lambda: self.paste_into(self.get_target_dir(proxy_index)))
                menu.addAction(paste_action)

            menu.addSeparator()

            # Renombrar / Eliminar
            rename_action = QAction("Renombrar", self)
            rename_action.triggered.connect(lambda: self._tree_view.edit(proxy_index))
            menu.addAction(rename_action)

            delete_action = QAction("Eliminar", self)
            delete_action.triggered.connect(lambda: self.delete_path(path))
            menu.addAction(delete_action)

            menu.addSeparator()

            # Abrir en terminal (opcional)
            if is_dir:
                open_terminal_action = QAction("Abrir en terminal", self)
                # Conectar a función del core (si existe)
                if hasattr(self.parent, 'term') and hasattr(self.parent.term, 'change_directory'):
                    open_terminal_action.triggered.connect(lambda: self.parent.term.change_directory(path))
                menu.addAction(open_terminal_action)

        menu.exec(self._tree_view.viewport().mapToGlobal(pos))

    def get_target_dir(self, proxy_index):
        """
        Devuelve el directorio destino para operaciones como nuevo archivo/carpeta.
        Si proxy_index es válido y es carpeta, usa esa ruta; si es archivo, usa su directorio padre;
        si no hay índice, usa la raíz del proyecto.
        """
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
        """
        Crea un nuevo archivo o carpeta en parent_path.
        Si parent_path es None o no existe, no hace nada.
        """
        if not parent_path or not os.path.isdir(parent_path):
            return

        if is_dir:
            # Carpeta: usar QFileSystemModel.mkdir
            # Generar nombre por defecto
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
            # Archivo: crear archivo vacío y luego editar
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
                # Buscar el índice en el modelo fuente y mapearlo al proxy
                source_index = self.source_model.index(file_path)
                if source_index.isValid():
                    proxy_index = self.proxy_model.mapFromSource(source_index)
                    self._tree_view.edit(proxy_index)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el archivo:\n{e}")

    def copy_path(self, path):
        """Almacena la ruta para copiar."""
        self.clipboard_path = path
        self.cut_mode = False

    def cut_path(self, path):
        """Almacena la ruta para cortar."""
        self.clipboard_path = path
        self.cut_mode = True

    def paste_into(self, target_dir):
        """
        Pega (copia o mueve) el elemento almacenado en el portapapeles interno
        al directorio target_dir.
        """
        if not self.clipboard_path or not target_dir or not os.path.exists(self.clipboard_path):
            return

        src = self.clipboard_path
        dst = os.path.join(target_dir, os.path.basename(src))

        # Evitar sobrescribir sin preguntar
        if os.path.exists(dst):
            reply = QMessageBox.question(
                self, "Confirmar",
                f"El archivo o carpeta '{os.path.basename(dst)}' ya existe.\n¿Sobrescribir?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            # Eliminar destino para poder copiar/mover
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
                # Mover
                shutil.move(src, dst)
                self.clipboard_path = None  # Limpiar portapapeles tras cortar
            else:
                # Copiar
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo pegar:\n{e}")

    def delete_path(self, path):
        """Elimina el archivo o carpeta (con confirmación)."""
        if not os.path.exists(path):
            return

        # Preguntar confirmación
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
    # Métodos para integración con el core (usados en create_new_file_global)
    # ----------------------------------------------------------------------
    def new_item_at_root(self, is_dir=False):
        """Crea un nuevo elemento en la raíz del proyecto."""
        if self.current_root:
            self.new_item(self.current_root, is_dir)

    # Propiedad tree_view para que el core pueda acceder directamente y conectar señales
    @property
    def tree_view(self):
        return self._tree_view