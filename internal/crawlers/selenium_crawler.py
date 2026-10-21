from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
import time

from internal.utils.logger import get_logger

logger = get_logger(__name__)

# create_firefox_webdriver создает и возвращает объект firefox браузера, созданный
# Selenium, принимая на вход путь до geckodriver.
def create_firefox_webdriver(geckodriver_path: str) -> webdriver.Firefox | None:
    logger.info("Creating Firefox webdriver")
    try:
        service = Service(geckodriver_path)
        driver = webdriver.Firefox(service=service)
        return driver
    except WebDriverException:
        logger.exception("Failed to create Firefox driver")
        return None

# make_query_button_click принимает на вход объект браузера и
# поисковой запрос, осуществляя переход на первую страницу поисковой
# выдачи при нажатии на кнопку поиска
def make_query_button_click(driver: webdriver.Firefox, query: str) -> None:
    logger.info("Submitting search query: %s", query)
    try:
        driver.get("https://html.duckduckgo.com/html/")
        driver.find_element(By.ID, "search_form_input_homepage").send_keys(query)
        driver.find_element(By.ID, "search_button_homepage").click()
    except WebDriverException:
        logger.exception("Failed to submit search query")
        raise


# more_results_button_click имея объект браузера пытается получить следующую
# страницу поисковой выдачи, нажимая на кнопку внизу страницы ("Next")
def more_results_button_click(driver: webdriver.Firefox) -> bool:
    try:
        driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Next"]').click()
        return True
    except NoSuchElementException:
        logger.info('Button "Next" not found')
        return False

# extract_results принимает на вход объект браузера. Используя
# объект браузера, функция извлекает все css атрибуты a.result__url,
# внутри которых находятся ссылки, ведущие на сайты
def extract_results(driver: webdriver.Firefox) -> list[str]:
    links = driver.find_elements(By.CSS_SELECTOR, "a.result__url")

    return [url for link in links if (url := link.get_attribute("href")) is not None]

# search_by_selenium принимает на вход:
# driver_path - путь до gecko драйвера
# query - поисковой запрос
# url_limit - лимит по количеству результатов
# delay - задержка между переходами по страницам
# Возвращает множество, содержащее в себе прямые ссылки на сайты.
def search_by_selenium(driver_path: str, query: str, url_limit: int, delay: int) -> set[str]:
    if not query or url_limit < 1 or delay < 1:
        logger.error("Invalid input arguments")
        return set()
    
    urls: set[str] = set()
    driver = create_firefox_webdriver(driver_path)

    if driver is None:
        logger.error("Cannot start Selenium search: driver was not created")
        return urls

    try:
        make_query_button_click(driver, query)

        while len(urls) < url_limit:
            current_urls = extract_results(driver)

            for url in current_urls:
                urls.add(url)

                if len(urls) >= url_limit:
                    break

            logger.info("Unique results collected: %d/%d", len(urls), url_limit)

            if len(urls) >= url_limit:
                break

            if not more_results_button_click(driver):
                logger.info(
                    "Next page button not found. "
                    "Stopping Selenium search"
                )
                break

            time.sleep(delay)

    finally:
        try:
            driver.quit()
            logger.info("Selenium browser closed")
        except WebDriverException:
            logger.exception("Failed to close Selenium browser")

    return urls