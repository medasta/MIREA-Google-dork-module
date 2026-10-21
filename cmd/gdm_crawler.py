#from internal.crawlers.selenium_crawler import search_by_selenium
#from internal.crawlers.openserp_crawler import search_by_openserp
from internal.crawlers.requests_crawler import search_by_requests
from internal.crawlers.searxng_crawler import search_by_searxng

# Selenium crawler test
#selenium_test = search_by_selenium("internal/crawlers/geckodriver", "test", 120, 2)
#print(selenium_test)

"""openserp_test = search_by_openserp(
    url_limit=20,
    query="python",
    engines=["google", "yandex", "duckduckgo"],
    openserp_url="http://127.0.0.1:7001/mega/search",
    delay=2,
)

print(openserp_test)"""

# Requests crawler test
requests_test = search_by_requests(
    query="python",
    url_limit=20,
    static_url="https://html.duckduckgo.com/html/",
    delay=2,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    },
)
print(requests_test)


# SearXNG crawler test
searxng_test = search_by_searxng(
    url_limit=20,
    query="python",
    engines=["google", "yandex", "duckduckgo"],
    delay=2,
    searxng_url="http://127.0.0.1:8080/search",
)
print(searxng_test)