from flask import request
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
            socketio.emit('file_created', {
                'name': filename,
                'project': data.get('project'),
                'files': ProjectService.get_project_files(data.get('project'))
            }, broadcast=True)
        except Exception as e:
            socketio.emit('file_error', {'error': str(e)})

    @socketio.on('save_file')
    def handle_save_file(data):
        try:
            FileService.save_file(
                data['project'],
                data['filename'],
                data['content']
            )
            socketio.emit('file_saved', {
                'filename': data['filename'],
                'project': data['project']
            }, broadcast=True)
        except Exception as e:
            socketio.emit('save_error', {'error': str(e)})

    @socketio.on('load_file')
    def handle_load_file(data):
        try:
            content = FileService.load_file(data['project'], data['filename'])
            socketio.emit('file_content', {
                'content': content,
                'filename': data['filename']
            })
        except Exception as e:
            socketio.emit('load_error', {'error': str(e)})
