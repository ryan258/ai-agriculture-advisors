// State Management
const state = {
    expertRoles: [],
    query: '',
    history: JSON.parse(localStorage.getItem('queryHistory')) || [],
    darkMode: localStorage.getItem('darkMode') === 'true'
};

// Common Queries for Suggestions
const suggestions = [
    "How do I improve soil fertility organically?",
    "What are the best practices for drip irrigation?",
    "Explain the impact of climate change on wheat yield.",
    "Current market trends for soybeans.",
    "Integrated Pest Management for corn."
];

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    renderHistory();
    renderSuggestions();

    // Event Listeners
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('query').addEventListener('input', (e) => state.query = e.target.value);
});

// Theme Management
function initTheme() {
    if (state.darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('themeToggle').textContent = '☀️';
    } else {
        document.documentElement.removeAttribute('data-theme');
        document.getElementById('themeToggle').textContent = '🌙';
    }
}

function toggleTheme() {
    state.darkMode = !state.darkMode;
    localStorage.setItem('darkMode', state.darkMode);
    initTheme();
}

// Suggestions
function renderSuggestions() {
    const container = document.getElementById('suggestions');
    container.innerHTML = suggestions.map(s =>
        `<div class="chip" onclick="useSuggestion('${s.replace(/'/g, "\\'")}')">${s}</div>`
    ).join('');
}

function useSuggestion(text) {
    document.getElementById('query').value = text;
    state.query = text;
}

// History Management
function renderHistory() {
    const container = document.getElementById('historyList');
    if (state.history.length === 0) {
        container.innerHTML = '<div style="color:var(--muted); font-style:italic;">No recent queries</div>';
        return;
    }
    container.innerHTML = state.history.map((item, index) =>
        `<div class="history-item" onclick="loadHistory(${index})">
            ${new Date(item.timestamp).toLocaleDateString()} - ${item.query}
        </div>`
    ).join('');
}

function addToHistory(query, expertRoles) {
    const newItem = { query, expertRoles, timestamp: Date.now() };
    state.history.unshift(newItem);
    if (state.history.length > 10) state.history.pop(); // Keep last 10
    localStorage.setItem('queryHistory', JSON.stringify(state.history));
    renderHistory();
}

function loadHistory(index) {
    const item = state.history[index];
    document.getElementById('query').value = item.query;
    state.query = item.query;

    // Reset checkboxes
    document.querySelectorAll('input[name="expertRole"]').forEach(cb => {
        cb.checked = item.expertRoles.includes(cb.value);
    });
}

// API Interactions
async function submitQuery() {
    const checkboxes = document.querySelectorAll('input[name="expertRole"]:checked');
    const expertRoles = Array.from(checkboxes).map(cb => cb.value);
    const query = document.getElementById('query').value;
    const responseElement = document.getElementById('response');
    const roundtableDiv = document.getElementById('roundtable');

    roundtableDiv.innerHTML = ''; // Clear roundtable

    if (expertRoles.length === 0) {
        showError(responseElement, 'Please select at least one expert.');
        return;
    }
    if (!query.trim()) {
        showError(responseElement, 'Please enter a query.');
        return;
    }

    // Show Loading
    responseElement.innerHTML = '<div class="loader"></div><p style="text-align:center">Consulting experts...</p>';

    addToHistory(query, expertRoles);

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ expertRoles, query }),
        });

        const data = await response.json();

        if (response.ok) {
            let html = '';
            for (const role of expertRoles) {
                html += `<div class="card">
                    <h3>${getExpertLabel(role)}</h3>
                    ${data.responses[role]?.error
                        ? `<p style='color:red;'>Error: ${data.responses[role].error}</p>`
                        : marked.parse(data.responses[role].response)}
                </div>`;
            }
            // Add Export Button
            html += `<button class="outline" onclick="exportResponse()">📥 Export Response</button>`;
            responseElement.innerHTML = html;
        } else {
            showError(responseElement, data.message);
        }
    } catch (error) {
        showError(responseElement, error.message);
    }
}

async function submitRoundTable() {
    const checkboxes = document.querySelectorAll('input[name="expertRole"]:checked');
    const expertRoles = Array.from(checkboxes).map(cb => cb.value);
    const query = document.getElementById('query').value;
    const roundtableDiv = document.getElementById('roundtable');
    const responseElement = document.getElementById('response');

    responseElement.innerHTML = ''; // Clear standard response

    if (expertRoles.length < 2) {
        showError(roundtableDiv, 'Please select at least two experts for a round table discussion.');
        return;
    }
    if (!query.trim()) {
        showError(roundtableDiv, 'Please enter a query.');
        return;
    }

    roundtableDiv.innerHTML = '<div class="loader"></div><p style="text-align:center">Convening round table...</p>';
    addToHistory(query, expertRoles);

    try {
        const response = await fetch('/api/roundtable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ expertRoles, query }),
        });

        const data = await response.json();

        if (response.ok) {
            let html = '<div class="card"><h2>🗣️ Round Table Transcript</h2><div class="transcript-container">';
            for (const msg of data.transcript) {
                html += `<div class="transcript-message">
                    <strong class="transcript-speaker">${msg.speaker}:</strong> 
                    <div class="transcript-text">${marked.parse(msg.text)}</div>
                </div>`;
            }
            html += '</div>';
            html += '<h2>✅ Consensus / Next-level Answer</h2>';
            html += `<div class="consensus-container">${marked.parse(data.finalAnswer)}</div></div>`;
            roundtableDiv.innerHTML = html;
        } else {
            showError(roundtableDiv, data.message);
        }
    } catch (error) {
        showError(roundtableDiv, error.message);
    }
}

// Utilities
function showError(element, message) {
    element.innerHTML = `<div class="card error-card">
        <h3 class="error-title">Error</h3>
        <p>${message}</p>
    </div>`;
}

function getExpertLabel(role) {
    const labels = {
        'agriculture': 'Agricultural Science Expert',
        'climate': 'Climate Change Impact Analyst',
        'commodities': 'Commodities Trading Specialist',
        'agritech': 'AgriTech Innovation Researcher',
        'supplychain': 'Food Supply Chain Analyst',
        'soil': 'Soil Health Specialist',
        'pest': 'Pest & Disease Management Expert',
        'irrigation': 'Irrigation & Water Management Specialist',
        'organic': 'Organic Farming Consultant',
        'economics': 'Agricultural Economics Advisor'
    };
    return labels[role] || role;
}

function exportResponse() {
    const content = document.getElementById('response').innerText;
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agriculture-advice.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
