# main.py (English Version)
import sys
import os
import base64
import ctypes
import multiprocessing
from ctypes import wintypes
from pathlib import Path
import yaml
from PySide6.QtGui import QIcon, QPixmap, QColor, QPalette
from PySide6.QtCore import Qt, QThread, QPoint, QEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser,
                               QFileDialog, QTreeWidget, QTreeWidgetItem, QSplitter,
                               QPlainTextEdit, QMessageBox, QProgressBar)

try:
    from icon_data import icon_base64
except ImportError:
    icon_base64 = "" 
from worker import Worker
from yaml_highlighter import YamlHighlighter

DARK_STYLE = """
#MainWindow, #CentralWidget { background-color: #1e2129; } #CustomTitleBar { background-color: #1e2129; height: 35px; } #TitleLabel { color: #a0a5b1; font-weight: bold; padding-left: 5px; } #MinimizeButton, #MaximizeButton, #CloseButton { background-color: transparent; border: none; width: 35px; height: 35px; padding: 8px; qproperty-iconSize: 12px; } #MinimizeButton:hover, #MaximizeButton:hover { background-color: #2c313c; } #CloseButton:hover { background-color: #e81123; } QWidget { background-color: #2c313c; color: #e0e5f1; border: none; font-family: "Segoe UI", "Microsoft YaHei", "Arial"; font-size: 10pt; } QTabWidget::pane { border-top: 2px solid #3c414d; } QTabBar::tab { background: #2c313c; color: #a0a5b1; padding: 10px 25px; border-top-left-radius: 4px; border-top-right-radius: 4px; min-width: 150px; } QTabBar::tab:selected, QTabBar::tab:hover { background: #3c414d; color: #ffffff; font-weight: bold; } QLabel { color: #a0a5b1; font-weight: bold; padding-top: 5px; } QLineEdit, QTextBrowser, QPlainTextEdit, QTreeWidget { background-color: #252932; color: #e0e5f1; border: 1px solid #3c414d; border-radius: 4px; padding: 5px; } QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #5d78ff; } QPushButton { background-color: #5d78ff; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px; min-height: 20px; } QPushButton:hover { background-color: #758fff; } QPushButton:disabled { background-color: #4a4e5a; color: #888888; } QMessageBox { background-color: #3c414d; } QProgressBar { border: 1px solid #3c414d; border-radius: 5px; text-align: center; color: #e0e5f1; background-color: #252932; } QProgressBar::chunk { background-color: #5d78ff; border-radius: 4px; } QTreeWidget::item { padding: 5px 0; } QTreeWidget::item:hover { background-color: #3c414d; } QTreeWidget::item:selected { background-color: #5d78ff; color: white; } QHeaderView::section { background-color: #3c414d; color: #a0a5b1; padding: 5px; border: 1px solid #252932; font-weight: bold; } QSplitter::handle { background-color: #3c414d; height: 3px; }
"""

class CustomTitleBar(QWidget):
    def __init__(self, parent, icon: QIcon):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("CustomTitleBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.iconLabel = QLabel(self)
        self.iconLabel.setPixmap(icon.pixmap(16, 16))
        layout.addWidget(self.iconLabel)
        self.titleLabel = QLabel("Nuclei Template Toolkit", self)
        self.titleLabel.setObjectName("TitleLabel")
        layout.addWidget(self.titleLabel)
        layout.addStretch()
        self.minimizeButton = QPushButton(self)
        self.minimizeButton.setObjectName("MinimizeButton")
        self.minimizeButton.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarMinButton))
        self.minimizeButton.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.minimizeButton)
        self.maximizeButton = QPushButton(self)
        self.maximizeButton.setObjectName("MaximizeButton")
        self.maximizeButton.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarMaxButton))
        self.maximizeButton.clicked.connect(self.toggle_maximize_restore)
        layout.addWidget(self.maximizeButton)
        self.closeButton = QPushButton(self)
        self.closeButton.setObjectName("CloseButton")
        self.closeButton.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarCloseButton))
        self.closeButton.clicked.connect(self.parent.close)
        layout.addWidget(self.closeButton)
        self.start_pos = None
        self.start_frame_pos = None

    def toggle_maximize_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximizeButton.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarMaxButton))
        else:
            self.parent.showMaximized()
            self.maximizeButton.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TitleBarNormalButton))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.start_frame_pos = self.parent.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.start_frame_pos + delta)

    def mouseReleaseEvent(self, event):
        self.start_pos = None
        self.start_frame_pos = None

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 128)) 
        self.setPalette(palette)
        self.setAutoFillBackground(True)

class MainWindow(QMainWindow):
    def __init__(self, icon: QIcon):
        super().__init__()
        self.setWindowTitle("Nuclei Template Toolkit")
        self.setGeometry(100, 100, 950, 750)
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self, icon)
        self.main_layout.addWidget(self.title_bar)
        
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.content_widget)

        self.overlay = OverlayWidget(self.content_widget)
        self.overlay.hide()
        
        self.classification_tab = self._create_classification_tab()
        self.deduplication_tab = self._create_deduplication_tab()
        self.editor_tab = self._create_editor_tab()
        
        self.tabs.addTab(self.classification_tab, "Template Classifier")
        self.tabs.addTab(self.deduplication_tab, "Template Deduplicator")
        self.tabs.addTab(self.editor_tab, "YAML Editor")

        self.is_task_running = False
        self.worker = None
        self.thread = None
        
        self.classify_file_list = []
        self.dedup_file_list = []

    def resizeEvent(self, event):
        self.overlay.resize(self.content_widget.size())
        super().resizeEvent(event)

    def _create_classification_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(QLabel("Select Template Files (Multi-Select Enabled):"))
        select_file_layout = QHBoxLayout()
        self.classify_file_display = QPlainTextEdit()
        self.classify_file_display.setReadOnly(True)
        self.classify_file_display.setPlaceholderText("Click 'Browse' to select one or more .yaml files...")
        select_file_layout.addWidget(self.classify_file_display)
        source_browse_btn = QPushButton("Browse...")
        source_browse_btn.clicked.connect(self._browse_source_files_classify)
        select_file_layout.addWidget(source_browse_btn)
        layout.addLayout(select_file_layout)
        layout.addWidget(QLabel("Destination Folder:"))
        target_layout = QHBoxLayout()
        self.classify_target_dir = QLineEdit()
        self.classify_target_dir.setPlaceholderText("Select a folder to store the classified results...")
        target_browse_btn = QPushButton("Browse...")
        target_browse_btn.clicked.connect(lambda: self._browse_directory(self.classify_target_dir))
        target_layout.addWidget(self.classify_target_dir)
        target_layout.addWidget(target_browse_btn)
        layout.addLayout(target_layout)
        
        self.classify_start_btn = QPushButton("Start Classification")
        self.classify_start_btn.clicked.connect(self._start_classification)
        layout.addWidget(self.classify_start_btn)
        
        self.classify_progress_bar = QProgressBar()
        self.classify_progress_bar.setVisible(False)
        layout.addWidget(self.classify_progress_bar)
        layout.addWidget(QLabel("Log Output:"))
        self.classify_log = QTextBrowser()
        layout.addWidget(self.classify_log)
        return widget

    def _create_deduplication_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(QLabel("Select Template Files for Deduplication (Multi-Select Enabled):"))
        select_file_layout = QHBoxLayout()
        self.dedup_file_display = QPlainTextEdit()
        self.dedup_file_display.setReadOnly(True)
        self.dedup_file_display.setPlaceholderText("Click 'Browse' to select one or more .yaml files...")
        select_file_layout.addWidget(self.dedup_file_display)
        source_browse_btn = QPushButton("Browse...")
        source_browse_btn.clicked.connect(self._browse_source_files_dedup)
        select_file_layout.addWidget(source_browse_btn)
        layout.addLayout(select_file_layout)

        self.dedup_start_btn = QPushButton("Start Deduplication")
        self.dedup_start_btn.clicked.connect(self._start_deduplication)
        layout.addWidget(self.dedup_start_btn)

        self.dedup_progress_bar = QProgressBar()
        self.dedup_progress_bar.setVisible(False)
        layout.addWidget(self.dedup_progress_bar)
        splitter = QSplitter(Qt.Vertical)
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(QLabel("Log Output:"))
        self.dedup_log = QTextBrowser()
        log_layout.addWidget(self.dedup_log)
        splitter.addWidget(log_container)
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.addWidget(QLabel("Deduplication Results:"))
        self.dedup_results_tree = QTreeWidget()
        self.dedup_results_tree.setHeaderLabels(["Duplicate Item (ID / Hash)", "File Path"])
        self.dedup_results_tree.setColumnWidth(0, 300)
        results_layout.addWidget(self.dedup_results_tree)
        splitter.addWidget(results_container)
        splitter.setSizes([150, 400])
        layout.addWidget(splitter)
        return widget

    def _create_editor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(QLabel("YAML Content Editor:"))
        self.editor_text = QPlainTextEdit()
        self.editor_text.setPlaceholderText("Write or paste new Nuclei template content here...")
        font = self.editor_text.font()
        font.setFamily("Courier New")
        self.editor_text.setFont(font)
        self.highlighter = YamlHighlighter(self.editor_text.document())
        layout.addWidget(self.editor_text)
        layout.addWidget(QLabel("Save to Folder:"))
        save_dir_layout = QHBoxLayout()
        self.editor_save_dir = QLineEdit()
        self.editor_save_dir.setPlaceholderText("Select a folder to save to...")
        save_dir_browse_btn = QPushButton("Browse...")
        save_dir_browse_btn.clicked.connect(lambda: self._browse_directory(self.editor_save_dir))
        save_dir_layout.addWidget(self.editor_save_dir)
        save_dir_layout.addWidget(save_dir_browse_btn)
        layout.addLayout(save_dir_layout)
        layout.addWidget(QLabel("Filename:"))
        self.editor_filename = QLineEdit()
        self.editor_filename.setPlaceholderText("e.g., my-new-template.yaml")
        layout.addWidget(self.editor_filename)
        
        self.editor_save_btn = QPushButton("Save File")
        self.editor_save_btn.clicked.connect(self._save_yaml_file)
        layout.addWidget(self.editor_save_btn)
        
        return widget

    def _browse_directory(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder")
        if directory:
            line_edit.setText(directory)

    def _browse_source_files_classify(self):
        if self.is_task_running: return
        files, _ = QFileDialog.getOpenFileNames(self, "Select Template Files", "", "YAML Files (*.yaml *.yml)")
        if files:
            self.classify_file_list = files
            self.classify_file_display.setPlainText("\n".join(files))

    def _browse_source_files_dedup(self):
        if self.is_task_running: return
        files, _ = QFileDialog.getOpenFileNames(self, "Select Template Files", "", "YAML Files (*.yaml *.yml)")
        if files:
            self.dedup_file_list = files
            self.dedup_file_display.setPlainText("\n".join(files))

    def _save_yaml_file(self):
        content = self.editor_text.toPlainText()
        save_dir = self.editor_save_dir.text()
        filename = self.editor_filename.text()
        if not all([content, save_dir, filename]):
            QMessageBox.warning(self, "Incomplete Information", "Please fill all fields: content, save folder, and filename.")
            return
        if not filename.endswith(('.yaml', '.yml')):
            filename += '.yaml'
        
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "Save Failed", f"Invalid YAML format. Cannot save:\n\n{e}")
            return

        file_path = Path(save_dir) / filename
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Success", f"File saved successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def _update_progress(self, value):
        if self.tabs.currentWidget() == self.classification_tab:
            self.classify_progress_bar.setValue(value)
        elif self.tabs.currentWidget() == self.deduplication_tab:
            self.dedup_progress_bar.setValue(value)

    def _set_ui_for_task_start(self):
        self.is_task_running = True
        self.classify_start_btn.setEnabled(False)
        self.dedup_start_btn.setEnabled(False)
        self.overlay.show()

    def _set_ui_for_task_finish(self):
        self.is_task_running = False
        self.classify_start_btn.setEnabled(True)
        self.dedup_start_btn.setEnabled(True)
        self.classify_progress_bar.setVisible(False)
        self.dedup_progress_bar.setVisible(False)
        self.overlay.hide()

    def _start_classification(self):
        if not self.classify_file_list or not self.classify_target_dir.text():
            QMessageBox.warning(self, "Incomplete Information", "Please select template files and a destination folder.")
            return
        file_list = [str(Path(f).absolute()) for f in self.classify_file_list]
        self._run_task("classify", file_list, self.classify_target_dir.text())

    def _start_deduplication(self):
        if not self.dedup_file_list:
            QMessageBox.warning(self, "Incomplete Information", "Please select template files to check for duplicates.")
            return
        file_list = [str(Path(f).absolute()) for f in self.dedup_file_list]
        self._run_task("deduplicate", file_list)

    def _run_task(self, task_type, *args):
        if self.is_task_running:
            return
        
        self._set_ui_for_task_start()
        
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        log_area = None
        progress_bar = None
        
        if task_type == "classify":
            self.thread.started.connect(lambda: self.worker.do_organize_templates(*args))
            log_area = self.classify_log
            progress_bar = self.classify_progress_bar
        elif task_type == "deduplicate":
            self.thread.started.connect(lambda: self.worker.do_find_duplicates(*args))
            log_area = self.dedup_log
            progress_bar = self.dedup_progress_bar
            self.dedup_results_tree.clear()
        else:
            self._set_ui_for_task_finish()
            return

        self.worker.progress_log.connect(log_area.append)
        self.worker.progress_percent.connect(self._update_progress)
        self.worker.finished.connect(self._task_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        
        log_area.clear()
        progress_bar.setValue(0)
        progress_bar.setVisible(True)
        
        self.thread.start()

    def _task_finished(self, data):
        if self.thread and self.thread.isRunning():
             self.thread.quit()
             self.thread.wait()

        self._set_ui_for_task_finish()

        status = data.get("status")

        if "classification" in status:
            self.classify_log.append("\n--- Classification task finished ---")
        elif "deduplication" in status:
            if status == "deduplication_done":
                self.dedup_log.append("\n--- Deduplication task finished ---")
                self._populate_dedup_results(data.get("results", {}))
        
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self.thread = None

    def _populate_dedup_results(self, results):
        self.dedup_results_tree.clear()
        total = results.get('total_scanned', 0)
        self.dedup_log.append(f"Total files scanned: {total}.")
        id_duplicates = results.get("id_duplicates", {})
        hash_duplicates = results.get("hash_duplicates", {})
        id_root = QTreeWidgetItem(self.dedup_results_tree, ["Potential Duplicates by Template ID"])
        if id_duplicates:
            for tid, files in id_duplicates.items():
                parent = QTreeWidgetItem(id_root, [f"ID: {tid} ({len(files)} files)"])
                for file in files:
                    QTreeWidgetItem(parent, ["", file])
        else:
            QTreeWidgetItem(id_root, ["No duplicates found based on ID."])
        id_root.setExpanded(True)
        hash_root = QTreeWidgetItem(self.dedup_results_tree, ["Exact Duplicates by File Hash"])
        if hash_duplicates:
            for f_hash, files in hash_duplicates.items():
                parent = QTreeWidgetItem(hash_root, [f"Hash: {f_hash[:12]}... ({len(files)} files)"])
                for file in files:
                    QTreeWidgetItem(parent, ["", file])
        else:
            QTreeWidgetItem(hash_root, ["No duplicates found based on hash."])
        hash_root.setExpanded(True)
        
    def closeEvent(self, event):
        if self.is_task_running:
            QMessageBox.information(self, 'Task in Progress', 'Please wait for the current task to finish before closing the window.')
            event.ignore()
        else:
            event.accept()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    if sys.platform == 'win32':
        my_app_id = 'MyCompany.MyProduct.SubProduct.1'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)

    try:
        if icon_base64:
            decoded_icon_data = base64.b64decode(icon_base64)
            pixmap = QPixmap()
            pixmap.loadFromData(decoded_icon_data)
            app_icon = QIcon(pixmap)
            app.setWindowIcon(app_icon)
        else:
            app_icon = QIcon()
    except Exception:
        app_icon = QIcon() 

    if DARK_STYLE:
        app.setStyleSheet(DARK_STYLE)

    window = MainWindow(icon=app_icon)
    window.show()
    sys.exit(app.exec())