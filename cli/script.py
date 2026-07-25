import csv
import json
import time
from os import path
from pathlib import Path

import redis
import requests

HOST = "YOUR host"
BASE_URL = f"http://{HOST}:9000"
RED = redis.Redis(host=HOST, port=6379, decode_responses=True)
QNAME = "tasks"
DELIMITER = ";"


def use_proxy(proxies: list[str]):
    requests.post(f"{BASE_URL}/remove-all-proxies")

    for proxy in proxies:
        requests.post(
            f"{BASE_URL}/add-proxy",
            params={"proxy": proxy}
        )


def add_tasks(urls: list[str]):
    for url in urls:
        RED.lpush(QNAME, url)


def wait_finishing(urls: list[str]):
    print("Ожидаем выполнения всех задач...")
    expected_count = len(urls)

    while True:
        # Считаем, сколько ключей 'result:url' из нашего списка УЖЕ появилось в Redis
        completed_count = sum(1 for url in urls if RED.exists(f"result:{url}"))

        if completed_count == expected_count:
            print("Все результаты успешно записаны!")
            break

        print(f"Готово {completed_count} из {expected_count} задач...")
        time.sleep(10)


def get_result(urls: list[str]):
    combined_data = []

    for url in urls:
        key = f"result:{url}"
        raw_data = RED.get(key)
        parsed_list = json.loads(raw_data)
        combined_data.extend(parsed_list)

        RED.delete(key)

    return combined_data


def do_task(urls: list[str]):
    add_tasks(urls)
    wait_finishing(urls)
    return get_result(urls)


def save_results_to_csv(combined_data: list[dict], file_path: str | Path) -> Path:
    out_path = Path(file_path)

    if out_path.parent:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for item in combined_data:
        row = (
            item.get("product_id"),
            item.get("name"),
            item.get("price"),
            0,  # 4-я колонка: bonus (0 для соответствия оригиналу)
            item.get("delivery_days"),  # 5-я колонка: delivery_days
            item.get("description")  # 6-я колонка: description
        )
        rows.append(row)

    # csv.writer сам автоматически разставит кавычки там, где встречаются специсимволы
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=DELIMITER, lineterminator="\n")
        writer.writerows(rows)

    return out_path


def main():
    proxy = []
    # your proxy


    urls = []
    # your urls

    path = Path("dns.txt")
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            clean_url = line.strip()

            if clean_url:
                urls.append(clean_url)

    print(urls)

    use_proxy(proxy)
    ans = do_task(urls)

    save_results_to_csv(ans, "data.csv")


if __name__ == "__main__":
    main()
