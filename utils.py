import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# -------------------------------------------
# HE AÑADIDO 'window_bg' Y 'splitter' A CADA TEMA
THEMES = {
    "Dark": {
        "bg": "#1e1e1e",           # Fondo del Editor (Gris Oscuro)
        "window_bg": "#181818",    # NUEVO: Fondo de Ventana (Casi Negro)
        "splitter": "#2b2b2b",     # NUEVO: Separadores (Gris medio)
        "fg": "#d4d4d4", 
        "select_bg": "#264f78", 
        "line_bg": "#1e1e1e", 
        "line_fg": "#858585",
        "tags": { "keyword": "#569cd6", "string": "#ce9178", "comment": "#6a9955", "function": "#dcdcaa", "class": "#4ec9b0", "number": "#b5cea8" }
    },
    "Light": {
        "bg": "#f3f3f3",           # Fondo Editor (Blanco)
        "window_bg": "#eeeeeeff",    # NUEVO: Fondo Ventana (Gris muy claro)
        "splitter": "#e5e5e5",     # NUEVO: Separador
        "fg": "#000000", 
        "select_bg": "#add6ff", 
        "line_bg": "#e7e7e7", 
        "line_fg": "#2b91af",
        "tags": { "keyword": "#0000ff", "string": "#a31515", "comment": "#008000", "function": "#795e26", "class": "#2b91af", "number": "#098658" }
    },
    "Monokai": {
        "bg": "#272822",           # Editor
        "window_bg": "#1e1f1c",    # NUEVO: Ventana más oscura
        "splitter": "#3e3d32",     # NUEVO: Separador
        "fg": "#f8f8f2", 
        "select_bg": "#49483e", 
        "line_bg": "#272822", 
        "line_fg": "#90908a",
        "tags": { "keyword": "#f92672", "string": "#e6db74", "comment": "#75715e", "function": "#a6e22e", "class": "#66d9ef", "number": "#ae81ff" }
    },
    "Dracula": {
        "bg": "#282a36",           # Editor
        "window_bg": "#21222c",    # NUEVO: Ventana más oscura
        "splitter": "#44475a",     # NUEVO: Separador
        "fg": "#f8f8f2", 
        "select_bg": "#44475a", 
        "line_bg": "#282a36", 
        "line_fg": "#6272a4",
        "tags": { "keyword": "#ff79c6", "string": "#f1fa8c", "comment": "#6272a4", "function": "#50fa7b", "class": "#8be9fd", "number": "#bd93f9" }
    }
}