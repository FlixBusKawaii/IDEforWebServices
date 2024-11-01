class CursorService:
    user_cursors = {}

    @staticmethod
    def add_user(session_id):
        CursorService.user_cursors[session_id] = {
            'position': {'row': 0, 'column': 0},
            'color': f'#{hash(session_id) % 0xFFFFFF:06x}'
        }
        return CursorService.user_cursors[session_id]

    @staticmethod
    def update_cursor(session_id, position):
        if session_id in CursorService.user_cursors:
            CursorService.user_cursors[session_id]['position'] = position
            return True
        return False

    @staticmethod
    def remove_user(session_id):
        if session_id in CursorService.user_cursors:
            del CursorService.user_cursors[session_id]
            return True
        return False

    @staticmethod
    def get_user_cursor(session_id):
        return CursorService.user_cursors.get(session_id)