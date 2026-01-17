from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import re
import os

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])  # Enable CORS for all origins

DATABASE = 'russian_words.db'

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with Russian words"""
    if os.path.exists(DATABASE):
        print(f"Database {DATABASE} already exists.")
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create table for Russian words
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS russian_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            lowercase_word TEXT NOT NULL
        )
    ''')
    
    # Common Russian words dictionary
    russian_words = [
        # Pronouns
        'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они',
        'мой', 'твой', 'его', 'её', 'наш', 'ваш', 'их',
        'это', 'этот', 'эта', 'эти', 'тот', 'та', 'те',
        'кто', 'что', 'какой', 'какая', 'какое', 'какие',
        'который', 'которая', 'которое', 'которые',
        'чей', 'чья', 'чьё', 'чьи',
        
        # Common verbs
        'быть', 'есть', 'был', 'была', 'было', 'были', 'буду', 'будет', 'будут',
        'иметь', 'делать', 'мочь', 'могу', 'можешь', 'может', 'можем', 'можете', 'могут',
        'говорить', 'сказать', 'знать', 'хотеть', 'хочу', 'хочет', 'хотят',
        'идти', 'пойти', 'идёт', 'идут', 'пошёл', 'пошла', 'пошли',
        'видеть', 'смотреть', 'думать', 'писать', 'читать',
        'жить', 'работать', 'учиться', 'любить', 'понимать',
        'стать', 'стал', 'стала', 'стали', 'станет',
        'дать', 'дал', 'дала', 'дали', 'даёт', 'дают',
        'взять', 'взял', 'взяла', 'взяли', 'возьмёт',
        'прийти', 'пришёл', 'пришла', 'пришли', 'придёт',
        'сидеть', 'стоять', 'лежать', 'спать',
        'есть', 'пить', 'кушать',
        
        # Common nouns
        'человек', 'люди', 'мужчина', 'женщина', 'ребёнок', 'дети',
        'день', 'ночь', 'утро', 'вечер', 'время', 'год', 'месяц', 'неделя',
        'дом', 'квартира', 'комната', 'окно', 'дверь', 'стол', 'стул',
        'город', 'страна', 'мир', 'земля', 'небо', 'вода', 'воздух',
        'работа', 'дело', 'вопрос', 'ответ', 'слово', 'язык', 'текст',
        'жизнь', 'смерть', 'любовь', 'друг', 'семья', 'мать', 'отец',
        'голова', 'рука', 'нога', 'глаз', 'ухо', 'нос', 'рот',
        'книга', 'школа', 'университет', 'учитель', 'студент',
        'компьютер', 'телефон', 'машина', 'автомобиль',
        'еда', 'хлеб', 'вода', 'молоко', 'мясо', 'рыба',
        'число', 'цифра', 'буква', 'имя', 'фамилия',
        
        # Adjectives
        'большой', 'большая', 'большое', 'большие',
        'маленький', 'маленькая', 'маленькое', 'маленькие',
        'хороший', 'хорошая', 'хорошее', 'хорошие', 'хорошо',
        'плохой', 'плохая', 'плохое', 'плохие', 'плохо',
        'новый', 'новая', 'новое', 'новые',
        'старый', 'старая', 'старое', 'старые',
        'молодой', 'молодая', 'молодое', 'молодые',
        'красивый', 'красивая', 'красивое', 'красивые',
        'белый', 'чёрный', 'красный', 'синий', 'зелёный', 'жёлтый',
        'первый', 'второй', 'третий', 'последний',
        'один', 'одна', 'одно', 'два', 'три', 'четыре', 'пять',
        'шесть', 'семь', 'восемь', 'девять', 'десять',
        
        # Adverbs
        'здесь', 'там', 'тут', 'где', 'куда', 'откуда',
        'сейчас', 'теперь', 'тогда', 'когда', 'всегда', 'никогда',
        'очень', 'много', 'мало', 'немного', 'совсем',
        'хорошо', 'плохо', 'быстро', 'медленно',
        'так', 'как', 'почему', 'зачем', 'поэтому',
        'да', 'нет', 'ещё', 'уже', 'только', 'даже',
        'вместе', 'опять', 'снова', 'опять',
        
        # Prepositions
        'в', 'на', 'с', 'со', 'к', 'о', 'об', 'у', 'из', 'от', 'до',
        'по', 'при', 'через', 'над', 'под', 'перед', 'за', 'между',
        'для', 'без', 'про', 'во',
        
        # Conjunctions
        'и', 'а', 'но', 'или', 'да', 'если', 'что', 'чтобы',
        'потому', 'так', 'как', 'когда', 'пока', 'хотя',
        
        # Particles
        'не', 'ни', 'же', 'ли', 'бы', 'ведь', 'вот', 'вон',
        
        # Common words
        'спасибо', 'пожалуйста', 'привет', 'здравствуйте', 
        'до', 'свидания', 'пока', 'извините', 'простите',
        'можно', 'нельзя', 'надо', 'нужно',
        
        # Additional common words
        'сегодня', 'вчера', 'завтра', 'час', 'минута', 'секунда',
        'право', 'левый', 'правый', 'левая', 'правая',
        'верх', 'низ', 'верхний', 'нижний',
        'начало', 'конец', 'середина',
        'часть', 'целый', 'весь', 'вся', 'всё', 'все',
        'каждый', 'каждая', 'каждое', 'любой', 'другой',
        'сам', 'сама', 'само', 'сами', 'самый',
        'свой', 'своя', 'своё', 'свои',
        'такой', 'такая', 'такое', 'такие',
        'какой-то', 'какая-то', 'какое-то', 'какие-то',
        'никто', 'ничто', 'никакой', 'ничей',
        'некто', 'нечто', 'некоторый',
        'весь', 'всё', 'вся', 'все',
        'россия', 'российский', 'русский', 'русская', 'русское', 'русские',
        'москва', 'московский',
    ]
    
    # Insert words into database
    for word in russian_words:
        try:
            cursor.execute(
                'INSERT INTO russian_words (word, lowercase_word) VALUES (?, ?)',
                (word, word.lower())
            )
        except sqlite3.IntegrityError:
            # Skip duplicates
            pass
    
    conn.commit()
    conn.close()
    print(f"Database initialized with {len(russian_words)} Russian words.")

def is_russian_word(word):
    """Check if a word exists in the Russian dictionary"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Normalize word (lowercase)
    normalized_word = word.lower()
    
    cursor.execute(
        'SELECT word FROM russian_words WHERE lowercase_word = ?',
        (normalized_word,)
    )
    
    result = cursor.fetchone()
    conn.close()
    print(f"{normalized_word} {result} ")
    return result is not None

@app.route('/api/check-text', methods=['POST'])
def check_text():
    """API endpoint to check text for non-Russian words"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Split text into words, preserving punctuation
        # Match words including Cyrillic, Latin, and numbers
        word_pattern = re.compile(r'[a-zA-Zа-яА-ЯёЁ0-9]+')
        words = word_pattern.findall(text)
        
        # Check each word
        results = []
        for word in words:
            # Check if word contains Cyrillic characters
            has_cyrillic = bool(re.search(r'[а-яА-ЯёЁ]', word))
            
            # If word has Cyrillic, check if it's in dictionary
            if has_cyrillic:
                is_russian = is_russian_word(word)
            else:
                # Non-Cyrillic words are considered non-Russian
                is_russian = False
            
            results.append({
                'word': word,
                'is_russian': is_russian
            })
        
        # Statistics
        total_words = len(results)
        non_russian_count = sum(1 for r in results if not r['is_russian'])
        print(results)
        return jsonify({
            'results': results,
            'statistics': {
                'total_words': total_words,
                'non_russian_words': non_russian_count,
                'russian_words': total_words - non_russian_count
            },
            'text': text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-word', methods=['POST'])
def add_word():
    """API endpoint to add a word to the dictionary"""
    try:
        data = request.get_json()
        word = data.get('word', '').strip()
        
        if not word:
            return jsonify({'error': 'No word provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO russian_words (word, lowercase_word) VALUES (?, ?)',
                (word, word.lower())
            )
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'Word "{word}" added to dictionary'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Word already exists in dictionary'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dictionary-count', methods=['GET'])
def dictionary_count():
    """Get the total number of words in the dictionary"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM russian_words')
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({'count': result['count']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Russian Word Checker API is running'})

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the Flask app
    print("Starting Russian Word Checker API...")
    print("API will be available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
