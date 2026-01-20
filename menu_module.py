from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

class MenuBuilder:
    def __init__(self, main_window):
        self.p = main_window 

    def setup_menus(self):
        mb = self.p.menuBar()
        mb.clear()

        # --- 1. ARCHIVO ---
        file_menu = mb.addMenu("&Archivo")
        # Ctrl+N crea una pestaña nueva vacía (memoria)
        self.add_act(file_menu, "📄 Nuevo Pestaña", "Ctrl+N", lambda: self.p.add_tab())
        # Crea un archivo físico en el árbol
        self.add_act(file_menu, "📄 Nuevo Archivo", None, self.p.create_new_file_global)
        self.add_act(file_menu, "📁 Nueva Carpeta...", "Ctrl+Shift+N", self.p.create_new_folder_global)
        file_menu.addSeparator()
        self.add_act(file_menu, "📂 Abrir Proyecto...", None, self.p.select_folder)
        self.add_act(file_menu, "📄 Abrir Archivo...", "Ctrl+O", lambda: self.p.open_file())
        file_menu.addSeparator()
        self.add_act(file_menu, "💾 Guardar", "Ctrl+S", self.p.save_current_file)
        self.add_act(file_menu, "💾 Guardar como...", "Ctrl+Shift+S", self.p.save_file_as)
        file_menu.addSeparator()
        self.add_act(file_menu, "❌ Cerrar Pestaña", "Ctrl+W", self.p.close_current_tab)
        self.add_act(file_menu, "🚪 Salir", "Alt+F4", self.p.close)

        # --- 2. EDITAR (Usa el helper self.ed() para manipular el editor activo) ---
        edit_menu = mb.addMenu("&Editar")
        self.add_act(edit_menu, "↩️ Deshacer", "Ctrl+Z", lambda: self.ed().undo() if self.ed() else None)
        self.add_act(edit_menu, "↪️ Rehacer", "Ctrl+Y", lambda: self.ed().redo() if self.ed() else None)
        edit_menu.addSeparator()
        self.add_act(edit_menu, "✂️ Cortar", "Ctrl+X", lambda: self.ed().cut() if self.ed() else None)
        self.add_act(edit_menu, "📋 Copiar", "Ctrl+C", lambda: self.ed().copy() if self.ed() else None)
        self.add_act(edit_menu, "📥 Pegar", "Ctrl+V", lambda: self.ed().paste() if self.ed() else None)
        self.add_act(edit_menu, "🔍 Seleccionar Todo", "Ctrl+A", lambda: self.ed().selectAll() if self.ed() else None)
        edit_menu.addSeparator()
        self.add_act(edit_menu, "🔍 Buscar", "Ctrl+F", self.p.toggle_local_search)
        self.add_act(edit_menu, "🌎 Búsqueda Global", "Ctrl+Shift+F", self.p.show_global_search)
        self.add_act(edit_menu, "📍 Ir a Línea...", "Ctrl+G", self.p.go_to_line)

        # --- 3. VER ---
        view_menu = mb.addMenu("&Ver")
        
        # Minimapa Checkable
        mini_act = QAction("🗺️ Minimapa", self.p, checkable=True)
        mini_act.setChecked(self.p.minimap_enabled)
        mini_act.triggered.connect(self.p.toggle_minimap_global)
        view_menu.addAction(mini_act)
        
        view_menu.addSeparator()
        self.add_act(view_menu, "🔍 Aumentar Zoom", "Ctrl++", self.p.zoom_in)
        self.add_act(view_menu, "🔍 Disminuir Zoom", "Ctrl+-", self.p.zoom_out)

        # --- 4. CONFIGURACIÓN ---
        conf_menu = mb.addMenu("&Configuración")
        
        auto_act = QAction("🔄 Auto-Guardado", self.p)
        auto_act.setCheckable(True)
        auto_act.setChecked(self.p.autosave_enabled) 
        auto_act.triggered.connect(self.p.toggle_autosave)
        conf_menu.addAction(auto_act)
        conf_menu.addSeparator()

        font_menu = conf_menu.addMenu("🔡 Fuente Base")
        for size in [10, 12, 14, 16, 18, 20, 24]:
            act = QAction(f"{size} pt", self.p, checkable=True)
            if size == self.p.font_size: act.setChecked(True)
            # Usamos lambda con default argument para capturar el valor de size
            act.triggered.connect(lambda c, s=size: self.p.change_font_size(s))
            font_menu.addAction(act)

        tab_menu = conf_menu.addMenu("⭾ Tabulación")
        for width in [2, 4, 8]:
            act = QAction(f"{width} Espacios", self.p, checkable=True)
            if width == self.p.tab_width: act.setChecked(True)
            act.triggered.connect(lambda c, w=width: self.p.change_tab_width(w))
            tab_menu.addAction(act)

        # --- 5. EJECUTAR ---
        run_menu = mb.addMenu("&Ejecutar")
        self.add_act(run_menu, "▶️ Ejecutar Script", "F5", self.p.run_current_file)
        self.add_act(run_menu, "💻 Mostrar Terminal", "Ctrl+J", self.p.toggle_console)

        # --- 6. TEMA ---
        theme_menu = mb.addMenu("&Tema")
        for t_name in self.p.all_themes:
            self.add_act(theme_menu, t_name, None, lambda c=False, n=t_name: self.p.apply_theme(n))

        # --- 7. AYUDA ---
        help_menu = mb.addMenu("&Ayuda")
        # Aquí conectamos con tu diálogo de atajos nuevo
        self.add_act(help_menu, "⌨️ Lista de Atajos", "Ctrl+Shift+B", self.p.show_shortcuts_dialog)
        self.add_act(help_menu, "ℹ️ Acerca de", "F1", self.p.show_about)

    def add_act(self, menu, text, shortcut, func):
        """Helper para añadir acciones de forma compacta"""
        act = QAction(text, self.p)
        if shortcut: act.setShortcut(shortcut)
        act.triggered.connect(func)
        menu.addAction(act)

    def ed(self):
        """Helper seguro para obtener el editor de código actual"""
        w = self.p.tabs.currentWidget()
        # Verificar que existe y que no es la pantalla de bienvenida
        if w and hasattr(w, 'editor') and not getattr(w, 'is_welcome', False):
            return w.editor
        return None