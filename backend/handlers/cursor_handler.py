from flask import request
from flask_socketio import emit
import sys 
import os
from services import ProjectService, FileService, ExecutionService, CursorService

def register_cursor_handlers(socketio):
    @socketio.on('cursor_move')
    def handle_cursor_move(data):
        
        user_id = data.get('user_id')  
        position = data['pos']
        
        emit('cursor_update', {
            'user_id': user_id,  
            'position': position,
            'currentFile':data['currentFile']

        }, broadcast=True, include_self=False)   

    @socketio.on('disconnect')
    def handle_disconnect():
        session_id = request.sid
        if CursorService.remove_user(session_id):
            emit('user_disconnected', {
                'user_id': session_id
            }, broadcast=True)