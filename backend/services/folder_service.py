import os
from config import Config

class folderService:
    @staticmethod
    def create_folder(project_name, foldername):
        if not project_name:
            raise ValueError('No project selected')
            
        folder_path = os.path.join(Config.PROJECTS_DIR, project_name, foldername)
        os.makedirs(folder_path, exist_ok=True)
        return foldername

    @staticmethod
    def rename_folder(project_name, old_name, new_name):
        if not project_name:
            raise ValueError('No project selected')

        old_path = os.path.join(Config.PROJECTS_DIR, project_name, old_name)
        new_path = os.path.join(Config.PROJECTS_DIR, project_name, new_name)

        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            return True
        return False

    @staticmethod
    def delete_folder(project_name, foldername):
        if not project_name:
            raise ValueError('No project selected')

        folder_path = os.path.join(Config.PROJECTS_DIR, project_name, foldername)
        if os.path.exists(folder_path):
            os.remove(folder_path)
            return True
        return False

    @staticmethod
    def save_folder(project_name, foldername, content):
        if not project_name:
            raise ValueError('No project selected')

        folder_path = os.path.join(Config.PROJECTS_DIR, project_name, foldername)
        os.makedirs(os.path.dirname(folder_path), exist_ok=True)
        with open(folder_path, 'w') as f:
            f.write(content)

    @staticmethod
    def load_folder(project_name, foldername):
        if not project_name:
            raise ValueError('No project selected')

        folder_path = os.path.join(Config.PROJECTS_DIR, project_name, foldername)
        with open(folder_path, 'r') as f:
            return f.read()