from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu

class MenuBuilder:
    def __init__(self, main_window):
        self.main = main_window
        # Grupos para acciones exclusivas
        self.theme_group = QActionGroup(self.main)
        self.theme_group.setExclusive(True)
        
        self.font_group = QActionGroup(self.main)
        self.font_group.setExclusive(True)
        
        self.tab_group = QActionGroup(self.main)
        self.tab_group.setExclusive(True)

    def setup_menus(self):
        mb = self.main.menuBar()
        mb.clear()

        # --- 1. ARCHIVO ---
        file_menu = mb.addMenu("&Archivo")
        self.add_act(file_menu, "📄 Nueva Pestaña", "Ctrl+N", self.new_empty_tab)
        self.add_act(file_menu, "📄 Nuevo Archivo", None, self.main.create_new_file_global)
        self.add_act(file_menu, "📁 Nueva Carpeta...", "Ctrl+Shift+N", self.main.create_new_folder_global)
        file_menu.addSeparator()
        self.add_act(file_menu, "📂 Abrir Proyecto...", None, self.main.select_folder)
        self.add_act(file_menu, "📄 Abrir Archivo...", "Ctrl+O", lambda: self.main.open_file())
        file_menu.addSeparator()
        self.add_act(file_menu, "💾 Guardar", "Ctrl+S", self.main.save_current_file)
        self.add_act(file_menu, "💾 Guardar como...", "Ctrl+Shift+S", self.main.save_file_as)
        file_menu.addSeparator()
        self.add_act(file_menu, "❌ Cerrar Pestaña", "Ctrl+W", self.main.close_current_tab)
        self.add_act(file_menu, "🚪 Salir", "Alt+F4", self.main.close)

        # --- 2. EDITAR ---
        edit_menu = mb.addMenu("&Editar")
        self.add_act(edit_menu, "↩️ Deshacer", "Ctrl+Z", self.undo)
        self.add_act(edit_menu, "↪️ Rehacer", "Ctrl+Y", self.redo)
        edit_menu.addSeparator()
        self.add_act(edit_menu, "✂️ Cortar", "Ctrl+X", self.cut)
        self.add_act(edit_menu, "📋 Copiar", "Ctrl+C", self.copy)
        self.add_act(edit_menu, "📥 Pegar", "Ctrl+V", self.paste)
        self.add_act(edit_menu, "🔍 Seleccionar Todo", "Ctrl+A", self.select_all)
        edit_menu.addSeparator()
        self.add_act(edit_menu, "🔍 Buscar", "Ctrl+F", self.main.toggle_local_search)
        self.add_act(edit_menu, "🌎 Búsqueda Global", "Ctrl+Shift+F", self.main.show_global_search)
        self.add_act(edit_menu, "📍 Ir a Línea...", "Ctrl+G", self.main.go_to_line)

        # --- 3. VER ---
        view_menu = mb.addMenu("&Ver")
        
        mini_act = QAction("🗺️ Minimapa", self.main, checkable=True)
        mini_act.setChecked(self.main.minimap_enabled)
        mini_act.triggered.connect(self.main.toggle_minimap_global)
        view_menu.addAction(mini_act)
        
        view_menu.addSeparator()
        self.add_act(view_menu, "🔍 Aumentar Zoom", "Ctrl++", self.main.zoom_in)
        self.add_act(view_menu, "🔍 Disminuir Zoom", "Ctrl+-", self.main.zoom_out)

        # --- 4. CONFIGURACIÓN ---
        conf_menu = mb.addMenu("&Configuración")
        
        auto_act = QAction("🔄 Auto-Guardado", self.main, checkable=True)
        auto_act.setChecked(self.main.autosave_enabled) 
        auto_act.triggered.connect(self.main.toggle_autosave)
        conf_menu.addAction(auto_act)
        conf_menu.addSeparator()

        # Fuente - Acciones exclusivas
        font_menu = conf_menu.addMenu("🔡 Fuente Base")
        for size in [10, 12, 14, 16, 18, 20, 24]:
            act = QAction(f"{size} pt", self.main, checkable=True)
            act.setActionGroup(self.font_group)  # Grupo exclusivo
            if size == self.main.font_size: 
                act.setChecked(True)
            act.triggered.connect(lambda checked, s=size: self.main.change_font_size(s))
            font_menu.addAction(act)

        # Tabulación - Acciones exclusivas
        tab_menu = conf_menu.addMenu("⭾ Tabulación")
        for width in [2, 4, 8]:
            act = QAction(f"{width} Espacios", self.main, checkable=True)
            act.setActionGroup(self.tab_group)  # Grupo exclusivo
            if width == self.main.tab_width: 
                act.setChecked(True)
            act.triggered.connect(lambda checked, w=width: self.main.change_tab_width(w))
            tab_menu.addAction(act)

        # --- 5. EJECUTAR ---
        run_menu = mb.addMenu("&Ejecutar")
        self.add_act(run_menu, "▶️ Ejecutar Script", "F5", self.main.run_current_file)
        self.add_act(run_menu, "💻 Mostrar Terminal", "Ctrl+J", self.main.toggle_console)

        # --- 6. TEMA - Acciones exclusivas ---
        theme_menu = mb.addMenu("&Tema")
        for theme_name in self.main.all_themes:
            act = QAction(theme_name, self.main, checkable=True)
            act.setActionGroup(self.theme_group)  # Grupo exclusivo
            if theme_name == self.main.current_theme:
                act.setChecked(True)
            act.triggered.connect(lambda checked, t=theme_name: self.main.apply_theme(t))
            theme_menu.addAction(act)

        # --- 7. AYUDA ---
        help_menu = mb.addMenu("&Ayuda")
        self.add_act(help_menu, "⌨️ Lista de Atajos", "Ctrl+Shift+B", self.main.show_shortcuts_dialog)
        self.add_act(help_menu, "ℹ️ Acerca de", "F1", self.main.show_about)

    # --- Métodos helper ---
    def get_current_editor(self):
        w = self.main.tabs.currentWidget()
        if w and hasattr(w, 'editor') and not getattr(w, 'is_welcome', False):
            return w.editor
        return None

    def undo(self):
        editor = self.get_current_editor()
        if editor: editor.undo()

    def redo(self):
        editor = self.get_current_editor()
        if editor: editor.redo()

    def cut(self):
        editor = self.get_current_editor()
        if editor: editor.cut()

    def copy(self):
        editor = self.get_current_editor()
        if editor: editor.copy()

    def paste(self):
        editor = self.get_current_editor()
        if editor: editor.paste()

    def select_all(self):
        editor = self.get_current_editor()
        if editor: editor.selectAll()

    def new_empty_tab(self):
        self.main.add_tab(None, "")

    def add_act(self, menu, text, shortcut, func):
        act = QAction(text, self.main)
        if shortcut:
            act.setShortcut(shortcut)
        act.triggered.connect(func)
        menu.addAction(act)