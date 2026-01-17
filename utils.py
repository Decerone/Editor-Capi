import sys
import os

# --- FUNCIÓN CRÍTICA PARA COMPILACIÓN ---
def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- TEMAS DE COLOR ---
THEMES = {
    "Dark": {
        "bg": "#1e1e1e", "fg": "#d4d4d4", 
        "select_bg": "#264f78", "line_bg": "#1e1e1e", "line_fg": "#858585",
        "tags": {
            "keyword": "#569cd6", "class": "#4ec9b0", "function": "#dcdcaa",
            "string": "#ce9178", "comment": "#6a9955", "number": "#b5cea8",
            "operator": "#d4d4d4", "variable": "#9cdcfe"
        }
    },
    "Light": {
        "bg": "#fffffffd", "fg": "#000000",
        "select_bg": "#add6ff", "line_bg": "#f3f3f3", "line_fg": "#2b91af",
        "tags": {
            "keyword": "#0000ff", "class": "#2b91af", "function": "#795e26",
            "string": "#a31515", "comment": "#008000", "number": "#098658",
            "operator": "#000000", "variable": "#001080"
        }
    },
    "Monokai": {
        "bg": "#272822", "fg": "#f8f8f2",
        "select_bg": "#49483e", "line_bg": "#272822", "line_fg": "#75715e",
        "tags": {
            "keyword": "#f92672", "class": "#a6e22e", "function": "#a6e22e",
            "string": "#e6db74", "comment": "#75715e", "number": "#ae81ff",
            "operator": "#f8f8f2", "variable": "#f8f8f2"
        }
    },
    "Dracula": {
        "bg": "#282a36", "fg": "#f8f8f2",
        "select_bg": "#44475a", "line_bg": "#282a36", "line_fg": "#6272a4",
        "tags": {
            "keyword": "#ff79c6", "class": "#8be9fd", "function": "#50fa7b",
            "string": "#f1fa8c", "comment": "#6272a4", "number": "#bd93f9",
            "operator": "#ff79c6", "variable": "#f8f8f2"
        }
    }
}