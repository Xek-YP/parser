from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import random
import re
import csv
from datetime import datetime

def clean_text(text):
    """Очистка текста от лишних символов"""
    if not text:
        return ""
    return re.sub(r'^[/\s]+|[/\s]+$', '', str(text)).replace('\xa0', ' ').strip()

def clean_price(price_text):
    """Преобразование цены в число"""
    try:
        return int(re.sub(r'[^\d]', '', str(price_text)))
    except:
        return 0

def setup_driver():
    """Настройка драйвера Chrome"""
    options = Options()
    options.add_argument("--lang=ru")
    options.add_argument("--geo=ru")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def accept_cookies(driver):
    """Принятие куки, если появилось окно"""
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Принять') or contains(., 'Accept')]"))
        ).click()
    except:
        pass

def scroll_page(driver, scroll_pause=1):
    """Прокрутка страницы для загрузки всех товаров"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def parse_product_card(card):
    """Парсинг одной карточки товара"""
    try:
        # Новые селекторы для Wildberries (актуальные на 2024 год)
        brand_elem = card.find_element(By.CSS_SELECTOR, ".product-card__brand, .brand-name")
        name_elem = card.find_element(By.CSS_SELECTOR, ".product-card__name, .goods-name")
        price_elem = card.find_element(By.CSS_SELECTOR, "ins.price__lower-price, .price__lower-price, .final-price")
        
        # Получаем ссылку на товар
        link_elem = card.find_element(By.CSS_SELECTOR, "a.j-card-link")
        product_link = link_elem.get_attribute('href')
        
        brand = clean_text(brand_elem.text) if brand_elem else "Без бренда"
        name = clean_text(name_elem.text)
        price = clean_price(price_elem.text)
        
        # Попытка получить старую цену
        try:
            old_price_elem = card.find_element(By.CSS_SELECTOR, "del.price__old, .old-price")
            old_price = clean_price(old_price_elem.text)
        except:
            old_price = None
            
        # Попытка получить скидку
        try:
            discount_elem = card.find_element(By.CSS_SELECTOR, "span.price__sale, .discount-percentage")
            discount = clean_text(discount_elem.text)
        except:
            discount = None
            
        return {
            "brand": brand,
            "name": name,
            "price": price,
            "old_price": old_price,
            "discount": discount,
            "link": product_link,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"Ошибка при парсинге карточки: {str(e)[:100]}...")
        return None

def save_to_csv(products, filename="wildberries_products.csv"):
    """Сохранение результатов в CSV файл"""
    if not products:
        print("Нет данных для сохранения")
        return
    
    fieldnames = ["brand", "name", "price", "old_price", "discount", "link", "timestamp"]
    
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        print(f"\nДанные успешно сохранены в файл {filename}")
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")

def parse_wb_category(driver, url, max_pages=3):
    """Парсинг всей категории"""
    all_products = []
    
    for page in range(1, max_pages + 1):
        print(f"\nПарсинг страницы {page}...")
        page_url = f"{url.split('?')[0]}?page={page}&sort=popular"
        
        try:
            driver.get(page_url)
            time.sleep(random.uniform(2, 4))
            
            # Принимаем куки при первом заходе
            if page == 1:
                accept_cookies(driver)
                time.sleep(1)
            
            # Прокрутка для загрузки всех товаров
            scroll_page(driver)
            time.sleep(1)
            
            # Ждем загрузки карточек
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card, article.product-card"))
            )
            
            # Находим все карточки товаров
            cards = driver.find_elements(By.CSS_SELECTOR, "div.product-card, article.product-card")
            print(f"Найдено {len(cards)} карточек товаров")
            
            # Парсим каждую карточку
            for card in cards:
                product_data = parse_product_card(card)
                if product_data:
                    all_products.append(product_data)
                    print(f"Добавлен: {product_data['brand']} {product_data['name']} - {product_data['price']} ₽ | {product_data['link']}")
            
            # Случайная задержка между страницами
            time.sleep(random.uniform(3, 6))
            
        except Exception as e:
            print(f"Ошибка при обработке страницы {page}: {str(e)[:200]}")
            continue
    
    return all_products

if __name__ == "__main__":
    driver = setup_driver()
    try:
        url = "https://www.wildberries.ru/catalog/elektronika/smartfony-i-telefony/vse-smartfony"
        products = parse_wb_category(driver, url, max_pages=3)
        
        print("\nИтоговые результаты:")
        for i, product in enumerate(products[:20], 1):
            print(f"{i}. {product['brand']} {product['name']} - {product['price']} ₽ | {product['link']}")
        
        # Сохраняем в CSV
        save_to_csv(products)
            
    finally:
        driver.quit()