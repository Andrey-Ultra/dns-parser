import random
import time

from camoufox.sync_api import Camoufox
from loguru import logger

# кука выбора города (Александров), подставляется до захода на страницу
CURRENT_PATH = (
    "183b715ed6996bef513acabd9d1eb9912b9e5050626fb358acda9fcad1b366aca%3A2%3A%7Bi%3A0%3Bs%3A12%3A%22current_path%22"
    "%3Bi%3A1%3Bs%3A145%3A%22%7B%22city%22%3A%224eb13f45-5ca9-11e2-b5f7-001517c5631c%22%2C%22cityName%22%3A%22"
    "%5Cu0410%5Cu043b%5Cu0435%5Cu043a%5Cu0441%5Cu0430%5Cu043d%5Cu0434%5Cu0440%5Cu043e%5Cu0432%22%2C%22method%22"
    "%3A%22manual%22%7D%22%3B%7D"
)


def scroll_to_bottom(page, timeout=600, max_idle=15):
    """Крутит колесо, пока высота страницы не перестанет расти max_idle шагов подряд."""
    page.bring_to_front()
    best = page.evaluate("document.body.scrollHeight")
    idle = 0
    deadline = time.time() + timeout

    while idle < max_idle:
        if time.time() > deadline:
            raise TimeoutError(f"Скролл не завершился за {timeout} сек")

        page.mouse.wheel(0, random.randint(150, 350))
        time.sleep(random.uniform(0.05, 0.15))

        height = page.evaluate("document.body.scrollHeight")
        if height > best + 15:
            best, idle = height, 0
            logger.info(f"Высота страницы: {best}")
            time.sleep(random.uniform(0.8, 1.5))  # даём подгрузиться новым карточкам
        else:
            idle += 1


def start_task(proxy_config, url):
    with Camoufox(
            headless="virtual",
            proxy=proxy_config,
            geoip=True,
            humanize=True,
            firefox_user_prefs={
                "permissions.default.image": 2,
                # не душим таймеры и не усыпляем документ, даже если вкладка не в фокусе
                "dom.timeout.enable_budget_timer_throttling": False,
                "dom.min_background_timeout_value": 4,
                "dom.suspend_inactive.enabled": False,
            }
    ) as browser:
        context = browser.new_context()
        context.add_cookies([{
            "name": "current_path",
            "value": CURRENT_PATH,
            "domain": ".dns-shop.ru",
            "path": "/",
        }])
        page = context.new_page()

        page.goto(url + "?shop-catalog=2265&mode=tile", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".catalog-product", timeout=30000)  # ждём реальный каталог, а не заглушку
        page.evaluate("document.body.style.zoom = '0.25'")  # мелкий масштаб — больше карточек в экране

        scroll_to_bottom(page)
        return page.content()
