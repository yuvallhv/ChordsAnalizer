

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pdb


# consts
import logger

CHROME_DRIVER_PATH = "../chromedriver"
WEB_DRIVER_WAIT_TIME = 20
CNT_TRY = 4



def get_chrome_driver(path):
    chrome_options = Options()
    # chrome_options.add_argument("headless")
    chrome_options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(options=chrome_options, executable_path=path)


def get_clickable_element(driver, xpath, idx):
    """ wait for the web element to be clickable (page need to finish loading) """

    xpath_by_idx = "({})[{}]".format(xpath, str(idx + 1))  # note: xpath arr starts from 1
    return WebDriverWait(driver, WEB_DRIVER_WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, xpath_by_idx)))


def try_click(element, cnt_try=CNT_TRY):
    """ try click cnt_try times to try avoid losing data """

    try:
        element.click()

    except Exception as e:
        if cnt_try > 0:
            try_click(element, cnt_try-1)
        else:
            raise e


def get_songs_data(driver, url):

    next_page_nav_xpath = "//div[@class='pagination row']"
    songs_data_dict = {}

    # check if there are multiple pages
    try:
        driver.find_element_by_xpath(next_page_nav_xpath)
        return get_songs_data_multiple_page(driver, url, songs_data_dict)

    except NoSuchElementException as e:
        return get_songs_data_single_page(driver, url, songs_data_dict)


    # TODO: dump dict to disk (create a json file)


def get_songs_data_multiple_page(driver, url, songs_data_dict):

    next_page_str = "עמוד הבא"
    next_page_a_xpath = "//a[@class='nextPre']"

    # get current page songs data
    get_songs_data_single_page(driver, url, songs_data_dict)

    # check for more pages for this artist
    WebDriverWait(driver, WEB_DRIVER_WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, next_page_a_xpath)))
    next_page_a_element = driver.find_elements_by_xpath(next_page_a_xpath)[0]
    next_page_a_text = next_page_a_element.text

    if next_page_str in next_page_a_text:
        try:
            logger.log("clicking on the next page for this artist")
            try_click(next_page_a_element)
            get_songs_data_multiple_page(driver, url, songs_data_dict)

        except Exception as e:
            logger.warning("Failed to go to the next page")
            driver.get(url)

    return songs_data_dict


def get_songs_data_single_page(driver, url, songs_data_dict):
    """ returns a dictionary of songs and their data dictionaries  """
    # TODO: change data structure

    songs_xpath = "//td[@class='song']"
    songs_a_xpath = "//td[@class='song']/a"

    songs_elements = driver.find_elements_by_xpath(songs_xpath)

    song_href = ""  # needed for warning msg in case of failure
    song_name = ""  # needed for warning msg in case of failure

    # click to enter song's page and get it's data dictionary
    for idx, _ in enumerate(songs_elements):

        try:
            song_a_element = get_clickable_element(driver, songs_a_xpath, idx)

            # get song's name
            song_name = song_a_element.text

            # get the link to the song's page and move to the page
            song_href = song_a_element.get_attribute('href')
            try_click(song_a_element)

            # get song's chords and words data
            chords_dict = get_song_chords(driver)
            songs_data_dict[song_name] = chords_dict

            logger.log(f"parsed song {(idx+1)} for this page; name: {song_name}, href: {song_href}")

            # go back to the previous page, (driver.back() might cause weird behavior)
            driver.execute_script("window.history.go(-1)")

        except Exception as e:
            logger.warning(f"Failed to parse a song, song href: {song_href}, song text: {song_name}, exception: {e}")
            driver.get(url)

    return songs_data_dict


def get_artists_data(driver):
    """ returns artists data as string """
    # TODO: change data structure

    artist_data_xpath = "//div[@class='ArtistAndSongName']"
    artist_data = driver.find_elements_by_xpath(artist_data_xpath)[0].text

    return artist_data


def get_song_chords(driver):
    """ returns key, value. key=song name, value=chords dictionary """

    return "** tmp **"


def get_chords(driver):
    """ returns all chords in the page in a dictionary """

    return {}

    # # TODO: change


if __name__ == "__main__":
    driver = get_chrome_driver(CHROME_DRIVER_PATH)

    try:
        # url = "https://www.tab4u.com/tabs/artists/1723_%D7%A6%D7%9C%D7%99%D7%9C_%D7%93%D7%99%D7%99%D7%9F.html"

        url = "https://www.tab4u.com/tabs/artists/112_%D7%94%D7%A8%D7%90%D7%9C_%D7%A1%D7%A7%D7%A2%D7%AA.html"

        driver.get(url)
        print(get_songs_data(driver, url))

    finally:
        driver.close()
