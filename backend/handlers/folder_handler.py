from flask import request
from flask_socketio import emit

from services.folder_service import folderService
from services.project_service import ProjectService

def register_folder_handlers(socketio):
    @socketio.on('create_folder')
    def handle_create_folder(data):
        try:
            foldername = folderService.create_folder(
                data.get('project'),
                data.get('name'),
            )
            # Obtenir la liste mise à jour des fichiers et dossiers
            files = ProjectService.get_project_files(data.get('project'))
            
            emit('folder_created', {
                'name': foldername,
                'project': data.get('project'),
                'files': files,
                
            }, broadcast=True)
        except Exception as e:
            emit('folder_error', {'error': str(e)})
        
    @socketio.on('save_folder')
    def handle_save_folder(data):
        try:
            folderService.save_folder(
                data['project'],
                data['foldername'],
                data['content']
            )
            emit('folder_saved', {
                'foldername': data['foldername'],
                'project': data['project']
            }, broadcast=True)
        except Exception as e:
            emit('save_error', {'error': str(e)})

    @socketio.on('load_folder')
    def handle_load_folder(data):
        try:
            content = folderService.load_folder(data['project'], data['foldername'])
            emit('folder_content', {
                'content': content,
                'foldername': data['foldername']
            })
        except Exception as e:
            emit('load_error', {'error': str(e)})
    
    @socketio.on('delete_folder')
    def handle_delete_file(data):
        try:
            folderService.delete_folder(data['project'], data['name'])
            emit('folder_deleted', {
            'name': data['name'],
            'files': ProjectService.get_project_files(data['project'])
            }, broadcast=True)
        except Exception as e:
            emit('load_error', {'error': str(e)})

