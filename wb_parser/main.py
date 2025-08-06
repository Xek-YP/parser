from core.driver import Browser
from core.parser import WildberriesParser
from data.saver import DataSaver

def main():
    browser = Browser()
    try:
        parser = WildberriesParser(browser)
        saver = DataSaver()
        
        url = "https://www.wildberries.ru/catalog/elektronika/smartfony-i-telefony/vse-smartfony"
        products = parser.parse_category(url, max_pages=2)
        
        print("\nИтоговые результаты:")
        for i, product in enumerate(products[:40], 1):
            print(f"{i}. {product.brand} {product.name} {product.rate} - {product.price} ₽ | {product.link}")
        
        saver.save_to_csv(products)
        saver.save_to_excel(products)
    finally:
        browser.close()

if __name__ == "__main__":
    main()