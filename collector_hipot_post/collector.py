import sys
import os

# Garante que o diretório do script esteja no sys.path para importações locais
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from PySide6.QtWidgets import QApplication
from gui import HipotWindow


def main():
    app = QApplication(sys.argv)
    window = HipotWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
