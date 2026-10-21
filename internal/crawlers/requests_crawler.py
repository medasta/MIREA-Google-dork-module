import requests
from lxml import html
from lxml.html import HtmlElement
import time

from internal.utils.logger import get_logger

logger = get_logger(__name__)


# parse_results принимает страницу поисковой выдачи и извлекает из неё
# прямые ссылки на найденные сайты.
# Возвращает список URL в виде строк.
def parse_results(page: HtmlElement) -> list[str]:
    urls: list[str] = []

    result_blocks = page.xpath(
        "//div[contains(@class, 'result__body')]"
    )

    for block in result_blocks:
        url: list[str] = block.xpath(
            ".//h2[@class='result__title']"
            "//a[@class='result__a']/@href"
        )

        if url:
            urls.append(url[0].strip())

    return urls


# get_next_page принимает страницу поисковой выдачи и текущее смещение.
# Извлекает скрытые поля формы для перехода на следующую страницу.
# Возвращает словарь с параметрами или None, если следующая страница не найдена.
def get_next_page(
    page: HtmlElement,
    current_offset: int,
) -> dict[str, str] | None:
    forms = page.xpath("//div[contains(@class, 'nav-link')]/form")

    for form in forms:
        data: dict[str, str] = {}
        input_fields = form.xpath(".//input[@type='hidden']")

        for input_field in input_fields:
            name = input_field.get("name")
            value = input_field.get("value")

            if isinstance(name, str) and isinstance(value, str):
                data[name] = value

        next_offset = data.get("s")

        if next_offset is None:
            continue

        try:
            if int(next_offset) > current_offset:
                return data
        except ValueError:
            logger.warning("Invalid pagination offset: %s", next_offset)

    return None


# make_query принимает объект сессии, URL поисковой системы и параметры
# запроса. Отправляет POST-запрос и возвращает HTTP-ответ.
def make_query(
    session: requests.Session,
    static_url: str,
    data: dict[str, str],
) -> requests.Response:
    response = session.post(
        static_url,
        data=data,
        timeout=10,
    )
    response.raise_for_status()
    return response


# search_by_requests принимает на вход:
# query - поисковый запрос
# url_limit - лимит количества результатов
# static_url - URL поисковой системы
# delay - задержка между запросами страниц
# headers - HTTP-заголовки
# Собирает уникальные URL и прекращает поиск при достижении лимита
# или отсутствии следующих страниц.
# Возвращает множество прямых ссылок на сайты.
def search_by_requests(
    query: str,
    url_limit: int,
    static_url: str,
    delay: int,
    headers: dict[str, str],
) -> set[str]:
    if not query or not static_url or url_limit < 1 or delay < 1:
        logger.error("Invalid input arguments")
        return set()

    urls: set[str] = set()
    seen_pages: set[int] = set()
    current_offset = 0

    logger.info("Starting Requests search for query: %s", query)

    with requests.Session() as session:
        session.headers.update(headers)

        try:
            response = make_query(
                session,
                static_url,
                {"q": query},
            )

            if "challenge-form" in response.text:
                logger.warning("Search engine returned a challenge page")
                return urls

            while len(urls) < url_limit:
                page = html.fromstring(response.text)

                current_urls = parse_results(page)

                for url in current_urls:
                    urls.add(url)

                    if len(urls) >= url_limit:
                        break

                logger.info(
                    "Unique results collected: %d/%d",
                    len(urls),
                    url_limit,
                )

                if len(urls) >= url_limit:
                    break

                next_page = get_next_page(page, current_offset)

                if next_page is None:
                    logger.info(
                        "Next page not found. Stopping Requests search"
                    )
                    break

                next_offset_value = next_page.get("s")

                if next_offset_value is None:
                    logger.warning("Next-page offset is missing")
                    break

                try:
                    next_offset = int(next_offset_value)
                except ValueError:
                    logger.warning(
                        "Invalid next-page offset: %s",
                        next_offset_value,
                    )
                    break

                if next_offset in seen_pages:
                    logger.warning("Pagination loop detected")
                    break

                seen_pages.add(next_offset)
                current_offset = next_offset

                time.sleep(delay)

                response = make_query(
                    session,
                    static_url,
                    next_page,
                )

                if "challenge-form" in response.text:
                    logger.warning(
                        "Search engine returned a challenge page. "
                        "Stopping Requests search"
                    )
                    break

        except requests.RequestException:
            logger.exception("Requests search failed")

    logger.info(
        "Requests search finished. Total unique URLs: %d",
        len(urls),
    )

    return urls