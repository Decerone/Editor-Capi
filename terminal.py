import sys
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFont, QColor, QTextCursor

class EditorTerminal(QWidget):
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent)
        self.setMinimumHeight(120) # Altura mínima para evitar bugs visuales
        self.process = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # BARRA DE CONTROL
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 0)
        self.lbl_status = QLabel("Terminal lista")
        self.lbl_status.setStyleSheet("color: #888; font-weight: bold;")
        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.setStyleSheet("background-color: #a31515; color: white; border: none; padding: 3px;")
        self.btn_stop.clicked.connect(self.stop_process)
        self.btn_stop.setEnabled(False)
        control_layout.addWidget(self.lbl_status)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_stop)
        layout.addLayout(control_layout)

        # ÁREA DE SALIDA
        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 10))
        self.output_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: none;")
        layout.addWidget(self.output_area)

        # ÁREA DE INPUT
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(5, 5, 5, 5)
        lbl_prompt = QLabel(">>>")
        lbl_prompt.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Entrada stdin...")
        self.input_line.setStyleSheet("background-color: #252526; color: white; border: 1px solid #3e3e42; padding: 4px;")
        self.input_line.returnPressed.connect(self.send_input)
        input_layout.addWidget(lbl_prompt)
        input_layout.addWidget(self.input_line)
        layout.addLayout(input_layout)

        if theme_colors: self.update_theme(theme_colors)

    def run_script(self, file_path):
        if not file_path: return
        self.stop_process()
        self.output_area.clear()
        self.lbl_status.setText(f"Ejecutando: {os.path.basename(file_path)}...")
        self.btn_stop.setEnabled(True)
        self.input_line.setFocus()
        
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        ext = os.path.splitext(file_path)[1].lower()
        program = ""
        args = []

        if ext == '.py' or ext == '.pyw':
            program = "python" if sys.platform == "win32" else "python3"
            args = ["-u", file_path] # -u for Unbuffered output
        elif ext == '.php': program = "php"; args = [file_path]
        elif ext == '.js': program = "node"; args = [file_path]
        elif ext == '.sh': program = "bash"; args = [file_path]
        else:
            self.append_output(f"⚠ No sé ejecutar {ext}\n", "#cca700")
            self.stop_process(); return

        self.process.start(program, args)

    def send_input(self):
        if self.process and self.process.state() == QProcess.Running:
            text = self.input_line.text()
            self.append_output(text + "\n", "#4ec9b0")
            self.process.write((text + "\n").encode())
            self.input_line.clear()

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="ignore")
        self.append_output(text, "#d4d4d4")

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="ignore")
        self.append_output(text, "#ff6b6b")

    def append_output(self, text, color_hex):
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = self.output_area.currentCharFormat()
        fmt.setForeground(QColor(color_hex))
        cursor.insertText(text, fmt)
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def stop_process(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill(); self.process.waitForFinished()
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Terminal inactiva")

    def process_finished(self, exit_code, exit_status):
        self.append_output(f"\n[Fin con código {exit_code}]", "#888888")
        self.stop_process()

    def update_theme(self, colors):
        bg = colors.get('bg', '#1e1e1e')
        fg = colors.get('fg', '#d4d4d4')
        self.output_area.setStyleSheet(f"background-color: {bg}; color: {fg}; border: none;")
        self.input_line.setStyleSheet(f"background-color: {colors.get('line_bg', '#252526')}; color: {fg}; border: 1px solid #3e3e42; padding: 4px;")