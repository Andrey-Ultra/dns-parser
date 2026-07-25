import json
import os
import re
import time

import browser_task
import data_parser as dp
from loguru import logger
import redis
import requests

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
PROXY_GIVER_HOST = os.getenv("PROXY_GIVER_HOST", "localhost")
r = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True,
    socket_timeout=None,            # Отключаем тайм-аут на чтение/запись сокета
    socket_connect_timeout=None,    # Отключаем тайм-аут на подключение
    health_check_interval=30        # Каждые 30 сек проверяет, жива ли связь
)


def parse_proxy(proxy_str: str) -> dict:
    pattern = r"([\d\.]+):(\d+):([^:]+):([^:\s]+)"
    match = re.search(pattern, proxy_str.strip())

    ip, port, username, password = match.groups()

    return {
        "server": f"{ip}:{port}",
        "username": username,
        "password": password
    }


def do_task(proxy, url):
    proxy_config = parse_proxy(proxy)

    try:
        html = browser_task.start_task(proxy_config, url)
    except Exception as e:
        logger.exception("Ошибка во время скролинга")
        return None

    # Парсит html
    try:
        ans = dp.get_product_data(html)
    except Exception as e:
        logger.exception("Ошибка во время парсинга html")
        return None

    return ans

def get_proxy_from_api() -> str | None:
    url = f"http://{PROXY_GIVER_HOST}:9000/get-random-proxy"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            return data.get("proxy")
        else:
            logger.error(f"API proxy-giver вернул ошибку: {data}")
            return None

    except Exception as e:
        logger.error(f"Не удалось связаться с API proxy-giver: {e}")
        return None


def main():
    logger.info("Воркер ожидает задачу")
    while True:

        _, url = r.brpop("tasks", timeout=0)
        proxy = get_proxy_from_api()

        if not proxy:
            logger.warning(f"Нет доступного прокси. Возвращаем задачу {url} в очередь.")
            r.rpush("tasks", url)
            time.sleep(5)
            continue

        logger.info(f"Используем прокси {proxy} для задачи {url}")

        ans = None
        try:
            ans = do_task(proxy, url)
        except Exception as e:
            logger.error(f"Ошибка {e}")
            ans = None

        if ans is None:
            logger.warning(f"Задача {url} не выполнена. Возвращаем в очередь.")
            r.rpush("tasks", url)
            time.sleep(2)
            continue

        # Сохраняем результат
        r.set(f"result:{url}", json.dumps(ans, ensure_ascii=False))
        logger.info(f"Успешно завершено: {url}")



if __name__ == "__main__":
    main()