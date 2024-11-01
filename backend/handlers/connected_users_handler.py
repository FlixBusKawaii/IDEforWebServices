from services.connected_users_service import ConnectedUsersService
from flask_socketio import emit

def register_connected_users_handlers(socketio):
    @socketio.on('user_connected')
    def handle_user_connected(data):
        try:
            user_id = data.get('user_id')
            username = data.get('username')
            if user_id and username:
                ConnectedUsersService.add_user(user_id, username)
                
                emit('update_user_list',{
                    'user_id' : data.get('user_id'),
                    'username' : data.get('username'),
                    'update_type': 'add',
                    'color' : '#333', # faire l'algo de random color
                    'users' : ConnectedUsersService.get_users()
                }, broadcast=True)
        
        except Exception as e:
            emit('connect_error', {
                'error': str(e)
            })

                

    @socketio.on('user_disconnected')
    def handle_user_disconnected(data):
        user_id = data.get('user_id')
        if user_id:
            ConnectedUsersService.remove_user(user_id)
            emit('update_user_list',{
                'user_id' : data.get('user_id'),
                'update_type': 'disconnect',
                'users' : ConnectedUsersService.get_users()
            },broadcast=True)

    