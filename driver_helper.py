from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import logger
import consts


class DriverHelper:

    def __init__(self):
        self.driver = None

    def get_chrome_driver(self, path):
        """ returns a chrome driver """

        chrome_options = Options()
        # chrome_options.add_argument("headless")
        # chrome_options.add_argument("--window-size=1920x1080")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


    def find_element_by_xpath(self, xpath, wait=True):
        """ find the required element (single) by xpath and wait for it to load """

        if wait:
            return WebDriverWait(self.driver, consts.WEB_DRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
        else:
            return self.driver.find_element_by_xpath(xpath)


    def find_elements_by_xpath(self, xpath, wait=True):
        """ find the required elements (multiple) by xpath and wait for them to load """

        if wait:
            WebDriverWait(self.driver, consts.WEB_DRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
        return self.driver.find_elements_by_xpath(xpath)


    def xpath_by_idx(self, xpath, idx):
        """ returns the xpath of the wanted element in the by the index parameter """

        return "({})[{}]".format(xpath, str(idx + 1))  # note: xpath arr starts from 1


    def try_click(self, url, element, cnt_try=consts.CNT_TRY):
        """ try click cnt_try times to try avoid losing data """

        try:
            element.click()

        except Exception as e:
            if cnt_try > 0:
                self.try_click(url, element, cnt_try-1)
            else:
                raise e


    def go_back(self, url):
        """ go back to the previous page """

        try:
            # driver.execute_script("window.history.go(-1)")
            # driver.back()
            self.driver.get(url)

        except Exception as e:
            logger.warning(f"Failed go back (-1) in history, exception: {e}. Reloading")
            self.driver.get(url)
