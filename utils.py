import sys, os

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso (útil para PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==========================================
# DEFINICIÓN DE TEMAS
# ==========================================
THEMES = {
    # --- TEMA OSCURO (VS CODE STYLE) ---
    "Dark": {
        "bg": "#1e1e1e",          # Fondo del Editor
        "window_bg": "#252526",   # Fondo de la Ventana
        "fg": "#d4d4d4",          # Texto Principal
        "select_bg": "#264f78",   # Selección
        "line_bg": "#2d2d30",     # Línea actual
        "line_fg": "#858585",     # Números de línea
        "splitter": "#3e3e42",    # Bordes
        "tags": {
            "keyword": "#569cd6", # Azul
            "string": "#ce9178",  # Naranja suave
            "comment": "#6a9955", # Verde
            "function": "#dcdcaa",# Amarillo pálido
            "class": "#4ec9b0",   # Verde agua
            "number": "#b5cea8"   # Verde claro
        }
    },

    # --- TEMA CLARO (CLEAN STYLE) ---
    "Light": {
        "bg": "#f4f4f3",          # Fondo del Editor (Blanco puro)
        "window_bg": "#f5f5f5",   # Fondo de la Ventana/Sidebar (Gris muy claro)
        "fg": "#333333",          # Texto Principal (Gris oscuro/Negro)
        "select_bg": "#add6ff",   # Color de selección (Azul suave)
        "line_bg": "#e1effe",     # Fondo de la línea actual (Azul muy tenue)
        "line_fg": "#2b91af",     # Números de línea (Azul acero)
        "splitter": "#e0e0e0",    # Bordes
        "tags": {                 # Colores de sintaxis (Contrastados para fondo blanco)
            "keyword": "#0000ff", # Azul
            "string": "#a31515",  # Rojo oscuro
            "comment": "#008000", # Verde
            "function": "#795e26",# Dorado oscuro
            "class": "#2b91af",   # Cian oscuro
            "number": "#098658"   # Verde esmeralda
        }
    },

    # --- TEMA MONOKAI (VIBRANT) ---
    "Monokai": {
        "bg": "#272822",          # Fondo Clásico Monokai
        "window_bg": "#1e1f1c",   # Un poco más oscuro para la UI
        "fg": "#f8f8f2",          # Blanco hueso
        "select_bg": "#49483e",   # Gris selección
        "line_bg": "#3e3d32",     # Highlight línea
        "line_fg": "#90908a",
        "splitter": "#171814",
        "tags": {
            "keyword": "#f92672", # Rosa Fuerte
            "string": "#e6db74",  # Amarillo
            "comment": "#75715e", # Gris verdoso
            "function": "#a6e22e",# Verde Neón
            "class": "#66d9ef",   # Cian
            "number": "#ae81ff"   # Violeta
        }
    },

    # --- TEMA DRACULA (PASTEL DARK) ---
    "Dracula": {
        "bg": "#282a36",          # Fondo Dracula
        "window_bg": "#21222c",   # Fondo UI
        "fg": "#f8f8f2",          # Texto
        "select_bg": "#44475a",   # Selección púrpura grisáceo
        "line_bg": "#44475a",     # Línea actual
        "line_fg": "#6272a4",     # Comentarios/Num línea
        "splitter": "#191a21",
        "tags": {
            "keyword": "#ff79c6", # Rosa Pastel
            "string": "#f1fa8c",  # Amarillo Pastel
            "comment": "#6272a4", # Azul Grisáceo
            "function": "#50fa7b",# Verde Pastel
            "class": "#8be9fd",   # Cian Pastel
            "number": "#bd93f9"   # Púrpura Pastel
        }
    }
}