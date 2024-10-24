from flask import request
import sys 
import os

from services import ProjectService, FileService, ExecutionService, CursorService

def register_cursor_handlers(socketio):
    @socketio.on('cursor_move')
    def handle_cursor_move(data):
        session_id = request.sid
        position = data['position']
        
        socketio.emit('cursor_update', {
            'user_id': session_id,
            'position': position
        }, to=request.sid)  

    @socketio.on('disconnect')
    def handle_disconnect():
        session_id = request.sid
        if CursorService.remove_user(session_id):
            socketio.emit('user_disconnected', {
                'user_id': session_id
            }, broadcast=True)