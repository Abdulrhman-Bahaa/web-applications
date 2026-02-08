from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt6.QtCore import QThread, pyqtSignal
import socket
import sys


class ConnectThread(QThread):
    result = pyqtSignal(bool, str)

    def __init__(self, ip: str, port: int, timeout: float = 5.0):
        super().__init__()
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def run(self):
        try:
            with socket.create_connection((self.ip, self.port), timeout=self.timeout) as s:
                peer = s.getpeername()
                self.result.emit(True, f"Connected to {peer[0]}:{peer[1]}")
        except Exception as e:
            self.result.emit(False, f"Connection failed: {e}")


class SocketGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Socket Connector")
        self._build_ui()
        self.thread = None

    def _build_ui(self):
        layout = QVBoxLayout()

        # IP input
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP Address:")
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("127.0.0.1")
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_edit)
        layout.addLayout(ip_layout)

        # Port input
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("8080")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_edit)
        layout.addLayout(port_layout)

        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect)
        layout.addWidget(self.connect_btn)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def on_connect(self):
        ip = self.ip_edit.text().strip() or "127.0.0.1"
        port_text = self.port_edit.text().strip() or "0"
        try:
            port = int(port_text)
        except ValueError:
            self.status_label.setText("Invalid port number")
            return

        self.connect_btn.setEnabled(False)
        self.status_label.setText("Connecting...")

        self.thread = ConnectThread(ip, port)
        self.thread.result.connect(self.on_result)
        self.thread.start()

    def on_result(self, ok: bool, message: str):
        self.status_label.setText(message)
        self.connect_btn.setEnabled(True)
        # thread will finish automatically


def run_app(argv=None):
    app = QApplication(argv or sys.argv)
    w = SocketGui()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
