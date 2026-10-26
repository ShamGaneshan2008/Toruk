export function pendingMessages(messages, content) {
  return [...messages, {role: 'user', content}].slice(-19);
}

export function completedMessages(pending, answer) {
  return [...pending, {role: 'assistant', content: answer}];
}

export function clearedMessages() {
  return [];
}
