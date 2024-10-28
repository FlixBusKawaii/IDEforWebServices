document.addEventListener('DOMContentLoaded', function() {
    const contextMenu = document.getElementById('contextMenu');
    const file_list = document.getElementById('file-list');

    // Désactiver le menu contextuel par défaut dans la zone spécifiée
    file_list.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        
        // Positionner le menu contextuel à l'endroit du clic
        contextMenu.style.display = 'block';
        contextMenu.style.left = e.pageX + 'px';
        contextMenu.style.top = e.pageY + 'px';
    });

    // Fermer le menu contextuel lors d'un clic ailleurs
    document.addEventListener('click', function() {
        contextMenu.style.display = 'none';
    });
});

function handleMenuClick(option) {
    console.log('Option sélectionnée:', option);
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
