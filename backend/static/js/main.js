
editor.setTheme("ace/theme/clouds");

let currentFile = '';
let currentProject = '';
let currentFolder ='';
let currentMode = 'colab';
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
    let resultPrompt = null;
    if (isExerciseMode()) {
        return;
    }
    if (option === 'create_file' || option === 'rename_file' || option === 'create_folder') {
        resultPrompt = prompt("Enter a name:");
        if (!resultPrompt) {
            alert("Name is required");
            return; 
        }
    }
    
    switch (option){
        case 'create_file':
            createFile(resultPrompt);    
            break;
        case 'rename_file':
            renameFile();
            break;
        case 'delete_file':
            deleteFile();
            break;
        case 'create_folder':
            createFolder(resultPrompt);
            break;
        case 'delete_folder':
            deleteFolder();
            break;

    }
}
function isExerciseMode() {
    return document.body.getAttribute('data-mode') === 'exercise';
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

function createFolder(name) {
    const foldername = name ||document.getElementById('filename').value.trim();

    if (!foldername) {
        alert('Please enter a foldername');
        return;
    }

    if (!currentProject) {
        alert('Please select a project first');
        return;
    }

    socket.emit('create_folder', {
        name: foldername,
        project: currentProject
    });
}
function deleteFolder() {
    if (currentFolder && currentProject && confirm(`Êtes-vous sûr de vouloir supprimer le dossier "${currentFolder}" ?`)) {
        socket.emit('delete_folder', {name: currentFolder, project: currentProject});
        currentFolder = '';
        editor.setValue('');
        updateUIState();
    }
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

function createFile(file_name) {
    const filename = file_name || document.getElementById('filename').value.trim();
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
    fileList.innerHTML = ''; // Vider la liste existante

    if (!data || data.length === 0) {
        console.warn('Aucune donnée à afficher');
        return;
    }

    const cursorPosition = editor.getCursorPosition();

    for (let i = 0; i < data.length; i++) {
        const item = data[i];

        if (item.name === '.' || item.name === '..') continue;

        const li = document.createElement('li');
        const itemSpan = document.createElement('span');

        // Déterminez le type d'élément
        if (item.type === 'directory') {
            itemSpan.innerHTML = `📁 ${item.name || 'Sans nom'}`;
            itemSpan.classList.add('folder');
            li.onclick = () => {
                loadFolder(item.name);
            };
        } else {
            itemSpan.innerHTML = `📄 ${item.name || 'Sans nom'}`;
            itemSpan.classList.add('file');

            // Ajoutez un événement onclick
            li.onclick = () => {
                loadFile(item.name, cursorPosition);
            };
        }

        li.appendChild(itemSpan);
        fileList.appendChild(li);
    }

    // Vérifiez le nombre d'enfants après l'ajout
}

function loadFolder(foldername){
    const fileListItems = document.querySelectorAll('#file-list li');
    fileListItems.forEach(item => {
        item.classList.remove('selected');
    });
    const clickedFolderItem = Array.from(fileListItems).find(item => {
        const itemText = item.textContent.trim().replace("📁 ", ""); // Retire l'emoji
        return itemText === foldername;
    });

    if (clickedFolderItem) {
        clickedFolderItem.classList.add('selected');
    } else {
        console.warn("File item not found for filename:", filename);
    }
    socket.emit('load_folder', { foldername: foldername});
    currentFolder = foldername
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
    editor.setOptions({
        enableBasicAutocompletion: true,   
        enableSnippets: true,              
        enableLiveAutocompletion: true     
    });
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

function loadFile(filename, cursorPos) {
    if (!currentProject) return;
    clearCursors();

    const fileListItems = document.querySelectorAll('#file-list li');
    fileListItems.forEach(item => {
        item.classList.remove('selected');
    });

    const clickedFileItem = Array.from(fileListItems).find(item => {
        const itemText = item.textContent.trim().replace("📄 ", ""); // Retire l'emoji
        return itemText === filename;
    });

    if (clickedFileItem) {
        clickedFileItem.classList.add('selected');
    } else {
        console.warn("File item not found for filename:", filename);
    }

    socket.emit('load_file', { filename: filename, project: currentProject, cursorpos: cursorPos });
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
    // executeBtn.disabled = !projectSelected || !fileSelected;
    editor.setReadOnly(!projectSelected || !fileSelected);
}

function createCursor(userId, color) {
    if (cursors[userId]) {
        return;
    }

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
    if (!cursors[userId]) {
        console.warn(`Cursor not found for user ${userId}`);
        return;
    }
    
    // Convertir la position du texte en position à l'écran
    const pixelPosition = editor.renderer.textToScreenCoordinates(position.row, position.column);
    
    // Ajuster la position en tenant compte du scroll et de la position de l'éditeur
    const editorRect = editor.container.getBoundingClientRect();
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    const cursor = cursors[userId].cursor;
    const label = cursors[userId].label;
    
    // Mettre à jour les positions
    cursor.style.transform = 'translate(-50%, 0)';
    cursor.style.left = `${pixelPosition.pageX + scrollLeft - editorRect.left}px`;
    cursor.style.top = `${pixelPosition.pageY + scrollTop - editorRect.top}px`;
    
    label.style.transform = 'translate(-50%, -100%)';
    label.style.left = `${pixelPosition.pageX + scrollLeft - editorRect.left}px`;
    label.style.top = `${pixelPosition.pageY + scrollTop - editorRect.top - 5}px`;
}


const username = localStorage.getItem('username');
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
    const userCookie = getUserCookie();
    if (userCookie) {
        socket.emit('user_connected', { user_id: userCookie.user_id, username: userCookie.username });
    } else {
        if (username) {
            const userId = socket.id;
            setUserCookie(username, userId);
            socket.emit('user_connected', { user_id: userId, username: username });
        }
    }
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
    // Si nous sommes en mode exercice, ne rien faire
    if (isExerciseMode()) {
        return;
    }

    const projectSelect = document.getElementById('project-select');
    if (!projectSelect) return;

    projectSelect.innerHTML = '<option value="">Sélectionner un projet</option>';
    data.projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project;
        option.textContent = project;
        projectSelect.appendChild(option);
    });
});

socket.on('project_selected', function(data) {
    
    updateFileList(data.files);
});

socket.on('file_created', function(data) {
    updateFileList(data.files);
});
socket.on('folder_created', function(data){
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
    if (currentFile === data.name) {
        currentFile = '';
        editor.setValue('');
        updateUIState();
    }
});
socket.on('folder_deleted', function(data) {
    updateFileList(data.files);
    if (currentFolder === data.name) {
        currentFolder = '';
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

function clearCursors() {
    // Parcourir tous les curseurs stockés
    for (const userId in cursors) {
        if (cursors.hasOwnProperty(userId)) {
            // Supprimer les éléments DOM du curseur et du label
            if (cursors[userId].cursor) {
                cursors[userId].cursor.remove();
            }
            if (cursors[userId].label) {
                cursors[userId].label.remove();
            }
            // Supprimer la référence dans l'objet cursors
            delete cursors[userId];
        }
    }
    // Au lieu de réassigner cursors, on le vide
    Object.keys(cursors).forEach(key => delete cursors[key]);
}

socket.on('cursor_update', function(data) {
    console.log(data.user_id);
    console.log(data.position);

    if (data.user_id !== localUserId && currentFile == data.currentFile) {
        createCursor(data.user_id, '#333');
        updateCursorPosition(data.user_id, data.position);
    }
    
});


editor.session.selection.on('changeCursor', () => {
    if (currentProject && currentFile) {
        const position = editor.selection.getCursor();
        
        socket.emit('cursor_move', { pos : position ,user_id: localUserId ,currentFile : currentFile});
        //console.log("ca bouge")
    }
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
                    li.textContent = user.username;    
                    if(user.user_id == localUserId){
                        li.classList.add("current-user")
                    }
                    console.log(userList);
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

    
});

window.addEventListener('beforeunload', () => {
    socket.emit('user_disconnected', { user_id: localUserId });
});

// socket.on('exercises_list', (exercises) => {
//     updateExercisesList(exercises);
// });

// socket.on('exercise_data', (exercise) => {
//     loadExerciseIntoEditor(exercise);
// });

// socket.on('submission_result', (result) => {
//     displaySubmissionResult(result);
// });

// socket.on('error', (error) => {
//     console.error('Server error:', error.message);
// });

// // function updateExercisesList(exercises) {
// //     const exerciseList = document.getElementById('exercise-list');
// //     exerciseList.innerHTML = '';
    
// //     exercises.forEach(exercise => {
// //         const li = document.createElement('li');
// //         li.className = 'exercise-item';
// //         li.innerHTML = `
// //             <h3>${exercise.name}</h3>
// //             <p>${exercise.description}</p>
// //             <button onclick="loadExercise('${exercise.id}')">Commencer</button>
// //         `;
// //         exerciseList.appendChild(li);
// //     });
// // }

// // function loadExercise(exerciseId) {
// //     socket.emit('get_exercise', { exercise_id: exerciseId });
// // }

// // function loadExerciseIntoEditor(exercise) {
// //     editor.setValue(exercise.template);
    
// //     document.getElementById('exercise-description').innerHTML = `<h2>${exercise.name}</h2><p>${exercise.description}</p>`;
    
// //     // Activer le bouton de soumission
// //     document.getElementById('submit-exercise').disabled = false;
// // }

// // function submitExercise() {
// //     const code = editor.getValue();
// //     const exerciseId = currentExercise.id; 
// //     socket.emit('submit_exercise', {
// //         exercise_id: exerciseId,
// //         code: code
// //     });
// // }

// function displaySubmissionResult(result) {
//     const resultDiv = document.getElementById('submission-result');
//     resultDiv.innerHTML = `
//         <div class="result ${result.status}">
//             ${result.message}
//         </div>
//     `;
// }

// // Initialiser la liste des exercices au chargement
// document.addEventListener('DOMContentLoaded', () => {
//     socket.emit('get_exercises');
// });