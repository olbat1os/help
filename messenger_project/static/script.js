const chatList = document.getElementById('chat-list');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const messagesContainer = document.getElementById('messages');
const chatHeader = document.getElementById('chat-header');
const userList = document.getElementById('user-list');

let selectedChatId = null;
let socket = null;

const fetchChats = async () => {
    const response = await fetch('/api/chats/');
    const data = await response.json();
    chatList.innerHTML = '';
    data.forEach(chat => {
        const listItem = document.createElement('li');
        listItem.textContent = chat.name || `Chat ${chat.id}`;
        listItem.addEventListener('click', () => {
            console.log('Chat click, chat id:', chat.id)
             loadChat(chat.id)
          });
        chatList.appendChild(listItem);
    });
};

const loadChat = async (chatId) => {
    console.log('Load chat, chat id:', chatId);
    selectedChatId = chatId;
    chatHeader.textContent = `Chat #${chatId}`;
    messagesContainer.innerHTML = '';

    if(socket) {
        socket.close()
    }

    const response = await fetch(`/api/chats/${chatId}/messages/`);
    const data = await response.json();

    data.forEach(message => {
        const messageElement = document.createElement('div');
        messageElement.textContent = `${message.sender.username}: ${message.text}`;
        messageElement.classList.add('message');
        messagesContainer.appendChild(messageElement);
    });

    startWebsocketConnection(chatId)
};
const startWebsocketConnection = (chatId) => {
        console.log('startWebsocketConnection, chat id:', chatId)
        socket = new WebSocket(`ws://127.0.0.1:8000/ws/chat/${chatId}/`);

        socket.onopen = (event) => {
          console.log('WebSocket connection opened:', event);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if(data.error){
              console.error('WebSocket error:', data.error);
              return;
            }
            const message = data.message;
            const messageElement = document.createElement('div');
            messageElement.textContent = `${message.sender.username}: ${message.text}`;
            messageElement.classList.add('message');
            messagesContainer.appendChild(messageElement);
        };

        socket.onclose = (event) => {
          console.log('WebSocket connection closed:', event);
          console.log('WebSocket close code:', event.code)
        };

        socket.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
};


sendButton.addEventListener('click', async () => {
    if(!selectedChatId || !messageInput.value){
        return
    }
    const message = messageInput.value;

    try {
            socket.send(JSON.stringify({ message: message }));
            messageInput.value = '';
    } catch(error) {
        console.error("Error send message:", error)
    }

});

const fetchUsers = async () => {
    const response = await fetch('/api/users/');
    const data = await response.json();
    userList.innerHTML = '';
    data.forEach(user => {
        const listItem = document.createElement('li');
        listItem.textContent = user.username;
         listItem.addEventListener('click', () => startPersonalChat(user.id));
        userList.appendChild(listItem);
    });
};

const startPersonalChat = async (userId) => {
  try {
    const response = await fetch('/api/chats/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
      },
        body: JSON.stringify({ participants: [userId], is_group: false })
    });

    if (response.ok) {
      const data = await response.json();
      loadChat(data.id)
    } else {
        const errorData = await response.json();
        console.error('Failed to create a personal chat:', errorData);
    }
  } catch (error) {
      console.error("Failed to create a personal chat:", error)
  }
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.startsWith(name + '=')) {
        cookieValue = cookie.substring(name.length + 1);
        break;
      }
    }
  }
  return cookieValue;
}

fetchChats();
fetchUsers()
