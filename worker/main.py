import json
import os
import re
import time

import browser_task
import data_parser as dp
import requests
from loguru import logger
from stm import ServerError, Worker


# ------------ CONFIG ------------

STM_URL = os.getenv("STM_URL", "http://localhost:8080")
PROXY_GIVER_URL = os.getenv("PROXY_GIVER_URL", "http://localhost:9001")

URL_PREF = "&shop-catalog=2265"


# ------------ PROXY ------------

def parse_proxy(proxy_str: str) -> dict:
    pattern = r"([\d\.]+):(\d+):([^:]+):([^:\s]+)"
    match = re.search(pattern, proxy_str.strip())

    ip, port, username, password = match.groups()

    return {
        "server": f"{ip}:{port}",
        "username": username,
        "password": password
    }

def get_proxy_from_api() -> str | None:
    try:
        response = requests.get(f"{PROXY_GIVER_URL}/get-random-proxy", timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Не удалось связаться с proxy-giver: {e}")
        return None

    if data.get("status") != "success":
        logger.warning("Список прокси пуст, добавьте прокси в панели")
        return None
    return data["proxy"]


# ------------ TASK ------------

def handle(url: str, proxy: str) -> list[dict]:
    url += URL_PREF
    html = browser_task.start_task(parse_proxy(proxy), url)
    return dp.get_product_data(html)


def main():
    worker = Worker(STM_URL)
    logger.info(f"Воркер запущен. Очередь: {STM_URL}, прокси: {PROXY_GIVER_URL}")

    while True:
        try:
            job = worker.take()
        except ServerError as e:
            logger.warning(f"Очередь недоступна: {e}")
            time.sleep(5)
            continue
        if job is None:
            time.sleep(1)
            continue

        proxy = get_proxy_from_api()
        if proxy is None:
            worker.release(job.id)
            time.sleep(5)
            continue

        logger.info(f"Взял задачу {job.task} (прокси {proxy.split(':')[0]})")
        try:
            products = handle(job.task, proxy)
        except Exception:
            logger.exception(f"Ошибка задачи {job.task}, возвращаю в очередь")
            worker.release(job.id)
            continue

        if worker.answer(job.id, json.dumps(products, ensure_ascii=False)):
            logger.info(f"Готово: {len(products)} товаров")
        else:
            logger.warning("Ответ не принят: задачу отменили или истёк TASK_TIMEOUT")


if __name__ == "__main__":
    main()
