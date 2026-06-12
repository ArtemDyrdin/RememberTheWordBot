import aiohttp
import logging

class DictionaryService:
    def __init__(self):
        self.base_url = "https://freedictionaryapi.com/api/v1/entries/en/{word}?translations=true"

    async def fetch_word_info(self, word: str) -> dict | None:
        """
        Делает запрос к Free Dictionary API и возвращает распарсенные данные:
        перевод (RU), дефиницию (EN), пример (EN) и транскрипции (UK/US).
        """
        url = self.base_url.format(word=word.lower().strip())
        
        # Настраиваем таймаут
        timeout = aiohttp.ClientTimeout(total=5)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logging.warning(f"API returned status {response.status} for word: {word}")
                        return None
                    
                    data = await response.json()
                    return self._parse_response(data)
                    
        except Exception as e:
            logging.error(f"Error fetching data from Free Dictionary API: {e}")
            return None

    def _parse_response(self, data: dict) -> dict | None:
        """
        Внутренний метод для извлечения нужных полей из JSON.
        """
        if not data or not isinstance(data, dict):
            return None

        entries = data.get("entries", [])
        if not entries:
            return None

        # Берем первую запись
        entry = entries[0]

        word_text = data.get("word", "")

        # 1. Извлекаем транскрипции
        pronunciations = entry.get("pronunciations", [])
        uk_trans = None
        us_trans = None

        for p in pronunciations:
            text = p.get("text")
            tags = p.get("tags", [])

            if not text:
                continue

            # Британский вариант
            if "Received Pronunciation" in tags and not uk_trans:
                uk_trans = text

            # Американский вариант
            if "General American" in tags and not us_trans:
                us_trans = text

        # Формируем строку транскрипции
        transcription_parts = []

        if uk_trans:
            transcription_parts.append(f"UK: {uk_trans}")

        if us_trans:
            transcription_parts.append(f"US: {us_trans}")

        if transcription_parts:
            final_transcription = " | ".join(transcription_parts)
        else:
            # Берем первую доступную транскрипцию
            final_transcription = (
                pronunciations[0].get("text", "")
                if pronunciations
                else ""
            )

        # 2. Извлекаем смысл, пример и переводы
        senses = entry.get("senses", [])

        definition = ""
        example = ""
        russian_translations = []

        if senses:
            first_sense = senses[0]

            definition = first_sense.get("definition", "")

            examples = first_sense.get("examples", [])
            if examples:
                example = examples[0]

            # Собираем переводы из всех значений
            for sense in senses:
                for translation in sense.get("translations", []):
                    language = translation.get("language", {})
                    code = language.get("code")

                    if code in ("ru", "rus"):
                        word_ru = translation.get("word")

                        if word_ru and word_ru not in russian_translations:
                            russian_translations.append(word_ru)

        return {
            "word": word_text,
            "transcription": final_transcription,
            "definition": definition,
            "example": example,
            "translations": russian_translations,
        }