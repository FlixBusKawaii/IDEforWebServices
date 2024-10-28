// set the editor
const editor = ace.edit("editor");
editor.setTheme("ace/theme/clouds");
//editor.session.setMode("ace/mode/python");

let currentFile = '';
let currentProject = '';
let isReceivingUpdate = false;
let localUserId = null;
let saveTimeout = null;
let lastSentContent = '';
const cursors = {};

// Initialisation des boutons
const createFileBtn = document.getElementById('create-file-btn');
const renameFileBtn = document.getElementById('rename-file-btn');
const deleteFileBtn = document.getElementById('delete-file-btn');
const executeBtn = document.getElementById('execute-btn');
const themeToggleButton = document.getElementById('themeToggle');
const icon = themeToggleButton.querySelector('.icon');


editor.setReadOnly(true);

function createFolder(){
    const filename = document.getElementById('filename').value.trim();

    if (!filename) {
        alert('Please enter a foldername');
        return;
    }

    if (!currentProject) {
        alert('Please select a project first');
        return;
    }

    console.log('Creating folder:', {name: filename, project: currentProject});

    socket.emit('create_folder', {
        name: filename,
        project: currentProject
    });

}
function createProject() {
    const projectName = document.getElementById('project-name').value;
    if (projectName) {
        console.log('Creating project:', projectName);
        socket.emit('create_project', {name: projectName});
        document.getElementById('project-name').value = '';
    }
}

function deleteProject() {
    if (currentProject && confirm(`Êtes-vous sûr de vouloir supprimer le projet "${currentProject}" ?`)) {
        console.log('Deleting project:', currentProject);
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

    console.log('Creating file:', {name: filename, project: currentProject});

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
            console.log('Renaming file:', {old_name: currentFile, new_name: newName, project: currentProject});
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
        console.log('Deleting file:', {name: currentFile, project: currentProject});
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

    console.log('Executing code:', {project: currentProject, filename: currentFile, code: editor.getValue()});
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


function updateFileList(files) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    files.forEach(file => {
        const li = document.createElement('li');
        const fileSpan = document.createElement('span');
        fileSpan.textContent = file;
        li.appendChild(fileSpan);
        li.onclick = () => loadFile(file);
        fileList.appendChild(li);
    });
}

function selectProject() {
    const projectSelect = document.getElementById('project-select');
    currentProject = projectSelect.value;
    currentFile = '';
    editor.setValue('');

    
    // Mise à jour de l'affichage des sections fichiers
    const fileActions = document.getElementById('file-actions');
    const projectInfo = document.getElementById('project-info');
    const currentProjectName = document.getElementById('current-project-name');
    
    if (currentProject) {
        fileActions.classList.add('visible');
        projectInfo.classList.add('visible');
        currentProjectName.textContent = currentProject;
        console.log('Selecting project:', currentProject);
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
    console.log("Mode:", "ace/mode/" + editorSyntax);

}

function toggleTheme() {
    // Basculer uniquement la classe dark-theme
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

function loadFile(filename) {
    if (!currentProject) return;
    
    const fileListItems = document.querySelectorAll('#file-list li');
    fileListItems.forEach(item => {
        item.classList.remove('selected');
    });

    const clickedFileItem = Array.from(fileListItems).find(item => item.textContent.trim() === filename);
    if (clickedFileItem) {
        clickedFileItem.classList.add('selected');
    }

    console.log('Loading file:', { filename: filename, project: currentProject });
    socket.emit('load_file', { filename: filename, project: currentProject });
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

    console.log('UI State updated:', {
        projectSelected,
        fileSelected,
        createFileBtnDisabled: createFileBtn.disabled,
        renameFileBtnDisabled: renameFileBtn.disabled,
        deleteFileBtnDisabled: deleteFileBtn.disabled,
        executeBtnDisabled: executeBtn.disabled,
        editorReadOnly: editor.getReadOnly()
    });
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
