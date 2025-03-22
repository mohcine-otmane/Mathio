import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QCheckBox, QPushButton, QTextEdit, 
                           QProgressBar, QLabel, QGroupBox, QScrollArea, 
                           QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from math_book_downloader import MathBookDownloader
import logging

class LogHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback(msg)

class DownloaderThread(QThread):
    progress_signal = Signal(str)
    finished_signal = Signal(int)
    
    def __init__(self, download_dir):
        super().__init__()
        self.download_dir = download_dir
        self.downloader = MathBookDownloader()
        self.downloader.download_dir = download_dir

        # Set up logging for this thread
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add our custom handler that will emit signals
        handler = LogHandler(self.log_message)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    def log_message(self, message):
        self.progress_signal.emit(message)

    def run(self):
        try:
            self.downloader.scrape_arxiv()
            self.finished_signal.emit(len(self.downloader.downloaded_files))
        except Exception as e:
            self.progress_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(0)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mathematics Document Downloader")
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create info section
        info_label = QLabel(
            "This tool downloads mathematics documents from arXiv, focusing on:"
            "\n• Textbooks and Lecture Notes"
            "\n• Course Materials"
            "\n• Introductory Texts"
            "\n\nTopics include: Topology, Algebra, Analysis, Geometry, Number Theory, "
            "and more advanced subjects."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 10pt; margin: 10px;")
        layout.addWidget(info_label)
        
        # Create directory selection
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("Download Directory:")
        self.dir_path = QLabel("math_books")
        dir_button = QPushButton("Change")
        dir_button.clicked.connect(self.change_directory)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_path, stretch=1)
        dir_layout.addWidget(dir_button)
        layout.addLayout(dir_layout)
        
        # Create progress section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        progress_layout.addWidget(self.log_display)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Download")
        self.start_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Add notes
        notes = [
            "Note: Downloads may take some time. Please be patient.",
            "The tool will automatically filter for educational content.",
            "Files will be organized by mathematical category."
        ]
        
        for note in notes:
            note_label = QLabel(note)
            note_label.setStyleSheet("color: gray; font-style: italic;")
            note_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(note_label)
        
        self.downloader_thread = None

    def log_message(self, message):
        self.log_display.append(message)
        # Scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def change_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if dir_path:
            self.dir_path.setText(dir_path)

    def start_download(self):
        # Disable controls during download
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # Clear previous logs
        self.log_display.clear()
        
        # Start download thread
        self.downloader_thread = DownloaderThread(self.dir_path.text())
        self.downloader_thread.progress_signal.connect(self.log_message)
        self.downloader_thread.finished_signal.connect(self.download_finished)
        self.downloader_thread.start()

    def cancel_download(self):
        if self.downloader_thread and self.downloader_thread.isRunning():
            self.downloader_thread.terminate()
            self.downloader_thread.wait()
            self.log_message("Download cancelled by user.")
            self.download_finished(0)

    def download_finished(self, num_files):
        # Re-enable controls
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        if num_files > 0:
            QMessageBox.information(self, "Success", 
                                  f"Downloaded {num_files} files successfully!\n"
                                  f"Files are saved in: {self.dir_path.text()}")
        else:
            QMessageBox.warning(self, "Warning", 
                              "No files were downloaded. Check the log for details.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 