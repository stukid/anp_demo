// Import utility functions
// Use getBasePath() to get the API base path
const BASE_PATH = getBasePath();

// Define API request function
async function submitQuestion() {
    const question = document.getElementById('question').value;
    const agentUrl = document.getElementById('agentUrl').value || 'https://agent-search.ai/ad.json';
    
    if (!question) {
        alert('Please enter a question');
        return;
    }

    // Show loading state
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').textContent = 'Processing...';
    
    // Clear previous results
    document.getElementById('result').innerHTML = '';
    document.getElementById('visitedUrls').innerHTML = '';
    
    try {
        const response = await fetch(`${BASE_PATH}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                agent_url: agentUrl
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display results
        document.getElementById('result').innerHTML = data.content;
        
        // Display visited URLs
        if (data.visited_urls && data.visited_urls.length > 0) {
            const urlsList = document.createElement('ul');
            data.visited_urls.forEach(url => {
                const li = document.createElement('li');
                li.textContent = url;
                li.style.wordBreak = 'break-word'; // Ensure long URLs can wrap
                urlsList.appendChild(li);
            });
            document.getElementById('visitedUrls').appendChild(urlsList);
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('result').innerHTML = `Error: ${error.message}`;
    } finally {
        // Restore button state
        document.getElementById('submitBtn').disabled = false;
        document.getElementById('submitBtn').textContent = 'Submit Question';
    }
} 