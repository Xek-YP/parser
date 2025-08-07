import re
import time
import random

def clean_text(text: str) -> str:
    """Очистка текста от лишних символов"""
    if not text:
        return ""
    return re.sub(r'^[/\s]+|[/\s]+$', '', str(text)).replace('\xa0', ' ').strip()

def clean_price(price_text: str) -> int:
    """Преобразование цены в число"""
    try:
        return int(re.sub(r'[^\d]', '', str(price_text)))
    except:
        return 0

def random_delay(min_sec: float = 1, max_sec: float = 3) -> None:
    """Случайная задержка между действиями"""
    time.sleep(random.uniform(min_sec, max_sec))