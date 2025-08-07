from core.driver import Browser
from core.parser import WildberriesParser
from data.saver import DataSaver
from data.database import Database
from core.price_analyzer import PriceAnalyzer
import json


def main():
    browser = Browser()
    try:
        parser = WildberriesParser(browser)
        saver = DataSaver()
        db = Database()
        analyzer = PriceAnalyzer(db)
        url = "https://www.wildberries.ru/catalog/elektronika/smartfony-i-telefony/vse-smartfony"
        products = parser.parse_category(url, max_pages=1, fbrand='23233')
        
        print("\nИтоговые результаты:")
        for i, product in enumerate(products[:40], 1):
            print(f"{i}. {product.brand} {product.name} {product.rate} - {product.price} ₽ | {product.link}")
        
        saver.save_to_database(products)

        # Анализ динамики цен (пример для первых 3 товаров)
        print("\nАнализ динамики цен:")
        for product in products[:5]:
            analysis = analyzer.analyze_price_changes(product.link)
            print(f"\nТовар: {product.brand} {product.name}")
            print(f"Текущая цена: {product.price} ₽")
            print(f"Изменение цены: {analysis.get('price_diff_percent', 0)}%")
            print(f"Тренд: {analysis.get('price_trend', 'нет данных')}")
            print(f"Анализ скидки: {json.dumps(analysis.get('discount_analysis', {}), indent=2, ensure_ascii=False)}")
        
        # Поиск лучших предложений
        print("\nЛучшие предложения (реальные скидки):")
        best_deals = analyzer.find_best_deals(min_discount=15)
        for deal in best_deals:
            print(f"{deal['brand']} {deal['name']}: {deal['previous_price']} → {deal['current_price']} ₽ ({deal['change_percent']}%)")

    finally:
        browser.close()

if __name__ == "__main__":
    main() 