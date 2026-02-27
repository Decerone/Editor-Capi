import sys
import os
import platform
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
        self.is_running_script = False
        self.initialized = False  # Bandera para evitar múltiples inicializaciones
        
        # Temporizador para el prompt
        self.prompt_timer = QTimer(self)
        self.prompt_timer.setSingleShot(True)
        self.prompt_timer.setInterval(120)
        self.prompt_timer.timeout.connect(self.print_prompt_now)
        
        self.prompt_color = "#50fa7b"  # Verde Esmeralda neón
        
        # Configuración de UI
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
        
        # Iniciar proceso después de un pequeño delay para asegurar que todo esté listo
        QTimer.singleShot(100, self.start_process)

    def get_prompt_html(self):
        """Genera el prompt con color y la carpeta actual."""
        folder_text = f"/{self.current_folder}" if self.current_folder else ""
        return f'<span style="color:{self.prompt_color}; font-weight:bold;">{self.base_prompt}{folder_text} → </span>'

    def start_process(self):
        """Inicia el proceso del sistema (Bash o CMD)."""
        if self.initialized:
            return
        self.initialized = True
        
        if self.process:
            self.cleanup_process()
        
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_output_received)
        self.process.readyReadStandardError.connect(self.on_output_received)  # También capturar stderr
        self.process.finished.connect(self.on_process_finished)
        self.process.errorOccurred.connect(self.on_process_error)
        
        system = platform.system()
        try:
            if system == "Windows":
                shell = os.environ.get("COMSPEC", "cmd.exe")
                args = []
            else:
                shell = os.environ.get("SHELL", "/bin/bash")
                args = ["--login"]  # Modo login para mejor entorno
            
            self.process.setProgram(shell)
            if args:
                self.process.setArguments(args)
            
            self.process.setWorkingDirectory(os.getcwd())
            self.process.start()
            
            # Verificar que el proceso inició correctamente
            if not self.process.waitForStarted(1000):
                raise Exception("No se pudo iniciar el proceso")
            
            self.prompt_timer.start(200)
            
        except Exception as e:
            self.append_text_safe(f"❌ Error al iniciar terminal: {str(e)}\n")
            self.initialized = False

    def on_process_finished(self, exit_code, exit_status):
        """Maneja cuando el proceso termina."""
        self.append_text_safe(f"\n[Proceso terminado con código {exit_code}]\n")
        self.is_running_script = False
        self.process = None
        self.initialized = False
        # Intentar reiniciar después de un momento
        QTimer.singleShot(1000, self.start_process)

    def on_process_error(self, error):
        """Maneja errores del proceso."""
        self.append_text_safe(f"\n❌ Error en proceso: {error}\n")
        self.cleanup_process()

    def on_output_received(self):
        """Gestión de salida del sistema y detección de rutas."""
        if not self.process:
            return
        
        try:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            if not data:
                # Intentar leer error channel si no hay stdout
                data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
            
            if not data:
                return

            # Procesar salida
            if self.path_marker in data and not self.is_running_script:
                parts = data.split(self.path_marker)
                real_output = parts[0]
                
                # Extraer nueva carpeta
                try:
                    path_info = parts[1].strip().split('\n')[0].strip()
                    if path_info and os.path.exists(path_info):
                        self.current_folder = os.path.basename(path_info)
                except Exception:
                    pass
                
                if real_output.strip():
                    self.append_text_safe(real_output)
            else:
                # Salida normal
                self.append_text_safe(data)
            
            # Solo mostrar el prompt si el proceso no está bloqueado
            if not self.is_running_script:
                self.prompt_timer.start(150)
                
        except Exception as e:
            print(f"Error procesando salida: {e}")

    def print_prompt_now(self):
        """Dibuja el prompt visual y bloquea la posición."""
        if self.is_running_script or not self.process:
            return
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        txt = self.document().toPlainText()
        
        # Asegurar que el prompt empiece en línea nueva
        if len(txt) > 0 and not txt.endswith('\n'):
            cursor.insertText("\n")
        
        cursor.insertHtml(self.get_prompt_html())
        self.moveCursor(QTextCursor.End)
        self.prompt_safe_pos = self.textCursor().position()
        self.ensureCursorVisible()

    def append_text_safe(self, text):
        """Escribe texto del sistema de forma segura."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        # Actualizar frontera
        self.prompt_safe_pos = self.textCursor().position()

    def execute_command(self, cmd, is_from_run=False):
        """Ejecuta comandos con alias inteligentes y rastreo de ruta."""
        clean_cmd = cmd.strip()
        if not clean_cmd:
            self.prompt_timer.start(10)
            return
        
        # Verificar que el proceso existe y está corriendo
        if not self.process or self.process.state() != QProcess.Running:
            self.start_process()
            QTimer.singleShot(500, lambda: self.execute_command(cmd, is_from_run))
            return
        
        # Alias para Linux/Mac
        if platform.system() != "Windows":
            if clean_cmd.startswith("python "):
                clean_cmd = clean_cmd.replace("python ", "python3 ", 1)
            elif clean_cmd == "python":
                clean_cmd = "python3"
            elif clean_cmd == "pip":
                clean_cmd = "pip3"

        # Comandos internos de la UI
        if clean_cmd.lower() in ["cls", "clear"]:
            self.clear()
            self.prompt_timer.start(10)
            return
        
        if clean_cmd.lower() == "exit":
            self.append_text_safe("\n[Saliendo de la terminal...]\n")
            self.cleanup_process()
            return

        try:
            if is_from_run:
                self.is_running_script = True
                full_cmd = clean_cmd
            else:
                # Comandos manuales: Inyectar rastreador de ruta
                if platform.system() == "Windows":
                    full_cmd = f"{clean_cmd} & echo {self.path_marker}%CD%"
                else:
                    full_cmd = f"{clean_cmd}; echo {self.path_marker}$PWD"
            
            self.append_text_safe("\n")
            self.process.write((full_cmd + "\n").encode('utf-8'))
            
        except Exception as e:
            self.append_text_safe(f"\n❌ Error ejecutando comando: {e}\n")
            self.is_running_script = False

    def run_script(self, script_path):
        """Llamado desde el botón RUN del editor."""
        if not os.path.exists(script_path):
            self.append_text_safe(f"\n❌ El archivo no existe: {script_path}\n")
            return
        
        # Usar python3 en Linux/Mac, python en Windows
        if platform.system() == "Windows":
            py_exe = "python"
        else:
            py_exe = "python3"
        
        # Asegurar que la ruta está entre comillas si tiene espacios
        if ' ' in script_path:
            script_path = f'"{script_path}"'
        
        cmd = f'{py_exe} -u {script_path}'
        self.append_text_safe(f"\n🚀 Ejecutando: {cmd}\n")
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
            
            if cmd_text:
                if self.is_running_script:
                    # Si un script está pidiendo input(), enviamos crudo
                    if self.process and self.process.state() == QProcess.Running:
                        self.process.write((cmd_text + "\n").encode('utf-8'))
                else:
                    # Si es la terminal libre, procesamos comando
                    self.execute_command(cmd_text)
            else:
                # Comando vacío, solo mostrar prompt
                self.prompt_timer.start(10)
            return
        
        # CTRL+C: Matar proceso actual
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_C:
            self.append_text_safe("\n^C\n")
            if self.is_running_script:
                self.is_running_script = False
                if self.process and self.process.state() == QProcess.Running:
                    if platform.system() == "Windows":
                        self.process.write(b"\x03\n")  # Ctrl+C en Windows
                    else:
                        self.process.terminate()
                        QTimer.singleShot(1000, lambda: self.process.kill() if self.process else None)
            else:
                self.cleanup_process()
                QTimer.singleShot(100, self.start_process)
            return

        # Bloqueo de borrado (Backspace)
        if e.key() == Qt.Key_Backspace:
            if cursor.position() <= self.prompt_safe_pos:
                return
        
        # Bloqueo de escritura en zona protegida
        if cursor.position() < self.prompt_safe_pos:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        
        # Permitir Ctrl+V para pegar
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_V:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                self.insertPlainText(text)
            return
        
        super().keyPressEvent(e)

    def cleanup_process(self):
        """Cierre forzado y limpio."""
        if self.process:
            try:
                self.process.terminate()
                if not self.process.waitForFinished(1000):
                    self.process.kill()
                    self.process.waitForFinished(500)
                self.process.deleteLater()
            except Exception:
                pass
            self.process = None
        self.initialized = False
        self.is_running_script = False

    def stop_process(self):
        """Cerrar desde el menú."""
        self.cleanup_process()
        self.clear()
        self.prompt_safe_pos = 0

    def update_theme(self, colors):
        """Actualiza el tema de la terminal."""
        bg = colors.get('bg', '#1e1e1e')
        fg = colors.get('fg', '#cccccc')
        self.setStyleSheet(f"""
            QPlainTextEdit {{ 
                background-color: {bg}; 
                color: {fg}; 
                border: none; 
                padding: 5px;
                border-top: 1px solid {colors.get('splitter', '#3e3e42')};
            }}
        """)
        # Mantener el color del prompt independiente del tema
        if colors.get('name') == 'Light':
            self.prompt_color = "#0066cc"  # Azul más visible en fondo claro
        else:
            self.prompt_color = "#50fa7b"  # Verde neón para temas oscuros