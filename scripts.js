const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const historyButton = document.getElementById('history-button');
const historyPanel = document.getElementById('history-panel');
const textInput = document.getElementById('text-input');
const sendButton = document.getElementById('send-button');

let socket;
let lastAudioFilename = '';
let lastMappingFilename = '';
let isPlaying = false;
let isLoading = false; 
let currentAvatar = 'Female';  // Avatar por defecto

document.getElementById('avatar-selection').addEventListener('change', (event) => {
    currentAvatar = event.target.value; // 'female' o 'male'
    console.log(`Avatar seleccionado: ${currentAvatar}`);
    // Cambiar el avatar a la imagen por defecto según la selección
    changeAvatarFrame(`public/frames/${currentAvatar}/X.jpg`);
});

function connectWebSocket() {
    socket = new WebSocket('ws://localhost:8032');

    socket.onopen = function(e) {
        console.log("WebSocket connection established");
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.audioUrl && data.mappingUrl) {
            if (data.audioUrl !== lastAudioFilename || data.mappingUrl !== lastMappingFilename) {
                lastAudioFilename = data.audioUrl;
                lastMappingFilename = data.mappingUrl;
                fetchMappingAndPlay(data.audioUrl, data.mappingUrl);
            }
        }
    };

    socket.onclose = function(event) {
        console.log('WebSocket connection closed. Reconnecting...');
        setTimeout(connectWebSocket, 1000);
    };

    socket.onerror = function(error) {
        console.error(`WebSocket Error: ${error.message}`);
    };
}

connectWebSocket();

async function getTranscriptionFiles() {
    try {
        console.log("Solicitando archivos de transcripción al servidor...");
        const response = await fetch('/get_transcription_files');
        const files = await response.json();
        console.log("Archivos de transcripción recibidos:", files);
        return files;
    } catch (error) {
        console.error('Error al obtener la lista de archivos de transcripción:', error);
        return [];
    }
}

async function playLoadingMessage() {
    if (isLoading) return;
    isLoading = true;

    console.log("Iniciando playLoadingMessage");

    // Obtener el último archivo de transcripción
    const transcriptionFiles = await getTranscriptionFiles();
    console.log("Archivos de transcripción:", transcriptionFiles);

    if (transcriptionFiles.length === 0) {
        console.error("No se encontraron archivos de transcripción");
        isLoading = false;
        return;
    }

    const latestTranscription = transcriptionFiles[0]; // El primer archivo es el más reciente
    console.log("Última transcripción:", latestTranscription);

    // Leer el contenido del archivo de transcripción
    let inputText = '';
    try {
        const response = await fetch(`Public/transcriptions/${latestTranscription}`);
        inputText = await response.text();
        console.log("Contenido de la transcripción:", inputText);
    } catch (error) {
        console.error('Error al leer el archivo de transcripción:', error);
        isLoading = false;
        return;
    }

    // Determinar qué mensaje de espera usar basado en el texto de entrada
    let waitIndex;
    if (inputText.includes('?')) {
        waitIndex = 4;
        console.log("Se detectó una pregunta");
    } else if (inputText.toLowerCase().includes('realiza')) {
        waitIndex = 5;
        console.log("Se detectó una solicitud de realización");
    } else if (inputText.toLowerCase().includes('busca')) {
        waitIndex = 6;
        console.log("Se detectó una solicitud de búsqueda");
    } else {
        // Si no se encuentra ninguna palabra clave, seleccionar aleatoriamente entre los mensajes generales
        waitIndex = Math.floor(Math.random() * 3) + 1;
        console.log("No se detectaron palabras clave, seleccionando mensaje aleatorio:", waitIndex);
    }

    console.log("Índice de espera seleccionado:", waitIndex);

    const audioElement = document.getElementById('audio');
    audioElement.src = `Public/Wait/Wait${waitIndex}.wav`;

    try { 
        const response = await fetch(`Public/Wait/Wait${waitIndex}.json`);
        const mappingData = await response.json();
    
        if (mappingData && Array.isArray(mappingData.mouthCues)) {
            audioElement.onplay = () => {
                mappingData.mouthCues.forEach(cue => {
                    if (cue && cue.value && cue.start != null) {
                        setTimeout(() => {
                            const frame = `public/frames/${currentAvatar}/${cue.value}.jpg`;
                            document.getElementById('avatar').src = frame;
                        }, cue.start * 1000);
                    }
                });
            };
    
            audioElement.play();
            audioElement.onended = () => {
                document.getElementById('avatar').src = `public/frames/${currentAvatar}/X.jpg`;
                isLoading = false;
            };
        }
    } catch (error) {
        console.error('Error al cargar el mensaje de carga:', error);
        isLoading = false;
    }
    
}

async function getTranscriptionFiles() {
    try {
        const response = await fetch('/get_transcription_files');
        const files = await response.json();
        return files;
    } catch (error) {
        console.error('Error al obtener la lista de archivos de transcripción:', error);
        return [];
    }
}

async function sendTextToBackend(text) {
    try {
        const buttonSpinner = document.getElementById('button-spinner');
        if (buttonSpinner) {
            buttonSpinner.classList.remove('hidden');
        }
        
        // Reproducir el mensaje de carga aleatorio
        playLoadingMessage();
        
        const response = await fetch('/generate_audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text }),
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Audio generado:', result.message);
            // Detener el mensaje de carga y reproducir la respuesta real
            isLoading = false;
            fetchMappingAndPlay(result.audioUrl, result.mappingUrl);
        } else {
            console.error('Error al generar audio:', result.error);
            isLoading = false;
        }

        if (buttonSpinner) {
            buttonSpinner.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error al enviar texto al backend:', error);
        const buttonSpinner = document.getElementById('button-spinner');
        if (buttonSpinner) {
            buttonSpinner.classList.add('hidden');
        }
        isLoading = false;
    }
}

document.getElementById('send-button').addEventListener('click', () => {
    const text = document.getElementById('text-input').value.trim();
    if (text) {
        sendTextToBackend(text);
        document.getElementById('text-input').value = '';
    }
});

sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('retracted');
    mainContent.classList.toggle('expanded');
});

historyButton.addEventListener('click', () => {
    historyPanel.classList.toggle('open');
});

document.addEventListener('click', (event) => {
    if (!historyPanel.contains(event.target) && event.target !== historyButton) {
        historyPanel.classList.remove('open');
    }
});

async function loadTranscription(filename) {
    try {
        const response = await fetch(`Public/transcriptions/${filename}`);
        return await response.text();
    } catch (error) {
        console.error('Error al cargar la transcripción:', error);
        return '';
    }
}

async function changeAvatarFrame(frameUrl) {
    const avatar = document.getElementById('avatar');
    avatar.src = frameUrl;
}

async function fetchMappingAndPlay(audioFilename, mappingFilename) {
    if (isPlaying) return; // Evita la ejecución si ya está reproduciendo
    isPlaying = true;

    try {
        const audioElement = document.getElementById('audio');
        audioElement.src = audioFilename;

        const response = await fetch(mappingFilename);
        const mappingData = await response.json();

        if (mappingData && Array.isArray(mappingData.mouthCues)) {
            audioElement.onplay = () => {
                mappingData.mouthCues.forEach(cue => {
                    if (cue && cue.value && cue.start != null) {
                        setTimeout(() => {
                            const frame = `public/frames/${currentAvatar}/${cue.value}.jpg`;
                            changeAvatarFrame(frame);
                        }, cue.start * 1000);
                    } else {
                        console.error('Datos de cue inválidos:', cue);
                    }
                });
            };

            audioElement.play();
            audioElement.onended = () => {
                changeAvatarFrame(`public/frames/${currentAvatar}/X.jpg`); // Regresar a fotograma por defecto
                isPlaying = false; // Restablecer estado de reproducción
            };

        } else {
            console.error('Datos de mapeo inválidos o mal formateados:', mappingData);
            isPlaying = false;
        }
    } catch (error) {
        console.error('Error al cargar el mapeo o reproducir el audio:', error);
        isPlaying = false;
    }
}


function playText(text, duration) {
    const speechTextElement = document.getElementById('speech-text');
    const words = text.split(' ');
    const wordsPerSecond = words.length / duration;
    let currentWord = 0;

    function updateText() {
        if (currentWord < words.length) {
            speechTextElement.textContent += words[currentWord] + ' ';
            currentWord++;
            setTimeout(updateText, 1000 / wordsPerSecond);
        }
    }

    speechTextElement.textContent = '';
    updateText();
}

document.getElementById('interact-button').addEventListener('click', () => {
    document.getElementById('interact-button').style.display = 'none';
});

