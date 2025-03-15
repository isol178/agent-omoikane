document.addEventListener('DOMContentLoaded', function() {
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const messages = document.getElementById('messages');
    let conversationHistory = [];

    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && event.metaKey) { // Command + Enter
            event.preventDefault();
            sendMessage();
        }
    });

    function sendMessage() {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addMessage('User', userMessage);
            conversationHistory.push({ role: 'user', content: userMessage });
            userInput.value = '';
            simulateAIResponse();
        }
    }

    function addMessage(sender, text) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
        messages.appendChild(messageElement);
        messages.scrollTop = messages.scrollHeight;
    }

    async function fetchAIResponse() {
        // Ensure a system prompt is present for context if history is empty
        if (conversationHistory.length === 0 || (conversationHistory.length === 1 && conversationHistory[0].role !== 'system')) {
            conversationHistory.unshift({ role: 'system', content: "You are a helpful assistant." });
        }
        const apiKey = process.env.OPEN_AI_API_KEY; // Loaded from .env file
        const apiUrl = 'https://api.openai.com/v1/chat/completions';

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'gpt-4o-mini',
                    messages: conversationHistory,
                    max_tokens: 150,
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Error: ${errorData.error.message}`);
            }

            const data = await response.json();
            const aiResponse = data.choices[0].message.content.trim();
            addMessage('AI', aiResponse);
            conversationHistory.push({ role: 'assistant', content: aiResponse });
        } catch (error) {
            console.error('Error fetching AI response:', error);
            addMessage('AI', 'Sorry, there was an error processing your request.');
        }
    }

    function simulateAIResponse() {
        fetchAIResponse();
    }
});
