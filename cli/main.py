import redis
import requests

HOST = "192.168.11.90"
BASE_URL = f"http://{HOST}:9000"
RED = redis.Redis(host=HOST, port=6379, decode_responses=True)
QNAME = "tasks"


def add_proxy(proxy: str):
    # todo проверка коректности
    response = requests.post(
        f"{BASE_URL}/add-proxy",
        params={"proxy": proxy}
    )


def remove_proxy(proxy: str):
    response = requests.post(
        f"{BASE_URL}/remove-proxy",
        params={"proxy": proxy}
    )


def all_proxies():
    response = requests.get(f"{BASE_URL}/get-all-proxies")
    data = response.json()
    if data["count"] == 0:
        print("No proxies found")
    else:
        for proxy in data["proxies"]:
            print(f"{proxy}")


def proxy_command(command):
    match command[0]:
        case "add":
            add_proxy(command[1])
        case "rm":
            remove_proxy(command[1])
        case "all":
            all_proxies()

    main()


def add_task(url: str):
    RED.lpush("tasks", url)


def get_result(url: str):
    return RED.get(f"result:{url}")


def main():
    command = input(">>> ").split()

    match command[0]:
        case "proxy":
            proxy_command(command[1:])
        case "parse":
            pass


def TEST():
    url = "https://www.dns-shop.ru/catalog/17a88f2816404e77/antivirusy/"

    # add_task(url)
    # queue_length = RED.llen(QNAME)
    # print(f"📊 Текущий размер очереди '{QNAME}': {queue_length}")
    #
    result = get_result(url)

    print("Результат получен!")
    print(result)


if __name__ == "__main__":
    TEST()

    # print("==================")
    # print(" CLI - dns-parser ")
    # print("==================")
    #
    # main()
