import random
import sys
import time
import types
from pathlib import Path


def _ensure_distutils():
    """Python 3.13 убрал distutils, а undetected-chromedriver всё ещё его импортирует."""
    try:
        from distutils.version import LooseVersion  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    class LooseVersion:
        def __init__(self, vstring):
            if isinstance(vstring, bytes):
                vstring = vstring.decode()
            self.vstring = str(vstring)
            parts = []
            for chunk in self.vstring.replace("-", ".").split("."):
                number = ""
                for char in chunk:
                    if char.isdigit():
                        number += char
                    else:
                        break
                if number:
                    parts.append(int(number))
            self.version = parts

        def __str__(self):
            return self.vstring

    distutils_mod = types.ModuleType("distutils")
    version_mod = types.ModuleType("distutils.version")
    version_mod.LooseVersion = LooseVersion
    distutils_mod.version = version_mod
    sys.modules["distutils"] = distutils_mod
    sys.modules["distutils.version"] = version_mod


_ensure_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PROFILE_DIR = Path(__file__).resolve().parents[2] / "output" / "chrome_profile"

BLOCK_MARKERS = (
    "подозрительная активность",
    "подозрительной активности",
    "доступ ограничен",
    "подтвердите, что вы не робот",
    "вы робот",
)


class Browser:
    def __init__(self):
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 20)

    def _chrome_major_version(self):
        """Мажорная версия установленного Chrome, чтобы драйвер ей соответствовал."""
        app_dir = Path(r"C:\Program Files\Google\Chrome\Application")
        versions = []
        if app_dir.exists():
            for child in app_dir.iterdir():
                if child.is_dir() and child.name[:1].isdigit():
                    versions.append(int(child.name.split(".", 1)[0]))
        return max(versions) if versions else None

    def _setup_driver(self):
        """Обычный Chrome без признаков автоматизации Selenium."""
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

        options = uc.ChromeOptions()
        options.add_argument("--lang=ru-RU")
        options.add_argument("--start-maximized")

        kwargs = {
            "options": options,
            "user_data_dir": str(PROFILE_DIR),
            "use_subprocess": True,
        }
        major = self._chrome_major_version()
        if major:
            kwargs["version_main"] = major

        driver = uc.Chrome(**kwargs)
        driver.set_page_load_timeout(60)
        return driver

    def accept_cookies(self):
        """Принятие cookies. Короткий таймаут и только тексты баннера, без «Ок»."""
        try:
            xpath_expression = (
                "//button[contains(., 'Принять') or contains(., 'Согласен') "
                "or contains(., 'Accept') or contains(., 'Agree')]"
            )
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath_expression))
            ).click()
            time.sleep(random.uniform(0.4, 1))
        except Exception:
            pass

    def is_blocked(self) -> bool:
        """Страница антибота Wildberries вместо каталога."""
        try:
            text = (self.driver.page_source or "").lower()
        except Exception:
            return False
        return any(marker in text for marker in BLOCK_MARKERS)

    def wait_if_blocked(self, timeout: int = 120) -> bool:
        """Даёт пройти проверку вручную в открытом окне Chrome."""
        if not self.is_blocked():
            return False

        print(
            "Wildberries показал проверку на подозрительную активность. "
            "Если в окне Chrome есть кнопка или капча, пройдите её вручную. "
            f"Жду до {timeout} секунд."
        )
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(2)
            if not self.is_blocked():
                print("Проверка пройдена, продолжаю сбор.")
                time.sleep(random.uniform(1, 2))
                return True

        print("Проверка так и не исчезла, карточки с этой страницы не собрать.")
        return False

    def scroll_page(self, scroll_pause=0.5, max_seconds=20):
        """Плавная прокрутка. Дольше max_seconds не идём: собираем уже загруженное."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        current = 0
        idle_rounds = 0
        deadline = time.time() + max_seconds

        while idle_rounds < 2:
            if time.time() >= deadline:
                print(f"Прокрутка дольше {max_seconds} секунд, собираю уже загруженные карточки.")
                break

            step = random.randint(350, 800)
            current = min(current + step, last_height)
            self.driver.execute_script("window.scrollTo(0, arguments[0]);", current)
            time.sleep(random.uniform(scroll_pause, scroll_pause + 0.7))

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if current >= last_height and new_height <= last_height:
                idle_rounds += 1
            else:
                idle_rounds = 0
            last_height = new_height

    def close(self):
        """Закрытие браузера."""
        try:
            self.driver.quit()
        except Exception:
            pass
