import importlib
import os
import sys

def comprobar_modulo(nombre_modulo, clases_esperadas):
    print(f"🔍 Verificando '{nombre_modulo}.py'...")
    try:
        # Intentar importar el módulo
        modulo = importlib.import_module(nombre_modulo)
        print(f"  ✅ Archivo encontrado e importado.")
        
        for clase in clases_esperadas:
            if hasattr(modulo, clase):
                print(f"  ✅ Clase '{clase}' detectada correctamente.")
            else:
                print(f"  ❌ ERROR: No se encuentra la clase '{clase}' en {nombre_modulo}.py")
                return False
        return True
    except ImportError as e:
        print(f"  ❌ ERROR CRÍTICO: No se pudo importar el módulo. Detalle: {e}")
        return False
    except Exception as e:
        print(f"  ❌ ERROR INESPERADO: {e}")
        return False

def verificar_sistema():
    print("="*50)
    print("   SISTEMA DE VERIFICACIÓN - EDITOR CAPI")
    print("="*50)
    
    # Mapa de archivos y qué deben contener para que editor_app.py no falle
    mapa_verificacion = {
        "utils": ["THEMES", "resource_path"],
        "sidebar_module": ["FileSidebar", "EmojiFileSystemModel"],
        "terminal": ["EditorTerminal"],
        "autocomplete": ["AutoCompleter"],
        "minimap": ["CodeMinimap"],
        "search_module": ["SearchWidget", "GlobalSearchDialog"],
        "menu_module": ["MenuBuilder"]
    }
    
    errores = 0
    
    for mod, clases in mapa_verificacion.items():
        if not comprobar_modulo(mod, clases):
            errores += 1
        print("-" * 30)
    
    if errores == 0:
        print("\n✨ ¡TODO PERFECTO! Todos los componentes están sincronizados.")
        print("🚀 Ya puedes ejecutar: python3 editor_app.py")
    else:
        print(f"\n⚠️ SE ENCONTRARON {errores} MÓDULO(S) CON PROBLEMAS.")
        print("Revisa los nombres de las clases o si los archivos están en la carpeta correcta.")

if __name__ == "__main__":
    verificar_sistema()
    
    

     