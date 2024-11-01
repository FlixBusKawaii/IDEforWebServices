import os
from config import Config

class FileService:
    @staticmethod
    def create_file(project_name, filename, filetype):
        if not project_name:
            raise ValueError('No project selected')
            
        full_filename = f"{filename}.{filetype}"
        file_path = os.path.join(Config.PROJECTS_DIR, project_name, full_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write('')
            
        return full_filename

    @staticmethod
    def rename_file(project_name, old_name, new_name):
        if not project_name:
            raise ValueError('No project selected')

        old_path = os.path.join(Config.PROJECTS_DIR, project_name, old_name)
        new_path = os.path.join(Config.PROJECTS_DIR, project_name, new_name)

        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            return True
        return False

    @staticmethod
    def delete_file(project_name, filename):
        if not project_name:
            raise ValueError('No project selected')

        file_path = os.path.join(Config.PROJECTS_DIR, project_name, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    @staticmethod
    def save_file(project_name, filename, content):
        if not project_name:
            raise ValueError('No project selected')

        file_path = os.path.join(Config.PROJECTS_DIR, project_name, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)

    @staticmethod
    def load_file(project_name, filename):
        if not project_name:
            raise ValueError('No project selected')

        file_path = os.path.join(Config.PROJECTS_DIR, project_name, filename)
        with open(file_path, 'r') as f:
            return f.read()