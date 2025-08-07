from typing import List, Dict
from datetime import datetime, timedelta
from data.models import PriceHistory
from data.database import Database

class PriceAnalyzer:
    def __init__(self, db: Database):
        self.db = db
    
    def analyze_price_changes(self, product_link: str) -> Dict:
        """Анализирует динамику цен для конкретного товара"""
        history = self.db.get_price_history(product_link, days=60)
        print(history)
        if not history:
            return {"status": "no_data"}
        
        current = history[0]
        oldest = history[-1]
        
        # Основные метрики
        price_diff = current.price - oldest.price
        price_diff_percent = (price_diff / oldest.price) * 100 if oldest.price else 0
        
        # Анализ скидок
        discount_analysis = self._analyze_discounts(history)
        
        return {
            "current_price": current.price,
            "oldest_price": oldest.price,
            "price_diff": price_diff,
            "price_diff_percent": round(price_diff_percent, 2),
            "max_price": max(h.price for h in history),
            "min_price": min(h.price for h in history),
            "discount_analysis": discount_analysis,
            "price_trend": self._calculate_trend(history),
            "price_history": history
        }
    
    def _analyze_discounts(self, history: List[PriceHistory]) -> Dict:
        """Анализирует подлинность скидок"""
        if len(history) < 3:
            return {"Статус": "недостаточно данных"}
        
        current = history[0]
        
        # Проверка на "накрутку" цены перед скидкой
        if current.discount:
            prev_prices = [h.price for h in history[1:4]]
            if current.price < min(prev_prices):
                return {
                    "Статус": "реальная скидка",
                    "Скидка": current.discount,
                    "Цена до скидок": max(prev_prices)
                }
            else:
                return {
                    "Статус": "возможно не настоящая скидка",
                    "Скидка": current.discount,
                    "Цена до скидок": max(prev_prices)
                }
        return {"status": "нет скидки"}
    
    def _calculate_trend(self, history: List[PriceHistory]) -> str:
        """Определяет тренд цены (рост/падение/стабильность)"""
        if len(history) < 3:
            return "недостаточно данных"
        
        recent = history[:7]  # Берем последнюю неделю
        prices = [h.price for h in recent]
        
        if len(prices) < 3:
            return "стабильный"
        
        # Простая линейная регрессия
        x = range(len(prices))
        y = prices
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi*yi for xi, yi in zip(x, y))
        sum_xx = sum(xi*xi for xi in x)
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
        except ZeroDivisionError:
            return "стабильный"
        
        if slope > 0.05 * prices[0]:
            return "возрастающий"
        elif slope < -0.05 * prices[0]:
            return "убывающий"
        return "стабильный"
    
    def find_best_deals(self, min_discount: int = 20) -> List[Dict]:
        """Находит товары с реальными скидками"""
        price_changes = self.db.get_price_changes(days=14)
        return [
            item for item in price_changes
            if item.get("change_percent", 0) <= -min_discount
        ]
