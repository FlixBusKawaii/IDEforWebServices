from flask import request
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
            socketio.emit('folder_created', {
                'name': foldername,
                'project': data.get('project'),
                'folders': ProjectService.get_project_folders(data.get('project'))
            }, broadcast=True)
        except Exception as e:
            socketio.emit('folder_error', {'error': str(e)})

    @socketio.on('save_folder')
    def handle_save_folder(data):
        try:
            folderService.save_folder(
                data['project'],
                data['foldername'],
                data['content']
            )
            socketio.emit('folder_saved', {
                'foldername': data['foldername'],
                'project': data['project']
            }, broadcast=True)
        except Exception as e:
            socketio.emit('save_error', {'error': str(e)})

    @socketio.on('load_folder')
    def handle_load_folder(data):
        try:
            content = folderService.load_folder(data['project'], data['foldername'])
            socketio.emit('folder_content', {
                'content': content,
                'foldername': data['foldername']
            })
        except Exception as e:
            socketio.emit('load_error', {'error': str(e)})
