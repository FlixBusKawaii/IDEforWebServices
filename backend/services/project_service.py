import os
import shutil
from config import Config

class ProjectService:
    @staticmethod
    def get_projects():
        return [d for d in os.listdir(Config.PROJECTS_DIR) 
                if os.path.isdir(os.path.join(Config.PROJECTS_DIR, d))]

    @staticmethod
    def get_project_files(project_name):
        if not project_name:
            return []
        
        project_path = os.path.join(Config.PROJECTS_DIR, project_name)
        items = []
        
        for root, dirs, filenames in os.walk(project_path):
            # Filtrer les dossiers spéciaux
            dirs[:] = [d for d in dirs if d not in ['.', '..']]
            
            # Ajouter les dossiers
            for dir_name in dirs:
                full_dir_path = os.path.join(root, dir_name)
                rel_dir_path = os.path.relpath(full_dir_path, project_path)
                items.append({
                    'name': rel_dir_path,
                    'type': 'directory'
                })
                
            # Ajouter les fichiers
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, project_path)
                items.append({
                    'name': rel_path,
                    'type': 'file'
                })
        
        return items

    @staticmethod
    def create_project(project_name):
        project_path = os.path.join(Config.PROJECTS_DIR, project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            return True
        return False

    @staticmethod
    def delete_project(project_name):
        project_path = os.path.join(Config.PROJECTS_DIR, project_name)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
            return True
        return False