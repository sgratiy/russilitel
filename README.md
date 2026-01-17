# 🇷🇺 Russian Word Checker (Проверка русских слов)

A web application that identifies and underlines words that do not belong to the Russian language. The application uses a Python Flask backend with a SQLite database to store Russian words.

## Features

- ✅ Identifies non-Russian words in text
- 📊 Provides statistics on Russian vs non-Russian words
- 🎨 Beautiful, responsive UI with gradient design
- 💾 SQLite database for Russian word dictionary
- 🌐 RESTful API backend
- 🔍 Real-time text analysis

## Tech Stack

**Frontend:**
- HTML5
- CSS3 (with modern gradients and animations)
- Vanilla JavaScript (ES6+)

**Backend:**
- Python 3.x
- Flask (Web framework)
- Flask-CORS (Cross-origin resource sharing)
- SQLite3 (Database)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or navigate to the project directory:**
```bash
cd c:\Users\sergey\repos\russilitel
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start the backend server:**
```bash
python app.py
```

The server will start on `http://localhost:5000` and automatically create the SQLite database with Russian words.

4. **Open the frontend:**
   - Open `index.html` in your web browser
   - Or use a local server (recommended):
   ```bash
   python -m http.server 8000
   ```
   Then visit `http://localhost:8000`

## Usage

1. **Enter text** in the input textarea
2. **Click "Проверить текст (Check Text)"** button or press `Ctrl+Enter`
3. **View results** with non-Russian words underlined in red
4. **Check statistics** showing total words, Russian words, and non-Russian words

### Keyboard Shortcuts

- `Ctrl+Enter` / `Cmd+Enter`: Check text
- `Shift+Enter`: Load sample text for testing

## API Endpoints

The Flask backend provides the following API endpoints:

### Check Text
```
POST /api/check-text
Content-Type: application/json

{
  "text": "Это текст с English словами"
}
```

**Response:**
```json
{
  "results": [
    {"word": "Это", "is_russian": true},
    {"word": "текст", "is_russian": true},
    {"word": "с", "is_russian": true},
    {"word": "English", "is_russian": false},
    {"word": "словами", "is_russian": true}
  ],
  "statistics": {
    "total_words": 5,
    "russian_words": 4,
    "non_russian_words": 1
  },
  "text": "Это текст с English словами"
}
```

### Add Word to Dictionary
```
POST /api/add-word
Content-Type: application/json

{
  "word": "новоеслово"
}
```

### Get Dictionary Count
```
GET /api/dictionary-count
```

### Health Check
```
GET /api/health
```

## Database Structure

The SQLite database (`russian_words.db`) contains a single table:

```sql
CREATE TABLE russian_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
    lowercase_word TEXT NOT NULL
);
```

The database is automatically populated with common Russian words on first run, including:
- Pronouns (я, ты, он, она, etc.)
- Common verbs (быть, делать, говорить, etc.)
- Common nouns (человек, дом, работа, etc.)
- Adjectives (большой, хороший, новый, etc.)
- Adverbs, prepositions, conjunctions, and particles
- Numbers and common phrases

## Project Structure

```
russilitel/
├── app.py                  # Flask backend server
├── index.html              # Main HTML page
├── style.css               # Styling
├── script.js               # Frontend JavaScript
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── russian_words.db       # SQLite database (created on first run)
```

## Development

### Adding More Words

You can add words to the database in two ways:

1. **Via API:**
   ```bash
   curl -X POST http://localhost:5000/api/add-word \
     -H "Content-Type: application/json" \
     -d '{"word": "новоеслово"}'
   ```

2. **Directly in code:**
   Edit the `russian_words` list in `app.py` and delete `russian_words.db` to regenerate.

### Customization

- **Change port:** Modify the `port` parameter in `app.py`
- **Update UI colors:** Edit CSS variables in `style.css`
- **Modify word matching:** Update the regex patterns in `app.py`

## Troubleshooting

**Issue: "Server not running" error**
- Make sure the Python backend is running: `python app.py`
- Check that port 5000 is not being used by another application

**Issue: CORS errors**
- Ensure Flask-CORS is installed: `pip install flask-cors`
- Check that the API_URL in `script.js` matches your backend URL

**Issue: Words not being detected correctly**
- The dictionary contains common Russian words. Add missing words via the API
- Case is ignored during comparison (все слова нормализованы)

## License

This project is open source and available for educational purposes.

## Author

Built for Russian language text analysis and validation.
