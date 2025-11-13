import sys
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    w = MainWindow() # создание меню
    w.setWindowTitle("Гостиница")
    w.show()
    sys.exit(app.exec())
#hiiii
if __name__ == "__main__":
    main()