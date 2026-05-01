document.addEventListener('DOMContentLoaded', () => {
  const maxHeight = 200; // Set your desired max height

  // Automatically adjust the textarea height based on content
  const promptText = document.querySelector('#promptText');
  promptText.addEventListener('input', () => {
    promptText.style.height = 'auto';
    promptText.style.height = Math.min(promptText.scrollHeight, maxHeight) + 'px';
  });
});
