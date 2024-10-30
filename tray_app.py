import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QSlider, QWidget, QVBoxLayout, QWidgetAction
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import asyncio
import threading

from main import apply_brightness, start_program  

class TrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self.app)

        # Menu for system tray
        self.menu = QMenu()

        # Brightness control slider in tray menu
        brightness_widget = QWidget()
        layout = QVBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_brightness_change)
        layout.addWidget(self.brightness_slider)
        brightness_widget.setLayout(layout)

        # Add start action to the menu
        start_action = self.menu.addAction("Start")
        start_action.triggered.connect(self.start_program)

        self.menu.addSeparator()

        # Add brightness control widget to the menu
        brightness_widget_action = QWidgetAction(self.menu)
        brightness_widget_action.setDefaultWidget(brightness_widget)
        self.menu.addAction(brightness_widget_action)

        # Add quit action to the menu
        quit_action = self.menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)

        # Attach menu to the tray icon
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

    def start_program(self):
        start_program()

    def on_brightness_change(self, value):
        
        asyncio.run(apply_brightness(value))

    def quit_app(self):
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = TrayApp()
    app.run()
