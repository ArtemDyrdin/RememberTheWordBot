import datetime

class SRSService:
    @staticmethod
    def calculate_next_review(
        current_repeat_count: int, 
        current_ease_factor: float, 
        is_correct: bool
    ) -> tuple[int, float, datetime.datetime]:
        """
        Реализует бинарный алгоритм SM-2 на основе существующих полей базы данных.
        Возвращает кортеж: (new_repeat_count, new_ease_factor, next_review_datetime)
        """
        now = datetime.datetime.now()

        if not is_correct:
            # --- НЕПРАВИЛЬНЫЙ ОТВЕТ ---
            # Сбрасываем счетчик успешных повторений подряд
            new_repeat_count = 0
            # Штрафуем ease_factor (но не даем упасть ниже минимального порога 1.3 в SM-2)
            new_ease_factor = max(1.3, current_ease_factor - 0.2)
            # Минимальный интервал по твоему ТЗ: 0.5 дня (12 часов)
            next_review = now + datetime.timedelta(hours=12)
            
            return new_repeat_count, new_ease_factor, next_review

        else:
            # --- ПРАВИЛЬНЫЙ ОТВЕТ ---
            new_repeat_count = current_repeat_count + 1
            
            # Слегка увеличиваем или удерживаем ease_factor при правильном ответе
            new_ease_factor = current_ease_factor + 0.1
            if new_ease_factor > 2.5: 
                new_ease_factor = 2.5 # Ограничим стандартным максимумом

            # Высчитываем интервал в днях на основе шага
            if new_repeat_count == 1:
                interval_days = 0.5  # 12 часов
            elif new_repeat_count == 2:
                interval_days = 2.0  # 2 дня
            elif new_repeat_count == 3:
                interval_days = 7.0  # 7 дней
            elif new_repeat_count == 4:
                interval_days = 30.0 # 30 дней
            elif new_repeat_count == 5:
                interval_days = 90.0
            else:
                # Если пользователь идет дальше 4-го шага, интервал масштабируется по формуле SM-2
                # Предыдущий интервал (30 дней) умножается на ease_factor
                interval_days = 90.0 * current_ease_factor

            next_review = now + datetime.timedelta(days=interval_days)
            
            return new_repeat_count, new_ease_factor, next_review