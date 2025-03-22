import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QCheckBox, QPushButton, QTextEdit, 
                           QProgressBar, QLabel, QGroupBox, QScrollArea, 
                           QFileDialog, QMessageBox, QGridLayout)
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
    download_progress_signal = Signal(str, float)  # filename, progress percentage
    finished_signal = Signal(int)
    
    def __init__(self, download_dir, selected_sources):
        super().__init__()
        self.download_dir = download_dir
        self.selected_sources = selected_sources
        self.downloader = MathBookDownloader(progress_callback=self.update_progress)
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

    def update_progress(self, filename, progress):
        self.download_progress_signal.emit(filename, progress)

    def run(self):
        try:
            self.downloader.run(self.selected_sources)
            self.finished_signal.emit(len(self.downloader.downloaded_files))
        except Exception as e:
            self.progress_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(0)

class ProgressWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.progress_bars = {}
        self.setLayout(self.layout)

    def update_progress(self, filename, progress):
        if filename not in self.progress_bars:
            # Create new progress bar group
            group = QWidget()
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(2)
            
            label = QLabel(f"Downloading: {filename}")
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            
            group_layout.addWidget(label)
            group_layout.addWidget(progress_bar)
            
            self.layout.addWidget(group)
            self.progress_bars[filename] = (group, progress_bar)
        
        # Update progress
        _, progress_bar = self.progress_bars[filename]
        progress_bar.setValue(int(progress))
        
        # Remove completed downloads after a delay
        if progress >= 100:
            group, _ = self.progress_bars[filename]
            self.layout.removeWidget(group)
            group.deleteLater()
            del self.progress_bars[filename]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mathematics Document Downloader")
        self.setMinimumSize(900, 700)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create source selection group
        source_group = QGroupBox("Select Document Sources")
        source_layout = QGridLayout()
        
        self.source_checkboxes = {
            'arxiv': {
                'checkbox': QCheckBox("arXiv"),
                'description': "Research papers, lecture notes, and academic materials",
                'default': True
            },
            'open_textbook': {
                'checkbox': QCheckBox("Open Textbook Library"),
                'description': "Free, peer-reviewed textbooks from the University of Minnesota",
                'default': True
            },
            'oer_commons': {
                'checkbox': QCheckBox("OER Commons"),
                'description': "Open educational resources and college-level mathematics textbooks",
                'default': True
            },
            'merlot': {
                'checkbox': QCheckBox("MERLOT"),
                'description': "Curated collection of free and open online teaching and learning materials",
                'default': True
            }
        }
        
        row = 0
        for key, source_info in self.source_checkboxes.items():
            checkbox = source_info['checkbox']
            checkbox.setChecked(source_info['default'])
            source_layout.addWidget(checkbox, row, 0)
            
            desc = QLabel(source_info['description'])
            desc.setWordWrap(True)
            desc.setStyleSheet("color: gray; font-size: 10pt;")
            source_layout.addWidget(desc, row, 1)
            row += 1
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Create directory selection
        dir_group = QGroupBox("Download Settings")
        dir_layout = QVBoxLayout()
        
        dir_selector = QHBoxLayout()
        self.dir_label = QLabel("Download Directory:")
        self.dir_path = QLabel("math_books")
        dir_button = QPushButton("Change")
        dir_button.clicked.connect(self.change_directory)
        
        dir_selector.addWidget(self.dir_label)
        dir_selector.addWidget(self.dir_path, stretch=1)
        dir_selector.addWidget(dir_button)
        dir_layout.addLayout(dir_selector)
        
        # Add organization info
        org_label = QLabel(
            "Downloads will be organized in subdirectories by source:\n"
            "• arxiv/ - Mathematics papers and lecture notes from arXiv\n"
            "• open_textbook/ - Free textbooks from Open Textbook Library\n"
            "• oer_commons/ - Open educational resources from OER Commons\n"
            "• merlot/ - Teaching and learning materials from MERLOT"
        )
        org_label.setStyleSheet("color: #666; font-size: 10pt; margin: 5px;")
        dir_layout.addWidget(org_label)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Create progress section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        # Add progress widget for individual downloads
        self.progress_widget = ProgressWidget()
        progress_layout.addWidget(self.progress_widget)
        
        # Add log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMinimumHeight(200)
        
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
            "Files will be organized by source and mathematical category.",
            "The downloader respects server rate limits to ensure reliable downloads."
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
        # Get selected sources
        selected_sources = [key for key, info in self.source_checkboxes.items() 
                          if info['checkbox'].isChecked()]
        
        if not selected_sources:
            QMessageBox.warning(self, "Warning", "Please select at least one source!")
            return
        
        # Disable controls during download
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        for info in self.source_checkboxes.values():
            info['checkbox'].setEnabled(False)
        
        # Clear previous logs
        self.log_display.clear()
        
        # Start download thread
        self.downloader_thread = DownloaderThread(self.dir_path.text(), selected_sources)
        self.downloader_thread.progress_signal.connect(self.log_message)
        self.downloader_thread.download_progress_signal.connect(self.progress_widget.update_progress)
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
        for info in self.source_checkboxes.values():
            info['checkbox'].setEnabled(True)
        
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
    sys.exit(app.exec_()) 