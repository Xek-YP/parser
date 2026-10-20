from core.driver import Browser
from core.parser import WildberriesParser
from data.saver import DataSaver
from data.database import Database
from core.price_analyzer import PriceAnalyzer


def main():
    browser = Browser()
    try:
        parser = WildberriesParser(browser)
        saver = DataSaver()
        db = Database()
        analyzer = PriceAnalyzer(db)
        
        url = "https://www.wildberries.ru/catalog/elektronika/smartfony-i-telefony/vse-smartfony"
        products = parser.parse_category(url, max_pages=1, fbrand='6049')
        
        saver.save_to_database(products)
        
        real_discounts = analyzer.get_real_discounts(products)
        
        print("\nТовары с реальными скидками:")
        for i, item in enumerate(real_discounts, 1):
            product = item['product']
            analysis = item['analysis']

            print(f"\n{i}. {product.brand} {product.name}")
            print(f"💰 Текущая цена: {product.price} ₽")
            print(f"🏷️ Размер скидки: {analysis['discount_analysis']['discount']}%")
            print(f"📉 Было: {analysis['discount_analysis']['price_before']} ₽")
            print(f"📈 Экономия: {analysis['discount_analysis']['price_before'] - product.price} ₽")
            print(f"🔗 Ссылка: {product.link}")

            print(f"📊 Тренд: {analysis['price_trend']}")
            print(f"📅 Изменение цены за период: {analysis['price_diff_percent']}%")

    finally:
        browser.close()

if __name__ == "__main__":
    main()