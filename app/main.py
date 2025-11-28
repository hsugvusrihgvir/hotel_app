import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from app.main_window import MainWindow
from app.db.db import Database



def main():
    app = QApplication(sys.argv)
    db = Database()

    try:
        db.connect()
    except Exception as e:
        QMessageBox.critical(None, "Ошибка подключения", str(e))
        return

    w = MainWindow(db)
    w.show()

    code = app.exec()

    db.close()
    sys.exit(code)


if __name__ == "__main__":
    main()