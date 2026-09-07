# dns-parser

Распределённый парсер карточек товаров dns-shop.ru: браузерные воркеры (Camoufox/Playwright) за ротацией прокси, очередь задач на Redis, оркестрация через Docker Compose.

## Компоненты

- **worker** (`server/worker`) — забирает URL из очереди Redis (`tasks`), открывает страницу через Camoufox с прокси, парсит карточку товара и кладёт результат обратно в Redis (`result:<url>`). Возвращает задачу в очередь при ошибке.
- **proxy-giver** (`server/proxy-giver`) — простой FastAPI-сервис, раздаёт прокси воркерам по кругу (`GET /get-random-proxy`) и принимает управление списком прокси (`POST /add-proxy`, `/remove-proxy`, `/remove-all-proxies`).
- **redis** — очередь задач + временное хранилище результатов.
- **cli** (`cli/`) — скрипты для постановки задач и выгрузки результатов в CSV.

## Запуск сервера

Требуется Docker и Docker Compose.

```bash
cd server
docker compose -f compose.yaml up -d --build      # прод: 3 реплики воркера
# либо для разработки (код монтируется как volume):
docker compose -f compose.dev.yaml up -d --build
```

Проверьте порты в `compose.yaml` / `compose.dev.yaml` — прод-конфиг публикует `proxy-giver` на `9001`, dev-конфиг — на `9000`.

## Использование CLI

1. В `cli/script.py` укажите `HOST` — адрес машины, где поднят сервер.
2. Список ссылок для парсинга — по одной в файл `cli/dns.txt`.
3. При необходимости пропишите список прокси в `main()` (`cli/script.py`).
4. Запустите:

```bash
cd cli
pip install redis requests
python script.py
```

Результат сохранится в `data.csv`. Каждый запуск сам чистит очередь Redis и все зависшие `result:*` ключи от прошлых прерванных запусков — старые данные по повторно используемым ссылкам не подмешаются.

## Статус

Проект в раннем состоянии (beta).
