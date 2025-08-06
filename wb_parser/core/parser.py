from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Optional
from data.models import Product
from selenium.webdriver.support import expected_conditions as EC
from .utils import clean_text, clean_price, random_delay

class WildberriesParser:
    def __init__(self, browser):
        self.browser = browser

    def parse_product_card(self, card: WebElement) -> Optional[Product]:
        """Парсинг одной карточки товара"""
        try:
            brand_elem = card.find_element(By.CSS_SELECTOR, ".product-card__brand, .brand-name, .product-card__brand-container")
            name_elem = card.find_element(By.CSS_SELECTOR, ".product-card__name, .goods-name")
            price_elem = card.find_element(By.CSS_SELECTOR, "ins.price__lower-price, .price__lower-price, .final-price")
            link_elem = card.find_element(By.CSS_SELECTOR, "a.j-card-link")
            
            product_data = {
                "brand": clean_text(brand_elem.text) if brand_elem else "Без бренда",
                "name": clean_text(name_elem.text),
                "price": clean_price(price_elem.text),
                "link": link_elem.get_attribute('href'),
                "rate": 0,
                "count_evolutions": 0,
                "old_price": None,
                "discount": None
            }

            # Дополнительные данные
            self._parse_old_price(card, product_data)
            self._parse_rating(card, product_data)
            self._calculate_discount(product_data)

            return Product.from_dict(product_data)
        except Exception as e:
            print(f"Ошибка при парсинге карточки: {str(e)[:200]}...")
            return None

    def _parse_old_price(self, card: WebElement, data: dict):
        """Парсинг старой цены"""
        try:
            old_price_elem = card.find_element(By.CSS_SELECTOR, "del")
            data["old_price"] = clean_price(old_price_elem.text)
        except:
            pass

    def _parse_rating(self, card: WebElement, data: dict):
        """Парсинг рейтинга и количества оценок"""
        try:
            rate_elem = card.find_element(By.CSS_SELECTOR, ".address-rate-mini--sm")
            rate_text = clean_text(rate_elem.text).replace(',', '.')
            data["rate"] = float(rate_text)
        except Exception as e:
            print(f"Ошибка при парсинге рейтинга: {e}")
            data["rate"] = 0.0

        try:
            count_elem = card.find_element(By.CSS_SELECTOR, "span.product-card__count")
            count = clean_price(count_elem.text)
            data["count_evolutions"] = count
            if count == 0:
                data["rate"] = 0.0
        except:
            data["count_evolutions"] = 0

    def _calculate_discount(self, data: dict):
        """Расчет скидки"""
        if data.get("old_price") and data["price"]:
            try:
                data["discount"] = int(round((1 - data["price"] / data["old_price"]) * 100))
            except:
                pass

    def parse_category(self, url: str, max_pages: int = 3) -> List[Product]:
        """Парсинг всей категории"""
        products = []
        
        for page in range(1, max_pages + 1):
            print(f"\nПарсинг страницы {page}...")
            page_url = f"{url.split('?')[0]}?page={page}&sort=popular&fbrand=5772"
            
            try:
                self.browser.driver.get(page_url)
                random_delay(2, 4)
                
                if page == 1:
                    self.browser.accept_cookies()
                    random_delay(1, 2)
                
                self.browser.scroll_page()
                random_delay(1, 2)
                
                self.browser.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card, article.product-card"))
                )
                
                cards = self.browser.driver.find_elements(By.CSS_SELECTOR, "div.product-card, article.product-card")
                print(f"Найдено {len(cards)} карточек товаров")
                
                for card in cards:
                    product = self.parse_product_card(card)
                    if product:
                        products.append(product)
                        print(f"Добавлен: {product.brand} {product.name} - {product.price} ₽")
                
                random_delay(3, 6)
                
            except Exception as e:
                print(f"Ошибка при обработке страницы {page}: {str(e)[:200]}")
                continue
        
        return products