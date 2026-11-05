export function pendingMessages(messages, content) {
  return [...messages, {role: 'user', content}];
}

export function completedMessages(pending, answer) {
  return [...pending, {role: 'assistant', content: answer}];
}

export function clearedMessages() {
  return [];
}

export function setChatAvailability({message, send, retry}, ready, sending) {
  const enabled = ready === true && !sending;
  message.disabled = !enabled;
  send.disabled = !enabled;
  retry.disabled = sending;
}
