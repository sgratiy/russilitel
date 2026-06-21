import os
import re
import time
from huggingface_hub import InferenceClient
from morphology_engine import MorphologyEngine

class Russifier:

    DEFAULT_ENG_PURISM_DICT = {
        "share": "показать, поделиться",
        "user": "пользователь, клиент",
        "challenge": "испытание, вызов, сложная задача",
        "doc": "документ, бумага",
        "meeting": "собрание, совещание, сборище"
    }

    DEFAULT_RUS_PURISM_DICT = {
        "менеджер": "руководитель, управляющий",
        "интернет": "межсеть, паутина",
        "дедлайн": "крайний срок, срок сдачи",
        "митинг": "собрание, сборище"
    }

    def __init__(self, hf_token, model_name="Qwen/Qwen2.5-7B-Instruct"):
        self.client = InferenceClient(token=hf_token)
        self.model_name = model_name
#        self.morph = pymorphy3.MorphAnalyzer()
        self.morph_engine = MorphologyEngine()
        self.load_dictionaries()

    # ---------------- DICTIONARIES ----------------

    def load_dictionaries(self,
                          eng_purism_dict=None,
                          rus_purism_dict=None):

        self.ENG_PURISM_DICT = eng_purism_dict or self.DEFAULT_ENG_PURISM_DICT
        self.RUS_PURISM_DICT = rus_purism_dict or self.DEFAULT_RUS_PURISM_DICT

    # ---------------- CORE LLM CALL ----------------

    def _rewrite_sentence(self, sentence, instructions):

        prompt = (
            f"Исходное предложение:\n{sentence}\n\n"
            f"Инструкции:\n{chr(10).join(instructions)}\n\n"
            "Перепиши предложение на естественном, грамотном русском языке.\n"
            "Выведи только итоговый вариант."
        )

        res = self.client.chat_completion(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "Ты профессиональный редактор русского языка."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )

        return res.choices[0].message.content.strip()

    # ---------------- TEXT SPLIT ----------------

    def split_text_into_sentences_words(self, text):
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        words_by_sentence = []

        for s in sentences:
            words = re.findall(r'\b[а-яА-Яa-zA-Z0-9-]+\b', s)
            words_by_sentence.append(words)

        return sentences, words_by_sentence

    # ---------------- DETECTION ----------------

    def find_suspicious_words(self, words_by_sentence):
        suspicious = set()

        for words in words_by_sentence:
            for w in words:
                if len(w) <= 2:
                    continue

                wl = w.lower()
                parsed = self.morph_engine.best_parse(wl)

                if re.search(r"[a-zA-Z]", wl):
                    suspicious.add(wl)
                elif not parsed.is_known:
                    suspicious.add(wl)
                elif parsed.normal_form in self.RUS_PURISM_DICT:
                    suspicious.add(wl)

        return suspicious


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
            f"Выводи строго в формате: 'исходное слово на русском языке -> английская лемма'. \n"
            f"Верни ровно одно английское слово для каждого входного слова. \n"
            f"Каждое слово с новой строки. Не используй JSON, не пиши пояснений.\n\n"
            f"Примеры:\n"
            f"задеплоили -> deploy\n"
            f"таска -> task\n"
            f"интернете -> internet\n"
            f"коммитить -> commit\n\n"
            f"Целевой список слов: {suspects_str}\n"
            f"Ответ:"
        )

        res = self.client.chat_completion(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.01,
            max_tokens=200
        )

        ai_output = res.choices[0].message.content.strip()
        rus_to_eng_map = {}

        for line in ai_output.split("\n"):
            if "->" not in line:
                continue

            parts = line.split("->")
            if len(parts) == 2:
                original = parts[0].strip()
                eng_lemma = parts[1].strip().lower()
                rus_to_eng_map[original] = eng_lemma

        return rus_to_eng_map


    # ---------------- INSTRUCTIONS ----------------

    def _fmt_exact(self, word, options):
        return (
            f"слово '{word}' заменить на один из вариантов: '{options}'. "
            f"Обязательно сохранить падеж, число и грамматическую форму исходного слова."
        )
    def _fmt_fallback(self, word, eng_lemma):
        return  (
            f"слово '{word}' — это новый англицизм (корень: {eng_lemma}). Обязательно замени его на красивый русский литературный аналог на свое усмотрение."
            f"Обязательно сохранить падеж, число и грамматическую форму исходного слова."
        )


    def rewrite_instructions(self, words_in_sentence, rus_to_eng_map):
        """
        Инструкции для ИИ по преобразованию предложений
        """
        instructions = []
        for word in words_in_sentence:
            if len(word) <= 2:
                continue

            # -----------------------------
            # 1. Русский контур (приоритет №1)
            # -----------------------------
            rus_lemma = self.morph_engine.normal_form(word)

            if rus_lemma in self.RUS_PURISM_DICT:
                instructions.append(
                    self._fmt_exact(word, self.RUS_PURISM_DICT[rus_lemma])
                )
                continue

            # -----------------------------
            # 2. Английский контур (из LLM)
            # -----------------------------
            if word in rus_to_eng_map:
                eng_lemma = rus_to_eng_map[word]

                if eng_lemma in self.ENG_PURISM_DICT:
                    instructions.append(
                        self._fmt_exact(word, self.ENG_PURISM_DICT[eng_lemma])
                    )
                else:
                    instructions.append(
                        self._fmt_fallback(word, eng_lemma)
                    )

        return instructions

    # ---------------- MAIN LLM PIPELINE ----------------

    def llm_rewrite(self, sentences, words_by_sentence, rus_to_eng_map):
        results = []

        for sentence, words in zip(sentences, words_by_sentence):

            instructions = self.rewrite_instructions(words, rus_to_eng_map)
            print(sentence)
            print(f"Instructions: {instructions}")
            if instructions:
                rewritten = self._rewrite_sentence(sentence, instructions)
                results.append(rewritten)
                print(f"Changed to: {rewritten}")
            else:
                results.append(sentence)
                print("Did not chnage")

        return results, len(results)

    # ---------------- MAIN ENTRY ----------------

    def process_text(self, text):

        print("=== START ===")

        sentences, words = self.split_text_into_sentences_words(text)

        suspicious = self.find_suspicious_words(words)

        print("Suspicious words:", suspicious)

        rus_to_eng_map = self._batch_decrypt_roots(list(suspicious))

        print(f"rus_to_eng_map: {rus_to_eng_map}")

        result, count = self.llm_rewrite(sentences, words, rus_to_eng_map)

        print(f"Rewritten sentences: {count}")

        return " ".join(result)