
const socket = io();
const username = localStorage.getItem('username') || prompt('Entrez votre nom:');
localStorage.setItem('username', username);

socket.on('connect', () => {
    localUserId = socket.id;
    console.log('Connected to server');
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
});

editor.session.on('change', function(delta) {
    if (!isReceivingUpdate && currentProject && currentFile) {
        // Envoyer la modification à tous les autres utilisateurs
        console.log('Editor change:', delta);
        socket.emit('editor_change', {
            delta: delta,
            project: currentProject,
            filename: currentFile
        });

        // Gérer la sauvegarde automatique
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            const currentContent = editor.getValue();
            if (currentContent !== lastSentContent) {
                console.log('Saving file:', {project: currentProject, filename: currentFile, content: currentContent});
                socket.emit('save_file', {
                    project: currentProject,
                    filename: currentFile,
                    content: currentContent
                });
                lastSentContent = currentContent;
            }
        }, 1000);
    }
});

socket.on('editor_change', function(data) {
    console.log('Received editor_change:', data);
    if (data.project === currentProject && data.filename === currentFile) {
        isReceivingUpdate = true;
        editor.session.getDocument().applyDeltas([data.delta]);
        isReceivingUpdate = false;
    }
});

socket.on('code_output', function(data) {
    console.log('Received code_output:', data);
    const outputElement = document.getElementById('output');

    if (data && data.output) {
        outputElement.innerHTML += `<span>${data.output}</span>`;
    }

    if (data && data.error) {
        outputElement.innerHTML += `<span class="error">${data.error}</span>`;
    }

    outputElement.scrollTop = outputElement.scrollHeight;
});

socket.on('project_list', function(data) {
    console.log('Received project_list:', data);
    const projectSelect = document.getElementById('project-select');
    projectSelect.innerHTML = '<option value="">Sélectionner un projet</option>';
    data.projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project;
        option.textContent = project;
        projectSelect.appendChild(option);
    });
});

socket.on('project_selected', function(data) {
    console.log('Received project_selected:', data);
    updateFileList(data.files);
});

socket.on('file_created', function(data) {
    console.log('Received file_created:', data);
    updateFileList(data.files);
});

socket.on('file_renamed', function(data) {
    console.log('Received file_renamed:', data);
    updateFileList(data.files);
    if (currentFile === data.old_name) {
        currentFile = data.new_name;
    }
});

socket.on('file_deleted', function(data) {
    console.log('Received file_deleted:', data);
    updateFileList(data.files);
    if (currentFile === data.name) {
        currentFile = '';
        editor.setValue('');
        updateUIState();
    }
});

socket.on('file_saved', function(data) {
    console.log('Received file_saved:', data);
    showSaveStatus();
});

socket.on('file_content', function(data) {
    console.log('Received file_content:', data);
    isReceivingUpdate = true;
    editor.setValue(data.content, -1);
    lastSentContent = data.content;
    currentFile = data.filename;
    updateUIState();
    isReceivingUpdate = false;
});

socket.on('user_connected', function(data) {
    if (data.user_id !== localUserId) {
        createCursor(data.user_id, data.color);
    }
});

socket.on('user_disconnected', function(data) {
    if (cursors[data.user_id]) {
        cursors[data.user_id].cursor.remove();
        cursors[data.user_id].label.remove();
        delete cursors[data.user_id];
    }
});

socket.on('cursor_update', function(data) {
    if (data.user_id !== localUserId) {
        updateCursorPosition(data.user_id, data.position);
    }
});

editor.session.selection.on('changeCursor', () => {
    if (currentProject && currentFile) {
        const position = editor.selection.getCursor();
        console.log('Cursor moved:', position);
        socket.emit('cursor_move', { position });
    }
});

// Mise à jour des écouteurs d'événements socket
socket.on('folder_created', (data) => {
    console.log('Folder created:', data);
    // Rafraîchir la liste des fichiers avec les nouveaux dossiers
    updateFileList({
        files: data.files || [],
        folders: data.folders || []
    });
});

socket.on('project_selected', (data) => {
    console.log('Project selected:', data);
    updateFileList({
        files: data.files || [],
        folders: data.folders || []
    });
});