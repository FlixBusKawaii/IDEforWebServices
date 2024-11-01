from flask import request
from flask_socketio import emit
from services.file_service import FileService
from services.project_service import ProjectService

def register_file_handlers(socketio):
    @socketio.on('create_file')
    def handle_create_file(data):
        try:
            filename = FileService.create_file(
                data.get('project'),
                data.get('name'),
                data.get('type')
            )
            emit('file_created', {
                'name': filename,
                'project': data.get('project'),
                'files': ProjectService.get_project_files(data.get('project'))
            }, broadcast=True)
        except Exception as e:
            emit('file_error', {'error': str(e)})

    @socketio.on('save_file')
    def handle_save_file(data):
        try:
            FileService.save_file(
                data['project'],
                data['filename'],
                data['content']
            )
            emit('file_saved', {
                'filename': data['filename'],
                'project': data['project']
            }, broadcast=True)
        except Exception as e:
            emit('save_error', {'error': str(e)})

    @socketio.on('load_file')
    def handle_load_file(data):
        try:
            content = FileService.load_file(data['project'], data['filename'])
            emit('file_content', {
                'content': content,
                'filename': data['filename'],
                'cursorpos' : data['cursorpos']
            })
        except Exception as e:
            emit('load_error', {'error': str(e)})
    
    @socketio.on('delete_file')
    def handle_delete_file(data):
        try:
            FileService.delete_file(data['project'], data['name'])
            emit('file_deleted', {
            'name': data['name'],
            'files': ProjectService.get_project_files(data['project'])
            }, broadcast=True)
        except Exception as e:
            emit('load_error', {'error': str(e)})

    @socketio.on('rename_file')
    def handle_rename_file(data):
        try:
            FileService.rename_file(data['project'], data['C'], data['newname'])

            emit('file_renamed',{
                "old_name" : data['filename'],
                "new_name" : data['newname']
            })
        except Exception as e:
            emit('load_error', {'error': str(e)})
