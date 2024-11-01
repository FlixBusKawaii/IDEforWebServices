class ConnectedUsersService:
    connected_users = {}

    @staticmethod
    def add_user(user_id, username):
        ConnectedUsersService.connected_users[user_id] = username

    @staticmethod
    def remove_user(user_id):
        ConnectedUsersService.connected_users.pop(user_id, None)

    @staticmethod
    def get_users():
        return [{'user_id': uid, 'username': uname} for uid, uname in ConnectedUsersService.connected_users.items()]
