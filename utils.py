# -*- coding: utf-8 -*-
"""
utils.py

Configuraciones, temas y utilidades para CapiEditor Pro.
"""

import sys
import os


# ==============================================================================
#  FUNCIONES DE UTILIDAD
# ==============================================================================

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso (útil para PyInstaller).
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_theme_names():
    """Devuelve la lista de nombres de temas disponibles."""
    return list(THEMES.keys())


def get_default_theme():
    """Devuelve el tema por defecto."""
    return "Dark"


# ==============================================================================
#  DEFINICIÓN DE TEMAS (EXPANDIDOS)
# ==============================================================================

THEMES = {
    # --- TEMA OSCURO (VS CODE STYLE) ---
    "Dark": {
        "name": "Dark",
        "bg": "#1e1e1e",
        "window_bg": "#252526",
        "fg": "#d4d4d4",
        "select_bg": "#264f78",
        "line_bg": "#2d2d30",
        "line_fg": "#858585",
        "splitter": "#3e3e42",
        "tags": {
            "keyword": "#569cd6",      # Azul (if, class, function)
            "string": "#ce9178",       # Naranja suave
            "comment": "#6a9955",      # Verde
            "function": "#dcdcaa",     # Amarillo pálido (nombre func)
            "class": "#4ec9b0",        # Verde agua
            "number": "#b5cea8",       # Verde claro
            "builtin": "#4fc1ff",      # Azul cian (echo, print, len)
            "variable": "#9cdcfe",     # Azul claro ($var)
            "operator": "#d4d4d4",     # Blanco ( =, +, -> )
            "tag": "#569cd6",          # Etiquetas HTML (<div, <?php)
            "attribute": "#9cdcfe",    # Atributos HTML (href, class)
            "decorator": "#dcdcaa",    # Decoradores Python (@)
            "constant": "#4fc1ff"      # Constantes
        }
    },

    # --- TEMA CLARO (CLEAN STYLE) ---
    "Light": {
        "name": "Light",
        "bg": "#f4f4f3",
        "window_bg": "#e9e9e9",
        "fg": "#333333",
        "select_bg": "#add6ff",
        "line_bg": "#e1effe",
        "line_fg": "#2b91af",
        "splitter": "#e0e0e0",
        "tags": {
            "keyword": "#0000ff",
            "string": "#a31515",
            "comment": "#008000",
            "function": "#795e26",
            "class": "#2b91af",
            "number": "#098658",
            "builtin": "#001080",
            "variable": "#001080",
            "operator": "#333333",
            "tag": "#800000",
            "attribute": "#ff0000",
            "decorator": "#795e26",
            "constant": "#0070c1"
        }
    },

    # --- TEMA MONOKAI (VIBRANT) ---
    "Monokai": {
        "name": "Monokai",
        "bg": "#272822",
        "window_bg": "#1e1f1c",
        "fg": "#f8f8f2",
        "select_bg": "#49483e",
        "line_bg": "#3e3d32",
        "line_fg": "#90908a",
        "splitter": "#171814",
        "tags": {
            "keyword": "#f92672",
            "string": "#e6db74",
            "comment": "#75715e",
            "function": "#a6e22e",
            "class": "#66d9ef",
            "number": "#ae81ff",
            "builtin": "#66d9ef",
            "variable": "#f8f8f2",
            "operator": "#f92672",
            "tag": "#f92672",
            "attribute": "#a6e22e",
            "decorator": "#a6e22e",
            "constant": "#ae81ff"
        }
    },

    # --- TEMA DRACULA (PASTEL DARK) ---
    "Dracula": {
        "name": "Dracula",
        "bg": "#282a36",
        "window_bg": "#21222c",
        "fg": "#f8f8f2",
        "select_bg": "#44475a",
        "line_bg": "#44475a",
        "line_fg": "#6272a4",
        "splitter": "#191a21",
        "tags": {
            "keyword": "#ff79c6",
            "string": "#f1fa8c",
            "comment": "#6272a4",
            "function": "#50fa7b",
            "class": "#8be9fd",
            "number": "#bd93f9",
            "builtin": "#8be9fd",
            "variable": "#f8f8f2",
            "operator": "#ff79c6",
            "tag": "#ff79c6",
            "attribute": "#50fa7b",
            "decorator": "#50fa7b",
            "constant": "#bd93f9"
        }
    }
}


# ==============================================================================
#  NOTA: La línea problemática ha sido eliminada.
#  Si necesitas probar el hover con color rojo, hazlo desde el código principal
#  o desde el método update_theme de FileTreeView.
# ==============================================================================