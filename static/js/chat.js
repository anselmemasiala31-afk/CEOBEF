const initializeChat = () => {
  const chat = document.querySelector('[data-chat]');
  if (!chat || !('WebSocket' in window)) return;

  const list = chat.querySelector('[data-chat-messages]');
  const form = chat.querySelector('[data-chat-form]');
  const input = chat.querySelector('[data-chat-input]');
  const typing = chat.querySelector('[data-typing]');
  const presence = chat.querySelector('[data-presence]');
  let socket;
  let reconnectTimer;
  let typingTimer;

  const addMessage = (message) => {
    if (message.id && list.querySelector(`[data-message-id="${message.id}"]`)) return;
    chat.querySelector('[data-chat-empty]')?.remove();
    const row = document.createElement('li');
    row.className = `chat-message${String(message.sender_id) === document.body.dataset.userId ? ' message-own' : ''}`;
    row.dataset.messageId = message.id;
    const author = document.createElement('span');
    author.className = 'chat-message-author';
    author.textContent = message.sender;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    if (message.content) bubble.textContent = message.content;
    if (message.attachment_url) {
      const attachment = document.createElement('a');
      attachment.href = message.attachment_url;
      attachment.target = '_blank';
      attachment.rel = 'noopener';
      attachment.textContent = 'Pièce jointe ↗';
      bubble.append(attachment);
    }
    const time = document.createElement('time');
    time.textContent = new Date(message.created_at).toLocaleTimeString('fr-CD', { hour: '2-digit', minute: '2-digit' });
    row.append(author, bubble, time);
    list.append(row);
    list.scrollTop = list.scrollHeight;
  };

  const connect = () => {
    socket = new WebSocket(chat.dataset.websocketUrl);
    socket.addEventListener('open', () => {
      presence.textContent = 'En ligne';
      socket.send(JSON.stringify({ action: 'read' }));
    });
    socket.addEventListener('message', (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === 'history') payload.messages.forEach(addMessage);
      if (payload.type === 'message') addMessage(payload);
      if (payload.type === 'typing') typing.textContent = payload.active ? `${payload.name} écrit…` : '';
      if (payload.type === 'presence') presence.textContent = 'En ligne';
    });
    socket.addEventListener('close', () => {
      presence.textContent = 'Reconnexion…';
      reconnectTimer = window.setTimeout(connect, 1800);
    });
  };

  connect();
  window.setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ action: 'heartbeat' }));
  }, 30000);

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const content = input.value.trim();
    if (!content || socket?.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ action: 'message', content }));
    input.value = '';
    input.style.height = 'auto';
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ action: 'typing', active: true }));
    window.clearTimeout(typingTimer);
    typingTimer = window.setTimeout(() => {
      if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ action: 'typing', active: false }));
    }, 900);
  });

  window.addEventListener('pagehide', () => {
    window.clearTimeout(reconnectTimer);
    socket?.close();
  });
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeChat, { once: true });
} else {
  initializeChat();
}
