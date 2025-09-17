import os
from PyQt5.QtCore import QObject, pyqtSignal


class AssignmentFolderMonitor(QObject):
    """监控作业文件夹变化的工具类"""
    files_changed = pyqtSignal(str)  # 信号，当文件变化时触发

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.known_files = self._get_current_files()

    def _get_current_files(self):
        """获取当前文件夹中的文件列表"""
        if not os.path.exists(self.folder_path):
            return set()
        return set(os.listdir(self.folder_path))

    def check_for_changes(self):
        """检查文件夹是否有变化"""
        current_files = self._get_current_files()
        added = current_files - self.known_files
        removed = self.known_files - current_files

        if added or removed:
            self.known_files = current_files
            self.files_changed.emit(self.folder_path)
            return True
        return False

    def get_student_files(self, student_id):
        """获取指定学生的作业文件"""
        files = []
        for file in self.known_files:
            if student_id in file:  # 假设文件名包含学号
                files.append(file)
        return files