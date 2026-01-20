import sys, os, platform
from PySide6.QtCore import Qt, QProcess, QTimer
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

class EditorTerminal(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.base_prompt = "capi"
        self.current_folder = os.path.basename(os.getcwd())
        self.prompt_safe_pos = 0 
        self.path_marker = "__CAPI_PATH__"
        self.is_running_script = False # Control de flujo para evitar ruido
        
        # Temporizador inteligente para el prompt
        self.prompt_timer = QTimer(self)
        self.prompt_timer.setSingleShot(True)
        self.prompt_timer.interval = 120 # Un poco más lento para estabilidad visual
        self.prompt_timer.timeout.connect(self.print_prompt_now)
        
        self.prompt_color = "#50fa7b" # Verde Esmeralda neón
        
        # --- CONFIGURACIÓN DE UI ---
        self.setFont(QFont("Consolas", 10))
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setStyleSheet("""
            QPlainTextEdit { 
                background-color: #1e1e1e; 
                color: #cccccc; 
                border: none; 
                padding: 5px;
            }
        """)
        
        self.start_process()

    def get_prompt_html(self):
        """Genera el prompt con color y la carpeta actual."""
        folder_text = f".{self.current_folder}" if self.current_folder else ""
        return f'<span style="color:{self.prompt_color}; font-weight:bold;">{self.base_prompt}{folder_text}-> </span>'

    def start_process(self):
        """Inicia el proceso del sistema (Bash o CMD)."""
        if self.process:
            self.process.kill()
            self.process.waitForFinished(100)
        
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_output_received)
        # Sincronización: Detectar cuando termina una tarea pesada
        self.process.finished.connect(self._on_finished)
        
        system = platform.system()
        try:
            shell = os.environ.get("COMSPEC", "cmd.exe") if system == "Windows" else os.environ.get("SHELL", "/bin/bash")
            self.process.setProgram(shell)
            self.process.setWorkingDirectory(os.getcwd())
            self.process.start()
            self.prompt_timer.start(200) 
        except Exception as e:
            self.append_text_safe(f"Error de sistema: {e}\n")

    def _on_finished(self):
        """Reiniciar estado al terminar un script."""
        self.is_running_script = False
        self.prompt_timer.start(100)

    def on_output_received(self):
        """Gestión de salida del sistema y detección de rutas."""
        if not self.process: return
        try:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            if not data: return

            # Si detectamos nuestra marca de ruta y no estamos en medio de un input() de Python
            if self.path_marker in data and not self.is_running_script:
                parts = data.split(self.path_marker)
                real_output = parts[0]
                # Extraer nueva carpeta
                try:
                    path_info = parts[1].strip().split('\n')[0].strip()
                    if path_info:
                        self.current_folder = os.path.basename(path_info)
                except: pass
                
                if real_output.strip():
                     self.append_text_safe(real_output)
            else:
                # Salida normal
                self.append_text_safe(data)
            
            # Solo mostrar el prompt si el proceso no está bloqueado por un script
            if not self.is_running_script:
                self.prompt_timer.start(150) 
        except: pass

    def print_prompt_now(self):
        """Dibuja el prompt visual y bloquea la posición."""
        if self.is_running_script: return 
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        txt = self.document().toPlainText()
        
        # Asegurar que el prompt empiece en línea nueva
        if len(txt) > 0 and not txt.endswith('\n'):
            cursor.insertText("\n")
        
        cursor.insertHtml(self.get_prompt_html())
        self.moveCursor(QTextCursor.End)
        self.prompt_safe_pos = self.textCursor().position()

    def append_text_safe(self, text):
        """Escribe texto del sistema de forma segura."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        # Actualizar frontera
        self.prompt_safe_pos = self.textCursor().position()

    def execute_command(self, cmd, is_from_run=False):
        """Ejecuta comandos con Alias inteligentes y rastreo de ruta."""
        clean_cmd = cmd.strip()
        if not clean_cmd:
            self.prompt_timer.start(10)
            return
            
        # Alias: Corrección de Python en Linux/Mac
        if platform.system() != "Windows":
            if clean_cmd.startswith("python "):
                clean_cmd = clean_cmd.replace("python ", "python3 ", 1)
            elif clean_cmd == "python":
                clean_cmd = "python3"

        # Comandos internos de la UI
        if clean_cmd.lower() in ["cls", "clear"]:
            self.clear()
            self.prompt_timer.start(10)
            return

        if self.process and self.process.state() == QProcess.Running:
            if is_from_run:
                self.is_running_script = True # Evitar interferencia de prompt
                full_cmd = clean_cmd
            else:
                # Comandos manuales: Inyectar rastreador de ruta
                sep = "&" if platform.system() == "Windows" else ";"
                var = "%CD%" if platform.system() == "Windows" else "$PWD"
                full_cmd = f"{clean_cmd} {sep} echo {self.path_marker}{var}"
            
            self.append_text_safe("\n")
            self.process.write((full_cmd + "\n").encode('utf-8'))
        else:
            self.start_process()

    def run_script(self, script_path):
        """Llamado desde el botón RUN del editor."""
        py_exe = "python3" if platform.system() != "Windows" else "python"
        cmd = f'{py_exe} -u "{script_path}"'
        self.append_text_safe(cmd) # Mostrar el comando que se lanza
        self.execute_command(cmd, is_from_run=True)

    def keyPressEvent(self, e):
        """Control total del teclado."""
        cursor = self.textCursor()
        
        # ENTER: Procesar comando
        if e.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor.movePosition(QTextCursor.End)
            cursor.setPosition(self.prompt_safe_pos, QTextCursor.KeepAnchor)
            cmd_text = cursor.selectedText()
            cursor.clearSelection()
            self.setTextCursor(cursor)
            
            if self.is_running_script:
                # Si un script está pidiendo input(), enviamos crudo
                self.process.write((cmd_text + "\n").encode('utf-8'))
            else:
                # Si es la terminal libre, procesamos comando
                self.execute_command(cmd_text)
            return
        
        # CTRL+C: Matar proceso actual
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_C:
            self.cleanup_process()
            self.insertPlainText("^C\n")
            self.start_process()
            return

        # Bloqueo de borrado (Backspace)
        if e.key() == Qt.Key_Backspace:
            if cursor.position() <= self.prompt_safe_pos: return 
        
        # Bloqueo de escritura en zona protegida
        if cursor.position() < self.prompt_safe_pos:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            
        super().keyPressEvent(e)

    def cleanup_process(self):
        """Cierre forzado y limpio."""
        if self.process:
            try:
                self.process.kill()
                self.process.waitForFinished(100)
                self.process.deleteLater()
            except: pass
            self.process = None

    def stop_process(self):
        """Cerrar desde el menú."""
        self.cleanup_process()
        self.clear()

    def update_theme(self, colors):
        self.setStyleSheet(f"""
            QPlainTextEdit {{ 
                background-color: {colors['bg']}; 
                color: {colors['fg']}; 
                border: none; 
                padding: 5px;
            }}
        """)