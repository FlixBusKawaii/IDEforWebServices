from services.execution_service import ExecutionService

def register_execution_handlers(socketio):
    @socketio.on('execute_code')
    def handle_execute_code(data):
        try:
            if data.get('filename').endswith(".py") : 
                result = ExecutionService.execute_python_file(
                    data.get('project'),
                    data.get('filename'),
                    data.get('code')
                )
                socketio.emit('code_output', result)
            if data.get('filename').endswith(".c") : 
                result = ExecutionService.execute_c_file(
                    data.get('project'),
                    data.get('filename'),
                    data.get('code')
                )
                socketio.emit('code_output', result)
        
        except Exception as e:
            socketio.emit('code_output', {
                'error': str(e),
                'success': False
            })