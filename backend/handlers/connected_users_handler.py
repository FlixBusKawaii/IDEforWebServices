from services.connected_users_service import ConnectedUsersService
from flask_socketio import emit
from flask import request
import json

def register_connected_users_handlers(socketio):
    @socketio.on('user_connected')
    def handle_user_connected(data):
        try:
            user_cookie = request.cookies.get('user_data')
            if user_cookie:
                user_data = json.loads(user_cookie)
                user_id = user_data.get('user_id')
                username = user_data.get('username')
                
                if user_id and username:
                    ConnectedUsersService.add_user(user_id, username)
                    emit('update_user_list', {
                        'user_id': user_id,
                        'username': username,
                        'update_type': 'add',
                        'color': '#333',  # Vous pouvez remplacer par une fonction pour générer une couleur aléatoire
                        'users': ConnectedUsersService.get_users()
                    }, broadcast=True)
            else:
                emit('connect_error', {
                    'error': 'No user data in cookies'
                })

        except Exception as e:
            emit('connect_error', {
                'error': str(e)
            })

    @socketio.on('user_disconnected')
    def handle_user_disconnected(data):
        user_id = data.get('user_id')
        if user_id:
            ConnectedUsersService.remove_user(user_id)
            emit('update_user_list', {
                'user_id': user_id,
                'update_type': 'disconnect',
                'users': ConnectedUsersService.get_users()
            }, broadcast=True)
