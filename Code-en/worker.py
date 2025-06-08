# worker.py (English Version)
import hashlib
import shutil
import os
from collections import defaultdict
from pathlib import Path
import yaml
from PySide6.QtCore import QObject, Signal

SEVERITY_TO_FOLDER_MAP = {
    "critical": "critical", "high": "high", "medium": "medium",
    "low": "low", "info": "info", "informative": "info",
    "informational": "info", "unknown": "unknown"
}
DEFAULT_FOLDER = "other_or_no_severity"

class Worker(QObject):
    progress_log = Signal(str)
    progress_percent = Signal(int)
    finished = Signal(dict)

    def do_organize_templates(self, file_list, target_dir_str):
        self.progress_log.emit("Task started: Classifying templates...")
        ORGANIZED_TEMPLATES_DIR = Path(target_dir_str)
        DEBUG_LOG_FILE = ORGANIZED_TEMPLATES_DIR / "classification_debug.log"
        ORGANIZED_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        total_files = len(file_list)
        if total_files == 0:
            self.progress_log.emit("Error: No files to process.")
            self.finished.emit({"status": "classification_done"})
            return
        self.progress_log.emit(f"Found {total_files} files, starting process...")
        current_debug_log_entries = []

        for i, template_file_path in enumerate(file_list):
            template_file = Path(template_file_path)
            extracted_value = self.get_template_severity(template_file, current_debug_log_entries)
            
            target_folder_name = DEFAULT_FOLDER
            if extracted_value:
                target_folder_name = SEVERITY_TO_FOLDER_MAP.get(extracted_value.lower(), extracted_value)
            
            destination_folder = ORGANIZED_TEMPLATES_DIR / target_folder_name
            destination_folder.mkdir(parents=True, exist_ok=True)
            destination_file_path = destination_folder / template_file.name
            
            try:
                shutil.copy2(str(template_file), str(destination_file_path))
            except shutil.SameFileError:
                pass
            except Exception as e:
                self.progress_log.emit(f"Error: Failed to copy {template_file.name}: {e}")

            self.progress_percent.emit(int((i + 1) * 100 / total_files))

        try:
            with open(DEBUG_LOG_FILE, 'w', encoding='utf-8') as debug_f:
                debug_f.write("Nuclei Template Classification Debug Log\n---\n")
                debug_f.write("\n".join(current_debug_log_entries))
            self.progress_log.emit(f"Detailed debug log saved to: {DEBUG_LOG_FILE}")
        except Exception as e:
            self.progress_log.emit(f"Failed to write log file: {e}")
            
        self.finished.emit({"status": "classification_done"})

    def do_find_duplicates(self, file_list):
        self.progress_log.emit("Task started: Finding duplicate templates...")
        templates_by_id = defaultdict(list)
        templates_by_hash = defaultdict(list)
        total_files = len(file_list)
        if total_files == 0:
            self.progress_log.emit("Error: No files to process.")
            self.finished.emit({"status": "deduplication_done", "results": {}})
            return
        self.progress_log.emit(f"Found {total_files} files, starting scan...")

        for i, template_file_path in enumerate(file_list):
            template_file = Path(template_file_path)
            template_id = self.get_template_id_for_dedup(template_file)
            file_hash = self.get_file_hash_for_dedup(template_file)
            
            if template_id:
                templates_by_id[template_id].append(str(template_file))
            if file_hash:
                templates_by_hash[file_hash].append(str(template_file))

            self.progress_percent.emit(int((i + 1) * 100 / total_files))

        id_duplicates = {tid: files for tid, files in templates_by_id.items() if len(files) > 1}
        hash_duplicates = {f_hash: files for f_hash, files in templates_by_hash.items() if len(files) > 1}
        results = {
            "id_duplicates": id_duplicates,
            "hash_duplicates": hash_duplicates,
            "total_scanned": total_files
        }
        self.progress_log.emit("Deduplication scan finished.")
        self.finished.emit({"status": "deduplication_done", "results": results})

    def get_template_severity(self, file_path: Path, debug_log_entries):
        """
        Extracts the severity/risk level from a template file.
        It first looks for 'severity', then falls back to 'risk'.
        """
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'info' in data and isinstance(data['info'], dict):
                    info_block = data['info']
                    # Prioritize 'severity'
                    severity = info_block.get('severity')
                    if severity and isinstance(severity, str):
                        return severity.lower()
                    
                    # Fallback to 'risk'
                    risk = info_block.get('risk')
                    if risk and isinstance(risk, str):
                        return risk.lower()

        except Exception as e:
            debug_log_entries.append(f"Could not parse {file_path}: {e}")
        return None

    def get_file_hash_for_dedup(self, file_path: Path, hash_algo="sha256"):
        hasher = hashlib.new(hash_algo)
        try:
            with file_path.open('rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.progress_log.emit(f"Error calculating hash for {file_path}: {e}")
            return None

    def get_template_id_for_dedup(self, file_path: Path):
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'id' in data:
                    template_id = data.get('id')
                    if template_id and isinstance(template_id, str):
                        return template_id
        except Exception:
            pass
        return None