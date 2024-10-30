from services.connected_users_service import ConnectedUsersService

def register_connected_users_handlers(socketio):
    @socketio.on('user_connected')
    def handle_user_connected(data):
        user_id = data.get('user_id')
        username = data.get('username')
        if user_id and username:
            ConnectedUsersService.add_user(user_id, username)
            emit_user_list(socketio)

    @socketio.on('user_disconnected')
    def handle_user_disconnected(data):
        user_id = data.get('user_id')
        if user_id:
            ConnectedUsersService.remove_user(user_id)
            emit_user_list(socketio)

    def emit_user_list(socketio):
        user_list = ConnectedUsersService.get_users()
        socketio.emit('update_user_list', {'users': user_list})
