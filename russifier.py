import os
import re
import time
import pymorphy3
os.environ["GGML_QUIET"] = "1"
from llama_cpp import Llama

class Russifier:

    # СЛОВАРЬ 1: Строго английские корни-леммы (для сленга)
    DEFAULT_ENG_PURISM_DICT = {
        "share": "показать, поделиться",
        "meeting": "встреча, совещание, собрание",
        "user": "пользователь, клиент",
        "challenge": "испытание, вызов, сложная задача",
        "doc": "документ, бумага",
        "docs": "документ, бумага"
    }
    
    # СЛОВАРЬ 2: Строго русские леммы (для легальных исключений)
    DEFAULT_RUS_PURISM_DICT = {
        "менеджер": "руководитель, управляющий",
        "интернет": "межсеть, паутина",
        "дедлайн": "крайний срок, срок сдачи",

    }

    def __init__(self, model_path, n_threads=4, n_ctx=2048):
        """
        Инициализация конвейера с ОДНОЙ моделью Qwen 7B.
        """
        if model_path:
            print(f"Загрузка единого движка Qwen 7B из {model_path}...")
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                verbose=False
            )
        else:
            print("Initialiaing without loading the model")

        self.morph = pymorphy3.MorphAnalyzer()
        
        self.load_dictionaries()
        
    def load_dictionaries(self,
            eng_purism_dict=DEFAULT_ENG_PURISM_DICT, 
            rus_purism_dict=DEFAULT_RUS_PURISM_DICT):
        
        self.ENG_PURISM_DICT = eng_purism_dict
        self.RUS_PURISM_DICT = rus_purism_dict

    def _batch_decrypt_roots(self, suspicious_words):
        """
        [ВНУТРЕННИЙ МЕТОД] Пактная дешифровка: ИИ переводит весь список слов в корни за ОДИН вызов.
        """
        if not suspicious_words:
            return {}
            
        suspects_str = ", ".join(suspicious_words)
        
        prompt = (
            f"Ты — лингвистический сканер ИТ-сленга. Перед тобой список подозрительных слов, вырезанных из текста.\n"
            f"Переведи КАЖДОЕ слово в его исходную начальную форму на АНГЛИЙСКОМ языке (лемму).\n"
            f"Выводи строго в формате: 'слово -> english_lemma'. Каждое слово с новой строки. Не используй JSON, не пиши пояснений.\n\n"
            f"Пример:\n"
            f"задеплоили, таска, коммитить\n"
            f"Ответ:\n"
            f"задеплоили -> deploy\n"
            f"таска -> task\n"
            f"коммитить -> commit\n\n"
            f"Целевой список слов: {suspects_str}\n"
            f"Ответ:"
        )
        
        res = self.llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.01,
            max_tokens=200
        )
        
        # Парсим текстовый ответ модели в удобный Python-словарь
        ai_output = res["choices"][0]["message"]["content"].strip()
        rus_to_eng_map = {}
        
        for line in ai_output.split("\n"):
            if " -> " in line:
                parts = line.split(" -> ")
                if len(parts) == 2:
                    original, eng_lemma = parts[0].strip(), parts[1].strip().lower()
                    rus_to_eng_map[original] = eng_lemma
                    
        return rus_to_eng_map

    def _rewrite_sentence(self, sentence, instructions):
        """
            Преобразование предложения с жестким соблюдением падежей.
        """
        # Склеиваем инструкции через явный перенос
        inst_str = "\n".join(instructions)
        
        prompt_fix = (
            f"Исходное предложение: {sentence}\n\n"
            f"Инструкции по исправлению:\n{inst_str}\n\n"
            f"Задание: Перепиши предложение на красивом, естественном и чистом русском языке, соблюдая инструкции.\n"
            f"Строго соблюдай правила русской грамматики (правильно сопрягай глаголы по лицам, меняй падежи существительных).\n"
            f"Выведи только финальное измененное предложение. Иероглифы запрещены.\n\n"
            f"Исправленный вариант: " # <--- Модель ДОЛЖНА строго продолжить отсюда
        )
        # Используем create_completion вместо create_chat_completion
        res_fix = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты профессиональный русский редактор. "
                        "Отвечай только на русском языке. "
                        "Никогда не используй китайский, английский или другие языки."
                    )
                },
                {
                    "role": "user",
                    "content": prompt_fix
                }
            ],
            temperature=0.1,
            max_tokens=128
        )

        return res_fix["choices"][0]["message"]["content"].strip()



    def find_suspicious_words(self, sentence_words_map):
        """
            Cито поиска подозрительных слов

        """
        suspicious_words = set()

        for sentence_words in sentence_words_map:
            for word in sentence_words:
                if len(word) <= 2:
                    continue
                word_lower = word.lower()
                parsed = self.morph.parse(word_lower)[0]

                is_official_slang = 'Slng' in parsed.tag
                is_fake_guess = not parsed.is_known

                if parsed.normal_form in self.RUS_PURISM_DICT:
                    suspicious_words.add(word_lower)
                    continue
                
                if re.search(r'[a-zA-Z]', word):
                    suspicious_words.add(word_lower)
                    continue

                if is_official_slang:
                    suspicious_words.add(word_lower)
                    continue

                if is_fake_guess:
                    suspicious_words.add(word_lower)
                    continue


        return suspicious_words


    def _fmt_exact(self, word, options):
        return f"слово '{word}' заменить на один из вариантов: '{options}'"

    def _fmt_fallback(self, word, eng_lemma):
        return f"слово '{word}' — это новый англицизм (корень: {eng_lemma}). Обязательно замени его на красивый русский литературный аналог на свое усмотрение."

    def rewrite_instructions(self, words_in_sentence, rus_to_eng_map):
        """
        Инструкции для ИИ по преобразованию предложений
        """
        instructions = []

        for word in words_in_sentence:
            if len(word) <= 2: 
                continue
                
            # 1. Проверка по русскому контуру
            rus_lemma = self.morph.parse(word)[0].normal_form
            if rus_lemma in self.RUS_PURISM_DICT:
                instructions.append(self._fmt_exact(word, self.RUS_PURISM_DICT[rus_lemma]))
                continue # Уходим на следующее слово, избавляясь от elif
                
            # 2. Проверка по английскому контуру
            if word in rus_to_eng_map:
                eng_lemma = rus_to_eng_map[word]
                
                if eng_lemma in self.ENG_PURISM_DICT:
                    instructions.append(self._fmt_exact(word, self.ENG_PURISM_DICT[eng_lemma]))
                else:
                    instructions.append(self._fmt_fallback(word, eng_lemma))

        return instructions



    def split_text_into_sentences_words(self, text):
        """
            Splitting text into sentences and then each sentence into words

        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        words_in_text = [] # Храним списки слов для каждого предложения, чтобы не искать заново

        for sentence in sentences:
            if not sentence:
                words_in_text.append([])
                continue
            words_in_sentence = re.findall(r'\b[а-яА-Яa-zA-Z0-9-]+\b', sentence)
            words_in_text.append(words_in_sentence)
        
        return sentences, words_in_text

    def llm_rewrite(self, sentences, words, rus_to_eng_map):
        """
            Rewrite sentences with help of AI
        """
        sentences_updated = []
        rewrite_count = 0
        
        for sentence, words_in_sentence in zip(sentences,words):
            if not words_in_sentence:
                continue
            print(words_in_sentence)
            print(sentence)    
            instructions = self.rewrite_instructions(words_in_sentence, rus_to_eng_map)
            print(instructions)

            # Если есть инструкции используем мощь ИИ
            if instructions:
                sentence_updated = self._rewrite_sentence(sentence, instructions)
                rewrite_count += 1
                print(sentence_updated)
                sentences_updated.append(sentence_updated)
            
        return sentences_updated, rewrite_count


    def process_text(self, large_text):
        """
        ОСНОВНОЙ МЕТОД: Запуск пакетного конвейера очистки текста.
        """
        print("\n=== СТАРТ ОБРАБОТКИ ПАКЕТНОГО КОНВЕЙЕРА (ОДНА МОДЕЛЬ 7B) ===")
        global_start = time.time()
        
        # Шаг 1: Разбиваем текст на предложения. Храним списки слов для каждого предложения, чтобы не искать заново
        sentences, words = self.split_text_into_sentences_words(large_text) 
        
        # Шаг 2: Python собирает ВСЕ уникальные подозрительные слова со всего текста
        suspicious_words = self.find_suspicious_words(words)

        print(f"Найдено {len(suspicious_words)} уникальных подозрительных слов во всем тексте.")
        print(suspicious_words)
 
        # Шаг 3: ОДИН пакетный вызов ИИ для дешифровки всех корней разом

        print("Отправляем список слов на дешифровку корней...")
        #rus_to_eng_map = self._batch_decrypt_roots(list(all_suspicious_words))
        rus_to_eng_map = {
            'зааппрувлю': 'approve', 
            'митинга': 'meeting', 
            'менеджер': 'manager', 
            'интернете': 'internet', 
            'пошеришь': 'share'}

        print(f"Получена карта английских корней от ИИ: {rus_to_eng_map}")
        
# --- ШАГ 4: Анализ по двум словарям и подборка слов через модель ---
        sentences_updated, rewrite_count = self.llm_rewrite(sentences, words, rus_to_eng_map)

        global_end = time.time()

        print(f"\n=== ОБРАБОТКА ЗАВЕРШЕНА ЗА {global_end - global_start:.2f} сек ===")
        print(f"Всего предложений: {len(sentences_updated)} | Тяжелых преоразований: {rewrite_count}")
        
        return " ".join(sentences_updated)


if __name__ == "__main__":
    # Укажи правильный путь к своей 7B модели
    russifier = Russifier(model_path="models/qwen2.5-7b-instruct-q5_k_m.gguf", n_threads=4)
    
    dirty_text = (
        "Команда провела два отличных дня на природе. " # Пролетит мимо ИИ мгновенно
        "Давай ты пошеришь экран, а я зааппрувлю доки после митинга. " # Сленг -> Рерайт
        "Вчера была отличная погода, и мы гуляли в парке до самого вечера. " # Пролетит мимо ИИ мгновенно
        "Наш новый менеджер долго искал эту важную информацию в интернете." # Из списка ALWAYS_CATCH -> Рерайт
    )
    
    clean_text = russifier.process_text(dirty_text)
    print("\nИсправленный текст:")
    print(clean_text)