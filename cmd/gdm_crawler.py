from internal.crawlers.selenium_crawler import search_by_selenium

# Selenium crawler test
selenium_test = search_by_selenium("internal/crawlers/geckodriver", "test", 120, 2)
print(selenium_test)