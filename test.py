import asyncio
from app.services.dictionary import DictionaryService

async def main():
    dict_service = DictionaryService()
    
    word = "hello"
    print(f"Ищу слово: {word}...")
    
    result = await dict_service.fetch_word_info(word)
    
    if result:
        print("\n--- Результат парсинга ---")
        print(f"Слово: {result['word']}")
        print(f"Транскрипция: {result['transcription']}")
        print(f"Дефиниция (EN): {result['definition']}")
        print(f"Пример (EN): {result['example']}")
        print(f"Переводы (RU): {', '.join(result['translations'])}")
    else:
        print("Не удалось получить данные или слово не найдено.")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())