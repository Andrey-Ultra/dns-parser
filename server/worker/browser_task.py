import random
import time
from camoufox.sync_api import Camoufox
from loguru import logger


def change_city(page):
    logger.info("Старт выбора города")
    page.goto("https://www.dns-shop.ru")

    # шаг 1: клик "сменить город"
    change_city_btn = page.get_by_text("сменить город", exact=False)
    change_city_btn.wait_for(timeout=15000)
    time.sleep(random.uniform(0.8, 2.0))
    change_city_btn.click()

    # шаг 2: ждём поле поиска города
    search_input = page.get_by_placeholder("Найти город", exact=False)
    search_input.wait_for(timeout=10000)
    time.sleep(random.uniform(0.5, 1.5))

    # шаг 3: вводим город по буквам (человекоподобно, не вставкой целиком)
    search_input.click()
    search_input.type("Александров", delay=random.randint(80, 200))  # delay — мс между буквами

    # шаг 4: ждём подсказку в выпадающем списке и кликаем по ней
    time.sleep(random.uniform(0.8, 1.5))
    city_option = page.get_by_text("Александров", exact=False).first
    city_option.wait_for(timeout=10000)
    city_option.click()

    # шаг 5: ждём, пока сайт сам завершит перезагрузку/редирект после смены города
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(random.uniform(1.0, 2.0))

    logger.info("Город выбран")


def human_mouse_wander(page):
    """Двигает мышь по случайной кривой траектории в случайную точку экрана."""
    viewport = page.viewport_size
    width, height = viewport["width"], viewport["height"]

    target_x = random.randint(50, width - 50)
    target_y = random.randint(50, height - 50)

    steps = random.randint(2, 5)  # было 5-15 — сильно сократили
    page.mouse.move(target_x, target_y, steps=steps)


# todo хот фикс не мой стоит провреить
def human_scroll_to_bottom(page, stall_timeout=90):
    """stall_timeout — сколько секунд БЕЗ прогресса терпим, прежде чем сдаться."""
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    page.bring_to_front()

    last_height = page.evaluate("document.body.scrollHeight")
    last_progress_time = time.time()
    no_change = 0
    iterations_since_wander = 0
    iterations_since_focus = 0

    while True:
        if random.random() < 0.06:
            page.mouse.wheel(0, -random.randint(80, 200))
            time.sleep(random.uniform(0.05, 0.15))

        page.mouse.wheel(0, random.randint(150, 350))

        if random.random() < 0.15:
            time.sleep(random.uniform(0.15, 0.3))
        else:
            time.sleep(random.uniform(0.04, 0.1))

        iterations_since_focus += 1
        if iterations_since_focus > 20:
            page.bring_to_front()
            iterations_since_focus = 0

        iterations_since_wander += 1
        if iterations_since_wander > 15 and random.random() < 0.03:
            human_mouse_wander(page)
            time.sleep(random.uniform(0.1, 0.3))
            iterations_since_wander = 0

        if random.random() < 0.04:
            time.sleep(random.uniform(0.5, 1.2))

        new_height = page.evaluate("document.body.scrollHeight")

        if new_height - last_height <= 15:
            no_change += 1
        else:
            no_change = 0
            last_progress_time = time.time()  # реальный прогресс — сбрасываем таймер
            time.sleep(random.uniform(0.8, 1.5))

        if no_change == 15:
            break

        # ключевая защита — если реального прогресса нет дольше stall_timeout секунд, сдаёмся
        if time.time() - last_progress_time > stall_timeout:
            raise TimeoutError(f"Скролл завис: нет прогресса дольше {stall_timeout} сек")

        logger.info(f"Прокрутка страницы: {last_height} -> {new_height}")
        last_height = new_height

def get_catalog_page(page, url):
    logger.info("Старт прокрутки каталога")

    page.goto(url + "?mode=tile", wait_until="domcontentloaded", timeout=30000)
    page.evaluate("document.body.style.zoom = '0.25'")
    human_scroll_to_bottom(page)

    logger.info("Прокрутка завершена")

    return page.content()


def start_task(proxy_config, url):
    with Camoufox(
            headless="virtual",
            proxy=proxy_config,
            geoip=True,
            humanize=True,
            firefox_user_prefs={
                "permissions.default.image": 2,
                "dom.timeout.enable_budget_timer_throttling": False,  # отключает саму budget-throttling систему
                "dom.min_background_timeout_value": 4,
                # минимальная задержка для фоновых таймеров (мс), как у активной вкладки
                "dom.suspend_inactive.enabled": False,  # не "усыплять" неактивные документы вообще
            }
    ) as browser:
        # 1. Глушим на уровне браузера/контекста
        context = browser.new_context()
        context.on("pageerror", lambda exc: None)

        # 2. Глушим на уровне страницы
        page = context.new_page()
        page.on("pageerror", lambda exc: None)

        change_city(page)

        html = get_catalog_page(page, url)

        return html


