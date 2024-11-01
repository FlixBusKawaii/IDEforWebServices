const editor = ace.edit("editor");
editor.setTheme("ace/theme/clouds");

let currentFile = '';
let currentProject = '';
let isReceivingUpdate = false;
let localUserId = null;
let saveTimeout = null;
let lastSentContent = '';
const cursors = {};

const createFileBtn = document.getElementById('create-file-btn');
const renameFileBtn = document.getElementById('rename-file-btn');
const deleteFileBtn = document.getElementById('delete-file-btn');
const executeBtn = document.getElementById('execute-btn');
const themeToggleButton = document.getElementById('themeToggle');
const icon = themeToggleButton.querySelector('.icon');

editor.setReadOnly(true);
document.addEventListener('DOMContentLoaded', function() {
    const contextMenu = document.getElementById('contextMenu');
    const file_list = document.getElementById('file-list');

    file_list.addEventListener('contextmenu', function(e) {
        e.preventDefault();

        contextMenu.style.display = 'block';
        contextMenu.style.left = e.pageX + 'px';
        contextMenu.style.top = e.pageY + 'px';
    });

    document.addEventListener('click', function() {
        contextMenu.style.display = 'none';
    });
});

function handleMenuClick(option) {
    switch (option){
        case 'create_file':
            createFile();
            break;
        case 'rename_file':
            renameFile();
            break;
        case 'delete_file':
            deleteFile();
            break;
        case 'create_folder' :
            createFolder();
            break;
    }
}

function fetchIpAddress() {
    fetch('/get-ip')
        .then(response => response.json())
        .then(data => {
            document.getElementById('ipTooltip').textContent = "IP : " + data.ip;
        })
        .catch(error => {
            console.error("Erreur:", error);
        });
}

document.addEventListener('DOMContentLoaded', fetchIpAddress);

function createFolder() {
    const filename = document.getElementById('filename').value.trim();

    if (!filename) {
        alert('Please enter a foldername');
        return;
    }

    if (!currentProject) {
        alert('Please select a project first');
        return;
    }

    socket.emit('create_folder', {
        name: filename,
        project: currentProject
    });
}

function createProject() {
    const projectName = document.getElementById('project-name').value;
    if (projectName) {
        socket.emit('create_project', {name: projectName});
        document.getElementById('project-name').value = '';
    }
}

function deleteProject() {
    if (currentProject && confirm(`Êtes-vous sûr de vouloir supprimer le projet "${currentProject}" ?`)) {
        socket.emit('delete_project', {name: currentProject});
        currentProject = '';
        currentFile = '';
        editor.setValue('');
        updateUIState();
    }
}

function createFile() {
    const filename = document.getElementById('filename').value.trim();
    const fileType = document.getElementById('file-type').value.trim();

    if (!filename) {
        alert('Please enter a filename');
        return;
    }

    if (!currentProject) {
        alert('Please select a project first');
        return;
    }

    socket.emit('create_file', {
        name: filename,
        type: fileType,
        project: currentProject
    });
}

function renameFile() {
    if (currentFile && currentProject) {
        const newName = prompt('Nouveau nom du fichier:', currentFile);
        if (newName && newName !== currentFile) {
            socket.emit('rename_file', {
                old_name: currentFile,
                new_name: newName,
                project: currentProject
            });
        }
    }
}

function deleteFile() {
    if (currentFile && currentProject && confirm(`Êtes-vous sûr de vouloir supprimer le fichier "${currentFile}" ?`)) {
        socket.emit('delete_file', {name: currentFile, project: currentProject});
        currentFile = '';
        editor.setValue('');
        updateUIState();
    }
}

function showSaveStatus() {
    const saveStatus = document.getElementById('save-status');
    saveStatus.style.display = 'block';
    setTimeout(() => {
        saveStatus.style.display = 'none';
    }, 2000);
}

function executeCode() {
    const output = '';
    const error = '';
    if (!currentProject || !currentFile) {
        const outputElement = document.getElementById('output');
        outputElement.innerHTML += `<span class="error">Erreur : Aucun fichier actif. Sélectionnez un fichier avant d'exécuter.</span>\n`;
        return;
    }

    const outputElement = document.getElementById('output');
    outputElement.innerHTML += `<span class="success">> Exécution de ${currentFile} dans le projet ${currentProject}...</span>\n`;

    socket.emit('execute_code', {
        project: currentProject,
        filename: currentFile,
        code: editor.getValue()
    });
}

function clearTerminal() {
    const outputElement = document.getElementById('output');
    outputElement.innerHTML = '';
}

function updateFileList(data) {
    const fileList = document.getElementById('file-list');
    if (!fileList) {
        console.error('Élément file-list non trouvé dans le DOM');
        return;
    }
    console.log('fileList:', fileList); // Vérifiez que fileList n'est pas null
    fileList.innerHTML = ''; // Vider la liste existante

    if (!data || data.length === 0) {
        console.warn('Aucune donnée à afficher');
        return;
    }

    const cursorPosition = editor.getCursorPosition();

    for (let i = 0; i < data.length; i++) {
        const item = data[i];
        console.log(`Traitement de l'item: nom=${item.name}, type=${item.type}`); // Debug

        if (item.name === '.' || item.name === '..') continue;

        const li = document.createElement('li');
        const itemSpan = document.createElement('span');

        // Déterminez le type d'élément
        if (item.type === 'directory') {
            itemSpan.innerHTML = `📁 ${item.name || 'Sans nom'}`;
            itemSpan.classList.add('folder');
        } else {
            itemSpan.innerHTML = `📄 ${item.name || 'Sans nom'}`;
            itemSpan.classList.add('file');

            // Ajoutez un événement onclick
            li.onclick = () => {
                console.log(`Clic sur fichier: ${item.name}`); // Debug
                loadFile(item.name, cursorPosition);
            };
        }

        li.appendChild(itemSpan);
        fileList.appendChild(li); // Ajoutez li à fileList
        console.log('Élément ajouté:', li); // Vérifiez l'élément ajouté
    }

    // Vérifiez le nombre d'enfants après l'ajout
    console.log('Éléments dans fileList après ajout:', fileList.children.length);
}


function updateSubFileList(parentElement, items) {
    items.forEach(item => {
        const li = document.createElement('li');
        const itemSpan = document.createElement('span');
        const cursorPosition = editor.getCursorPosition();

        if (typeof item === 'object' && item.type === 'folder') {
            itemSpan.textContent = `📁 ${item.name}`;
            li.classList.add('folder-item');
            li.onclick = (e) => {
                e.stopPropagation();
                li.classList.toggle('folder-open');
            };
        } else {
            itemSpan.textContent = `📄 ${item}`;
            li.onclick = (e) => {
                e.stopPropagation();
                loadFile(item.name, cursorPosition);
            };
        }

        li.appendChild(itemSpan);
        parentElement.appendChild(li);
    });
}

function selectProject() {
    const projectSelect = document.getElementById('project-select');
    currentProject = projectSelect.value;
    currentFile = '';
    editor.setValue('');

    const fileActions = document.getElementById('file-actions');
    const projectInfo = document.getElementById('project-info');
    const currentProjectName = document.getElementById('current-project-name');

    if (currentProject) {
        fileActions.classList.add('visible');
        projectInfo.classList.add('visible');
        currentProjectName.textContent = currentProject;
        socket.emit('select_project', {name: currentProject});
    } else {
        fileActions.classList.remove('visible');
        projectInfo.classList.remove('visible');
        currentProjectName.textContent = '';
    }

    updateUIState();
}

function geteditorSyntax(filename){
    let editorSyntax = "";
    if (filename.endsWith(".py")) {
        editorSyntax = "python";
    } else if (filename.endsWith(".c")) {
        editorSyntax = "c_cpp";
    } else {
        editorSyntax = "python";
    }
    editor.session.setMode("ace/mode/" + editorSyntax);
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');

    if (document.body.classList.contains('dark-theme')) {
        icon.textContent = '🌙';
        editor.setTheme("ace/theme/monokai");
    } else {
        icon.textContent = '☀️';
        editor.setTheme("ace/theme/clouds");
    }
}
themeToggleButton.addEventListener('click', toggleTheme);

function loadFile(filename ,cursorPos) {
    if (!currentProject) return;

    const fileListItems = document.querySelectorAll('#file-list li');
    fileListItems.forEach(item => {
        item.classList.remove('selected');
    });

    const clickedFileItem = Array.from(fileListItems).find(item => item.textContent.trim() === filename);
    if (clickedFileItem) {
        clickedFileItem.classList.add('selected');
    }

    socket.emit('load_file', { filename: filename, project: currentProject , cursorpos :cursorPos });
    currentFile = filename;
    geteditorSyntax(currentFile);

    updateUIState();
}

function updateUIState() {
    const projectSelected = currentProject !== '';
    const fileSelected = currentFile !== '';

    createFileBtn.disabled = !projectSelected;
    renameFileBtn.disabled = !projectSelected || !fileSelected;
    deleteFileBtn.disabled = !projectSelected || !fileSelected;
    executeBtn.disabled = !projectSelected || !fileSelected;
    editor.setReadOnly(!projectSelected || !fileSelected);
}

function createCursor(userId, color) {
    const cursorElement = document.createElement('div');
    cursorElement.className = 'cursor';
    cursorElement.style.backgroundColor = color;

    const labelElement = document.createElement('div');
    labelElement.className = 'cursor-label';
    labelElement.style.backgroundColor = color;
    labelElement.textContent = `User ${userId.slice(0, 4)}`;

    cursors[userId] = {
        cursor: cursorElement,
        label: labelElement
    };

    document.getElementById('editor-container').appendChild(cursorElement);
    document.getElementById('editor-container').appendChild(labelElement);
}

function updateCursorPosition(userId, position) {
    if (!cursors[userId]) return;

    const pixelPosition = editor.renderer.textToScreenCoordinates(position.row, position.column);
    const cursor = cursors[userId].cursor;
    const label = cursors[userId].label;

    cursor.style.left = `${pixelPosition.pageX}px`;
    cursor.style.top = `${pixelPosition.pageY}px`;

    label.style.left = `${pixelPosition.pageX}px`;
    label.style.top = `${pixelPosition.pageY - 20}px`;
}

const socket = io();
const username = localStorage.getItem('username') || prompt('Entrez votre nom:');
localStorage.setItem('username', username);

function setUserCookie(username, user_id) {
    const userData = JSON.stringify({
        username: username,
        user_id: user_id
    });
    document.cookie = `${userData}; path=/; max-age=${30 * 24 * 60 * 60}`;
}

function getUserCookie() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith('{')) {
            try {
                const cookieValue = cookie.split(';')[0];
                const userData = JSON.parse(cookieValue);
                return {
                    username: userData.username,
                    user_id: userData.user_id
                };
            } catch (e) {
                console.error("Erreur lors du parsing du cookie:", e);
            }
        }
    }
    return null;
}
socket.on('connect', () => {
    localUserId = socket.id;
    if(!getUserCookie()){
        uname = prompt("Entrez votre nom d'utilisateur");
        setUserCookie(uname,localUserId);
    }
    let userData = getUserCookie();
    socket.emit('user_connected', { user_id: userData["user_id"], username: userData["username"]});
});

socket.on('connect_error', (error) => {
});

editor.session.on('change', function(delta) {
    if (!isReceivingUpdate && currentProject && currentFile) {
        socket.emit('editor_change', {
            delta: delta,
            project: currentProject,
            filename: currentFile
        });

        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            const currentContent = editor.getValue();
            if (currentContent !== lastSentContent) {
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
    if (data.project === currentProject && data.filename === currentFile) {
        isReceivingUpdate = true;
        editor.session.getDocument().applyDeltas([data.delta]);
        isReceivingUpdate = false;
    }
});

socket.on('code_output', function(data) {
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
    
    console.log('project_selected event received:', data);
    console.log('Files received:', data.files);
    updateFileList(data.files);
});

socket.on('file_created', function(data) {
    console.log('project_selected event received:', data);
    console.log('Files received:', data.files);
    updateFileList(data.files);
});

socket.on('file_renamed', function(data) {
    updateFileList(data.files);
    if (currentFile === data.old_name) {
        currentFile = data.new_name;
    }
});

socket.on('file_deleted', function(data) {
    updateFileList(data.files);
    console.log(data.files)
    if (currentFile === data.name) {
        currentFile = '';
        editor.setValue('');
        updateUIState();
    }
});

socket.on('file_saved', function(data) {
    showSaveStatus();
    
    const cursorPosition = editor.getCursorPosition();
    const scrollTop = editor.getSession().getScrollTop();

    loadFile(data.filename, cursorPosition);
    
    
});

socket.on('file_content', function(data) {
    isReceivingUpdate = true;
    editor.setValue(data.content, -1);
    console.log(data.cursorpos);
    editor.moveCursorToPosition(data.cursorpos);

    editor.clearSelection();
    // editor.getSession().setScrollTop(scrollTop);
    lastSentContent = data.content;
    currentFile = data.filename;
    updateUIState();
    isReceivingUpdate = false;
});

// socket.on('user_connected', function(data) {
//     if (data.user_id !== localUserId) {
//         createCursor(data.user_id, data.color);
//     }
// });

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
        socket.emit('cursor_move', { position });
    }
});

socket.on('folder_created', (data) => {
    updateFileList({
        files: data.files || [],
        folders: data.folders || []
    });
});

socket.on('project_selected', (data) => {
    updateFileList({
        files: data.files || [],
        folders: data.folders || []
    });
});

socket.on('update_user_list', (data) => {
    const userList = document.getElementById('user-list');
    const existingUserIds = new Set();
    userList.innerHTML = '';
    switch (data.update_type) {
        case "add":
            data.users.forEach(user => {
                if (!existingUserIds.has(user.user_id)) {
                    const li = document.createElement('li');
                    console.log(user.user_id)
                    li.textContent = user.username;
                    userList.appendChild(li);
                    existingUserIds.add(user.user_id);
                }
            });
            break;
        case "disconnect":
            data.users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = user.username;
                userList.appendChild(li);
            });
            break;
    }

    if (data.user_id !== localUserId) {
            createCursor(data.user_id, data.color);
        }
});

window.addEventListener('beforeunload', () => {
    socket.emit('user_disconnected', { user_id: localUserId });
});
