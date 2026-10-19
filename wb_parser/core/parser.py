from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Optional
from data.models import Product
from selenium.webdriver.support import expected_conditions as EC
from .utils import clean_text, clean_price, random_delay

class WildberriesParser:
    def __init__(self, browser):
        self.browser = browser

    def _find(self, card: WebElement, selector: str) -> Optional[WebElement]:
        elements = card.find_elements(By.CSS_SELECTOR, selector)
        return elements[0] if elements else None

    def parse_product_card(self, card: WebElement) -> Optional[Product]:
        """Парсинг одной карточки товара"""
        try:
            brand_elem = self._find(card, 'span[class*="brand--"], .product-card__brand, .brand-name')
            name_elem = self._find(card, 'span[class*="productName--"], .product-card__name, .goods-name')
            price_elem = self._find(
                card,
                '[class*="price--"] ins, ins.price__lower-price, .price__lower-price, .final-price',
            )
            link_elem = self._find(card, 'a[class*="catalogCardLink--"], a.j-card-link')

            if not name_elem or not price_elem or not link_elem:
                return None

            product_data = {
                "brand": clean_text(brand_elem.text) if brand_elem else "Без бренда",
                "name": clean_text(name_elem.text),
                "price": clean_price(price_elem.text),
                "link": link_elem.get_attribute("href"),
                "rate": 0,
                "count_evolutions": 0,
                "old_price": None,
                "discount": None,
            }

            self._parse_old_price(card, product_data)
            self._parse_rating(card, product_data)
            self._parse_discount_badge(card, product_data)
            self._calculate_discount(product_data)

            return Product.from_dict(product_data)
        except Exception as e:
            print(f"Ошибка при парсинге карточки: {str(e)[:200]}...")
            return None

    def _parse_old_price(self, card: WebElement, data: dict):
        """Парсинг старой цены"""
        old_price_elem = self._find(card, '[class*="price--"] del, del')
        if old_price_elem:
            data["old_price"] = clean_price(old_price_elem.text) or None

    def _parse_discount_badge(self, card: WebElement, data: dict):
        """Скидка с бейджа карточки, например −16%."""
        badge = self._find(card, '.mo-badge_colors-bg_red')
        if not badge:
            return
        discount = clean_price(badge.text)
        if discount:
            data["discount"] = discount

    def _parse_rating(self, card: WebElement, data: dict):
        """Парсинг рейтинга и количества оценок, если они есть на карточке."""
        rate_elem = self._find(card, '[class*="address-rate"], .address-rate-mini--sm')
        if rate_elem:
            rate_text = clean_text(rate_elem.text).replace(",", ".")
            try:
                data["rate"] = float(rate_text)
            except ValueError:
                data["rate"] = 0.0

        count_elem = self._find(card, 'span[class*="product-card__count"], span.product-card__count')
        if count_elem:
            count = clean_price(count_elem.text)
            data["count_evolutions"] = count
            if count == 0:
                data["rate"] = 0.0

    def _calculate_discount(self, data: dict):
        """Расчет скидки, если на карточке нет бейджа."""
        if data.get("discount") or not data.get("old_price") or not data.get("price"):
            return
        try:
            data["discount"] = int(round((1 - data["price"] / data["old_price"]) * 100))
        except ZeroDivisionError:
            pass

    def parse_category(self, url: str, max_pages: int = 3, fbrand='5772') -> List[Product]:
        """Парсинг всей категории"""
        products = []
        
        for page in range(1, max_pages + 1):
            print(f"\nПарсинг страницы {page}...")
            page_url = f"{url.split('?')[0]}?page={page}&sort=popular&fbrand={fbrand}"
            
            try:
                if page == 1:
                    self.browser.warmup()

                self.browser.driver.get(page_url)
                random_delay(2, 4)
                self.browser.wait_if_blocked()
                if self.browser.is_blocked():
                    continue

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