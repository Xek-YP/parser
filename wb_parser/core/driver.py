import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Browser:
    def __init__(self):
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def _setup_driver(self):
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

    def accept_cookies(self):
        """Принятие cookies"""
        try:
            accept_texts = [
                'Принять', 'Принять все', 'Принять cookies', 
                'Ок', 'Окей', 'OK', 'Okay',
                'Согласен', 'Согласиться', 'Я согласен',
                'Accept', 'Accept all', 'Accept cookies',
                'Agree', 'I agree', 'Consent', 'Allow'
            ]
            
            xpath_expression = "//button[" + " or ".join(f"contains(., '{text}')" for text in accept_texts) + "]"
            
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath_expression))
            ).click()
        except Exception as e:
            print(f"Не удалось найти кнопку принятия cookies: {e}")

    def scroll_page(self, scroll_pause=1):
        """Прокрутка страницы"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def close(self):
        """Закрытие браузера"""
        self.driver.quit()