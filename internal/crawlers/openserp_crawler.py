import requests
import time
from typing import Any

from internal.utils.logger import get_logger

logger = get_logger(__name__)

# make_query принимает объект сессии, поисковый запрос, список поисковых
# движков, смещение относительно результатов и URL OpenSERP.
# Выполняет HTTP-запрос и возвращает ответ в виде словаря.
def make_query(
    session: requests.Session,
    query: str,
    engines: list[str],
    start: int,
    openserp_url: str,
) -> dict[str, Any]:
    params: dict[str, str | int] = {
        "text": query,
        "engines": ",".join(engines),
        "limit": 10,
        "start": start,
    }

    logger.info("Making OpenSERP request. start: %d", start)

    try:
        response = session.get(openserp_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        logger.exception("OpenSERP request failed")
        raise
    except ValueError:
        logger.exception("Failed to decode OpenSERP response as JSON")
        raise

# extract_results принимает ответ OpenSERP и извлекает из него
# прямые ссылки на найденные сайты.
# Возвращает список URL в виде строк.
def extract_results(response: dict[str, Any]) -> list[str]:
    urls: list[str] = []

    results = response.get("results", [])

    for result in results:
        url = result.get("url")

        if isinstance(url, str) and url:
            urls.append(url)

    return urls

# search_by_openserp принимает лимит количества URL, поисковый запрос,
# список поисковых движков, URL сервиса OpenSERP и задержку между запросами.
# Последовательно получает страницы поисковой выдачи, собирает уникальные
# ссылки и прекращает поиск при достижении лимита или отсутствии результатов.
# Возвращает множество уникальных URL.
def search_by_openserp(
    url_limit: int,
    query: str,
    engines: list[str],
    openserp_url: str,
    delay: int,
) -> set[str]:
    if not query or not engines or not openserp_url or url_limit < 1 or delay < 1:
        logger.error("Invalid input arguments")
        return set()

    urls: set[str] = set()
    start = 0

    logger.info("Starting OpenSERP search for query: %s", query)

    with requests.Session() as session:
        while len(urls) < url_limit:
            response = make_query(
                session,
                query,
                engines,
                start,
                openserp_url,
            )

            current_urls = extract_results(response)

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

            pagination = response.get("pagination", {})

            if not pagination.get("has_more"):
                logger.info("No more OpenSERP results available")
                break

            next_start = pagination.get("next_start")

            if not isinstance(next_start, int):
                logger.warning("OpenSERP pagination has no valid next_start value")
                break

            start = next_start
            time.sleep(delay)

    logger.info("OpenSERP session closed")

    return urls