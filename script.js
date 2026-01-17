// API Configuration
const API_URL = 'http://localhost:5000/api';

// DOM Elements
const inputText = document.getElementById('inputText');
const outputDiv = document.getElementById('output');
const statsDiv = document.getElementById('stats');
const checkBtn = document.getElementById('checkBtn');
const clearBtn = document.getElementById('clearBtn');

// Event Listeners
checkBtn.addEventListener('click', checkText);
clearBtn.addEventListener('click', clearAll);

// Allow Enter key to trigger check (with Ctrl/Cmd)
inputText.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        checkText();
    }
});

async function checkText() {
    const text = inputText.value.trim();
    
    if (!text) {
        showError('Пожалуйста, введите текст для проверки');
        return;
    }
    
    // Show loading state
    checkBtn.disabled = true;
    checkBtn.textContent = 'Проверяю...';
    outputDiv.innerHTML = '<p class="placeholder">Обработка текста...</p>';
    
    try {
        const response = await fetch(`${API_URL}/check-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
            mode: 'cors' // Explicitly set CORS mode
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError('Ошибка при проверке текста. Убедитесь, что сервер запущен и CORS настроен.');
    } finally {
        checkBtn.disabled = false;
        checkBtn.textContent = 'Проверить текст';
    }
}

function displayResults(data) {
    const { results, statistics, text } = data;
    
    // Create a map of words to their Russian status
    const wordMap = new Map();
    results.forEach(result => {
        wordMap.set(result.word.toLowerCase(), result.is_russian);
    });
    
    // Process the text and highlight non-Russian words
    let processedText = text;
    
    // Sort words by length (longest first) to avoid partial replacements
    const sortedResults = [...results].sort((a, b) => b.word.length - a.word.length);
    
    // Replace each word with marked version if not Russian
    sortedResults.forEach(result => {
        if (!result.is_russian) {
            // Use a more robust approach for Unicode characters without relying on word boundaries
            const escapedWord = escapeRegex(result.word);
            // Use word boundaries with Unicode-aware approach
            const regex = new RegExp(`(^|\\s)(${escapedWord})(\\s|$|\\W)`, 'giu');
            
            console.log(`Debug: Processing word "${result.word}"`);
            console.log(`Debug: Escaped word: "${escapedWord}"`);
            console.log(`Debug: Regex pattern: ${regex}`);
            console.log(`Debug: Text before: "${processedText}"`);
            
            const originalText = processedText;
            processedText = processedText.replace(regex, (match, before, word, after) => {
                console.log(`Debug: Match found: "${match}" -> before:"${before}" word:"${word}" after:"${after}"`);
                return `${before}<span class="non-russian">${word}</span>${after}`;
            });
            
            if (processedText === originalText) {
                console.log(`Debug: No replacement made for "${result.word}"`);
            } else {
                console.log(`Debug: Text after: "${processedText}"`);
            }
        }
    });
    
    // Display the processed text
    outputDiv.innerHTML = processedText || '<p class="placeholder">Нет результатов</p>';
    
    // Display statistics
    statsDiv.innerHTML = `
        <div>
            <strong>Статистика проверки:</strong><br>
            📊 Всего слов: <strong>${statistics.total_words}</strong><br>
            ✅ Русских слов: <strong>${statistics.russian_words}</strong><br>
            ❌ Нерусских слов: <strong>${statistics.non_russian_words}</strong>
        </div>
    `;
    statsDiv.classList.add('show');
}

function showError(message) {
    outputDiv.innerHTML = `<p style="color: #e74c3c; font-weight: 600;">⚠️ ${message}</p>`;
    statsDiv.classList.remove('show');
}

function clearAll() {
    inputText.value = '';
    outputDiv.innerHTML = '<p class="placeholder">Результат появится здесь...</p>';
    statsDiv.innerHTML = '';
    statsDiv.classList.remove('show');
    inputText.focus();
}

function escapeRegex(string) {
    // Escape special regex characters for use in regex patterns
    // This handles all Unicode characters including Cyrillic
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Check API health on page load
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API Status:', data.message);
            
            // Get dictionary count
            const countResponse = await fetch(`${API_URL}/dictionary-count`);
            if (countResponse.ok) {
                const countData = await countResponse.json();
                console.log(`📚 Dictionary contains ${countData.count} Russian words`);
            }
        }
    } catch (error) {
        console.warn('⚠️ API is not running. Please start the backend server with: python app.py');
        showError('Сервер не запущен. Запустите: python app.py');
    }
}

// Initialize
checkAPIHealth();

// Add sample text on Shift+Enter
inputText.addEventListener('keydown', (e) => {
    if (e.shiftKey && e.key === 'Enter') {
        e.preventDefault();
        inputText.value = 'Это тестовый текст на русском языке. Здесь есть слова на English и другие foreign words. Также есть числа 123 и специальные символы!';
        checkText();
    }
});
