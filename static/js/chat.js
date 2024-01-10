// const room_id = "{{room.id}}";
const room_id = $("#room-data").data("room-id");
const socket = io.connect();
let lastMessageId = 0;
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let timer;
socket.on('connect', () => {
    socket.emit('join_room', {
        room: room_id
    });
});
socket.on('join_room_announcement', function (data) {
    console.log(data);
});

socket.on('leave_room_announcement', function (data) {
    console.log(data);
});

window.onbeforeunload = function () {
    socket.emit('leave_room', {
        room: room_id
    });
};

// Send a message

// Send a message when Enter key is pressed
const input = document.querySelector('#message-input');
input.addEventListener('keyup', function (event) {
    if (event.key === 'Enter' && input.value.trim() !== '') {
        document.querySelector('#send-button').click();
    }
});

document.querySelector('#send-button').onclick = function () {
    const input = document.querySelector('#message-input');
    const content = input.value;
    if (content) {
        console.log('Sending message:', content); // Debug message
        socket.emit('send_message', { room_id: room_id, content: content });
        input.value = '';
    }
};

// Handle file attachment
document.querySelector('#file-button').addEventListener('click', function () {
    document.querySelector('#file-input').click();
});

document.querySelector('#file-input').addEventListener('change', function () {
    const selectedFiles = this.files;
    const totalSize = Array.from(selectedFiles).reduce((acc, file) => acc + file.size, 0);
    const fileLimitMessage = document.querySelector('#file-limit-message');

    if (selectedFiles.length > 8) {
        fileLimitMessage.textContent = 'You can select a maximum of 8 files.';
        return;
    } else if (totalSize > 32 * 1024 * 1024) {
        fileLimitMessage.textContent = 'Total file size should be less than 32 MB.';
        return;
    } else {
        fileLimitMessage.textContent = '';
    }

    // Process selected files as before
    const fileContents = [];
    const fileExtensions = [];
    for (const file of selectedFiles) {
        const reader = new FileReader();
        reader.onload = function (event) {
            const fileContent = new Uint8Array(event.target.result);
            const fileExtension = file.name.split('.').pop();
            fileContents.push(fileContent);
            fileExtensions.push(fileExtension);
            if (fileContents.length === selectedFiles.length) {
                // All files have been read, emit them to the server
                socket.emit('send_file', { room_id: room_id, file_contents: fileContents, file_extensions: fileExtensions });
            }
        };
        reader.readAsArrayBuffer(file);
    }
});
function play_notification(){
    //const audio_url = "{{ url_for('static', filename='audio/notification.mp3') }}";
    const audio_url = "/static/audio/notification.mp3";
    const audio = new Audio(audio_url);
    audio.play();

}
// Handle file error messages
socket.on('file_error', function (data) {
    const fileLimitMessage = document.querySelector('#file-limit-message');
    fileLimitMessage.textContent = data.message;
});

function showTooltip() {
    const tooltip = document.getElementById('attachment-tooltip');
    tooltip.style.display = 'block';
}

function hideTooltip() {
    const tooltip = document.getElementById('attachment-tooltip');
    tooltip.style.display = 'none';
}

socket.on('receive_message', function (data) {
    console.log(data)
    console.log('This is content: ', data.content);
    // Display the received message in the chat container
    const messageContainer = document.querySelector('.chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-card';
    const profile_tag = document.createElement('img');
    
    profile_tag.src = data.profile_pic;
    profile_tag.style.width = '30px';
    profile_tag.style.height = '30px';
    profile_tag.style.borderRadius = '50%';
    profile_tag.style.objectFit = 'cover';
    profile_tag.addEventListener('click', function () {
        // Display the modal with the clicked profile picture
        const profileModalImg = document.getElementById('profileModalImg');
        profileModalImg.src = profile_tag.src;
        document.getElementById('profileModal').style.display = 'block';
    });

    if (data.file_path) {
        // Display the file link if it's a file message
        // if image use img src
        const senderName = document.createElement('span');

        
        senderName.textContent = data.username + ': ';
        console.log(senderName);
        const ext =  data.content.split('.').pop();
        console.log('[*]Sender function extension: '+ext)
        if(ext === 'jpg' || ext === 'png' || ext === 'jpeg' || ext === 'bmp'){
            console.log('[*]I got called');
            const im_tag = document.createElement('img');
            im_tag.src = data.file_path;
            im_tag.style.maxWidth = '300px';
            im_tag.style.maxHeight = '300px';
            messageDiv.appendChild(profile_tag);
            messageDiv.appendChild(senderName);
            messageDiv.appendChild(document.createElement('br'));
            messageDiv.appendChild(im_tag);


        }else if(ext === 'mp4' || ext === 'webm' || ext === 'ogg'){
            const video_tag = document.createElement('video');
            video_tag.src = data.file_path;
            video_tag.controls = true;
            video_tag.width = 400;
            video_tag.height = 300;
            messageDiv.appendChild(profile_tag);
            messageDiv.appendChild(senderName);
            messageDiv.appendChild(document.createElement('br'));
            messageDiv.appendChild(video_tag);



        }else if(ext === 'mp3' || ext === 'wav' || ext === 'flac'){
            const audio_tag = document.createElement('audio');
            audio_tag.src = data.file_path;
            audio_tag.controls = true;
            messageDiv.appendChild(profile_tag);
            messageDiv.appendChild(senderName);
            messageDiv.appendChild(document.createElement('br'));
            messageDiv.appendChild(audio_tag);

        }else{

            const fileLink = document.createElement('a');
            fileLink.href = data.file_path;
            fileLink.target = '_blank';
            fileLink.textContent = data.content;
            
            messageDiv.appendChild(profile_tag);
            messageDiv.appendChild(senderName);
            messageDiv.appendChild(document.createElement('br'));
            messageDiv.appendChild(fileLink);
        }
    } else {
        // Display the text message
        
        const m_tag = document.createElement('span');
        m_tag.textContent = data.username + ': ' + data.content;
        messageDiv.appendChild(profile_tag);
        messageDiv.appendChild(m_tag);
    }
    messageContainer.appendChild(messageDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight; // Scroll to the bottom
    play_notification();
});


//audio message stuff
const voiceRecordButton = document.getElementById('voice-recorder');
voiceRecordButton.addEventListener('mousedown', startRecording);
voiceRecordButton.addEventListener('mouseup', stopRecording);
voiceRecordButton.addEventListener('touchstart', startRecording);
voiceRecordButton.addEventListener('touchend', stopRecording);

function startRecording() {
if (!isRecording) {
    try {
        console.log("[*]Audio recording started");
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    //socket.emit('send_voice_message', { room_id: room_id, audioBlob: audioBlob });
                    sendaudio(audioBlob);
                    audioChunks = [];
                };
                mediaRecorder.start();
                isRecording = true;
                voiceRecordButton.textContent = 'Recording...';
            })
            .catch(function(error) {
                console.error('Error accessing the microphone:', error);
            });
    } catch (error) {
        console.error('Error accessing the microphone:', error);
    }
}
}

function stopRecording() {
if (isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    voiceRecordButton.innerHTML = "<img src='/static/images/voice.png' alt='Voice Message'>";
    
}
}

function sendaudio(audioBlob){

    console.log("[*]Audio sender started.....");
    const audio_reader = new FileReader();
    audio_reader.onload = function(event){
        const audiobuffer = event.target.result;
        const audiodata = new Uint8Array(audiobuffer);
        socket.emit('send_voice_message', { room_id: room_id, voice_data:audiodata});
    };
    audio_reader.readAsArrayBuffer(audioBlob);
}
socket.on('receive_voice_message',function(data){
    console.log('[*]receiver is called');
    console.log(data.file_path);
    const profile_tag = document.createElement('img');
    
    profile_tag.src = data.profile_pic;
    profile_tag.style.width = '30px';
    profile_tag.style.height = '30px';
    profile_tag.style.borderRadius = '50%';
    profile_tag.style.objectFit = 'cover';
    profile_tag.addEventListener('click', function () {
        // Display the modal with the clicked profile picture
        const profileModalImg = document.getElementById('profileModalImg');
        profileModalImg.src = profile_tag.src;
        document.getElementById('profileModal').style.display = 'block';
    });

    const messageContainer = document.querySelector('.chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-card';
    const senderName = document.createElement('span');
    senderName.textContent = data.username + ': ';
    const audio_tag = document.createElement('audio');
    audio_tag.src = data.file_path;
    audio_tag.controls = true;
    messageDiv.appendChild(profile_tag)
    messageDiv.appendChild(senderName);
    messageDiv.appendChild(document.createElement('br'));
    messageDiv.appendChild(audio_tag);
    messageContainer.appendChild(messageDiv);
    play_notification();


});
// JavaScript code to fetch and display the list of users
document.querySelector('#offcanvasScrolling').addEventListener('show.bs.offcanvas', function () {
    fetch('/active_users/'+room_id) 
        .then(response => response.json())
        .then(data => {
            console.log(data)
            const usersList = document.querySelector('#usersList');
            usersList.innerHTML = '';  // Clear any existing content

            if (data.length > 0) {
                const userListContainer = document.createElement('ul');
                userListContainer.className = 'list-group';

                data.forEach(user => {
                    const userItem = document.createElement('li');
                    userItem.className = 'list-group-item';
                    userItem.textContent = user.username;

                    userListContainer.appendChild(userItem);
                });

                usersList.appendChild(userListContainer);
            } else {
                usersList.textContent = 'No active users in this chatroom.';
            }
        })
        .catch(error => {
            console.error('Error fetching user data:', error);
        });
});

// Add an event listener for clicks on profile pictures
document.addEventListener('click', function (event) {
    const target = event.target;

    // Check if the clicked element is a profile picture
    if (target.tagName === 'IMG' && target.classList.contains('profile-pic')) {
        // Display the modal with the clicked profile picture
        const profileModalImg = document.getElementById('profileModalImg');
        profileModalImg.src = target.src;
        document.getElementById('profileModal').style.display = 'block';
    }
});

// Function to close the profile modal
function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
}

// Close the modal if the user clicks outside of it
window.addEventListener('click', function (event) {
    if (event.target === document.getElementById('profileModal')) {
        closeProfileModal();
    }
});

