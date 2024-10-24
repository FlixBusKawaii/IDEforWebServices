from flask import request
from flask_socketio import emit
from services.cursor_service import CursorService
from services.project_service import ProjectService

def register_project_handlers(socketio):
    @socketio.on('connect')
    def handle_connect():  
        session_id = request.sid
        cursor_info = CursorService.add_user(session_id)
        socketio.emit('user_connected', {
            'user_id': session_id, 
            'color': cursor_info['color']
        }, to='broadcast')  
        socketio.emit('project_list', {
            'projects': ProjectService.get_projects()
        })

        def handle_disconnect():
            session_id = request.sid
            if CursorService.remove_user(session_id):
                socketio.emit('user_disconnected', {
                    'session_id': session_id
                }, broadcast=True)

    @socketio.on('create_project')
    def handle_create_project(data):
        if ProjectService.create_project(data['name']):
            socketio.emit('project_created', {'name': data['name']}, to='broadcast')
            socketio.emit('project_list', {
                'projects': ProjectService.get_projects()
            }, to='broadcast')
        else:
            socketio.emit('project_error', {'error': 'Project already exists'})

    @socketio.on('delete_project')
    def handle_delete_project(data):
        if ProjectService.delete_project(data['name']):
            socketio.emit('project_deleted', {'name': data['name']}, to='broadcast')
            socketio.emit('project_list', {
                'projects': ProjectService.get_projects()
            }, to='broadcast')

    @socketio.on('select_project')
    def handle_select_project(data):
        project_name = data['name']
        files = ProjectService.get_project_files(project_name)
        socketio.emit('project_selected', {'name': project_name, 'files': files})
