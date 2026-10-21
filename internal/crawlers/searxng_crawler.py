import requests
import time
from typing import Any

from internal.utils.logger import get_logger

logger = get_logger(__name__)


# fetch принимает объект сессии, номер страницы, поисковый запрос,
# список поисковых движков и URL SearXNG.
# Выполняет поисковый запрос и возвращает результаты в виде списка словарей.
def fetch(
    session: requests.Session,
    page: int,
    query: str,
    engines: list[str],
    searxng_url: str,
) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {
        "q": query,
        "format": "json",
        "pageno": page,
        "language": "all",
        "categories": "general",
        "safesearch": 0,
        "engines": ",".join(engines),
    }

    logger.info("Fetching SearXNG results. Page: %d", page)

    try:
        response = session.get(
            searxng_url,
            params=params,
            timeout=45,
        )
        response.raise_for_status()

        data: Any = response.json()

        if not isinstance(data, dict):
            logger.warning("Unexpected SearXNG response format")
            return []

        results = data.get("results", [])

        if not isinstance(results, list):
            logger.warning("Invalid results field in SearXNG response")
            return []

        return [
            result
            for result in results
            if isinstance(result, dict)
        ]

    except requests.RequestException:
        logger.exception("SearXNG request failed")
        raise
    except ValueError:
        logger.exception("Failed to decode SearXNG response as JSON")
        raise


# get_urls принимает результаты SearXNG и извлекает из них
# прямые ссылки на найденные сайты.
# Возвращает множество уникальных URL.
def get_urls(results: list[dict[str, Any]]) -> set[str]:
    urls: set[str] = set()

    for result in results:
        url = result.get("url")

        if isinstance(url, str) and url:
            urls.add(url)

    return urls


# search_by_searxng принимает на вход:
# url_limit - лимит количества результатов
# query - поисковый запрос
# engines - список поисковых движков SearXNG
# delay - задержка между запросами страниц
# searxng_url - URL сервиса SearXNG
# Последовательно получает страницы выдачи и собирает уникальные URL.
# Возвращает множество прямых ссылок на сайты.
def search_by_searxng(
    url_limit: int,
    query: str,
    engines: list[str],
    delay: int,
    searxng_url: str,
) -> set[str]:
    if (
        url_limit < 1
        or not query
        or not engines
        or delay < 1
        or not searxng_url
    ):
        logger.error("Invalid input arguments")
        return set()

    urls: set[str] = set()
    page = 1

    logger.info("Starting SearXNG search for query: %s", query)

    with requests.Session() as session:
        try:
            while len(urls) < url_limit:
                results = fetch(
                    session,
                    page,
                    query,
                    engines,
                    searxng_url,
                )

                if not results:
                    logger.info(
                        "No results returned. Stopping SearXNG search"
                    )
                    break

                current_urls = get_urls(results)

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

                page += 1
                time.sleep(delay)

        except requests.RequestException:
            logger.exception("SearXNG search failed")
        except ValueError:
            logger.exception("Invalid SearXNG response")

    logger.info(
        "SearXNG search finished. Total unique URLs: %d",
        len(urls),
    )

    return urls