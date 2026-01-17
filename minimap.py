from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

class CodeMinimap(QPlainTextEdit):
    def __init__(self, parent_editor):
        super().__init__()
        self.parent_editor = parent_editor
        self.setReadOnly(True)
        self.setFixedWidth(120)
        
        # Ocultar scrollbars
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Fuente pequeña para simular vista lejana
        font = QFont("Consolas", 4)
        self.setFont(font)
        
        # Configuración inicial (se sobreescribirá con el tema)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def sync_with_parent(self):
        """Copia el texto del editor principal al minimapa"""
        self.setPlainText(self.parent_editor.toPlainText())

    def update_scroll(self, value, maximum):
        """Sincroniza el scroll"""
        if maximum > 0:
            ratio = value / maximum
            my_max = self.verticalScrollBar().maximum()
            self.verticalScrollBar().setValue(int(my_max * ratio))

    def apply_theme(self, colors):
        """Recibe el diccionario de colores y actualiza el estilo"""
        bg = colors.get('bg', '#1e1e1e')
        fg = colors.get('fg', '#d4d4d4')
        
        # Aplicamos el estilo CSS dinámicamente
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-left: 1px solid {colors.get('line_bg', '#333')}; /* Borde sutil a la izquierda */
            }}
        """)