import calendar
import datetime
import re
import json

from bs4 import BeautifulSoup
import lxml

class InvalidHtml(Exception):
    pass

def parse_delivery_days(st: str) -> int:
    """Оценить дни до наличия по строке доступности."""
    st = st or ""
    if 'Цифровая версия' in st: return 0
    if 'в 2 магазинах' in st or 'в 1 магазине' in st: return 0
    if 'автра' in st: return 1
    if 'послезавтра' in st: return 2
    if 'Товара нет в наличии' in st: return 30

    now = datetime.datetime.now()
    digits = ''.join(x for x in st if x.isdigit())
    if digits:
        day = int(digits)
        delta = day - now.day
        if delta < 0:
            mon_len = calendar.mdays[datetime.date.today().month]
            return mon_len + day - now.day
        return delta
    return 20  # дефолт


def get_product_data(html):
    soup = BeautifulSoup(html, "lxml")

    products = soup.find_all("div", class_="catalog-product")

    products_list = []

    for product in products:
        # =========== Артикул =============
        article = product.get("data-code")


        # ====== Название и описание ======
        title_el = product.find("a", class_="catalog-product__name")
        title_raw = title_el.get_text(" ", strip=True)
        name = title_raw
        description = ""
        m = re.match(r"(.+?)\s*\[(.+)\]$", title_raw)
        if m:
            name = m.group(1).strip()
            description = m.group(2).strip()

        # ============= Цена ==============
        price_el = product.find("div", class_="product-buy__price")
        if price_el:
            # Находим первый текстовый узел непосредственно внутри блока цены,
            # игнорируя вложенные теги вроде <span class="product-buy__prev">
            price_text = price_el.find(string=True, recursive=False)

            # Если по какой-то причине напрямую текст не нашелся, берем весь текст
            if not price_text:
                price_text = price_el.get_text(strip=True)

            price = int("".join(char for char in price_text if char.isdigit()))
        else:
            price = 0

        # ======== Дней доставки ==========
        target_el = product.find(class_=["digital-product-modal", "order-avail-wrap__link"])
        raw_text = target_el.get_text(" ", strip=True) if target_el else None
        delivery_days = parse_delivery_days(raw_text)

        product_item = {
            "product_id": int(article),
            "name": name,
            "description": description,
            "price": price,
            "delivery_days": delivery_days
        }

        products_list.append(product_item)


    print("Всего товаров", len(products_list))

    return products_list
