

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

import consts
import logger
import pdb


def get_chrome_driver(path):
    chrome_options = Options()
    # chrome_options.add_argument("headless")
    chrome_options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(options=chrome_options, executable_path=path)


def find_element_by_xpath(driver, xpath):
    """ find the required element (single) by xpath and wait for it to load """
    return WebDriverWait(driver, consts.WEB_DRIVER_WAIT_TIME).until(
        EC.presence_of_element_located((By.XPATH, xpath)))
    # return driver.find_element_by_xpath(xpath)


def find_elements_by_xpath(driver, xpath):
    """ find the required elements (multiple) by xpath and wait for them to load """
    WebDriverWait(driver, consts.WEB_DRIVER_WAIT_TIME).until(
        EC.presence_of_element_located((By.XPATH, xpath)))
    return driver.find_elements_by_xpath(xpath)


def try_click(url, element, cnt_try=consts.CNT_TRY):
    """ try click cnt_try times to try avoid losing data """

    try:
        element.click()

    except Exception as e:
        if cnt_try > 0:
            try_click(url, element, cnt_try-1)
        else:
            raise e


def get_data_by_artist(driver, url, artist_name):
    """ returns a data dictionary of the artist's biography information and songs data """

    # get data
    data_by_artist_dict = {
        consts.SONGS_DATA: navigate_songs(driver, url),
        consts.ARTIST_DATA: get_artist_data(driver, url)
    }

    # dump to file by artist name
    try:
        file_name = f"json_files/{artist_name}.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data_by_artist_dict, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.warning(f"Failed to dump artist {artist_name} to json file, exception: {e}.")


def get_artist_data(driver, url):
    """ returns a dictionary of the artist's biography information """

    artist_bios_xpath = "//ul[@class='artist_block_bio']/li"
    artist_bio_dict = {}

    try:
        artist_bios_elements = find_elements_by_xpath(driver, artist_bios_xpath)

        for artist_bio_e in artist_bios_elements:

            if ": " in artist_bio_e.text:
                artist_bio = artist_bio_e.text.split(": ")
                artist_bio_dict[artist_bio[0]] = artist_bio[1]

        logger.log(f"parsed artist's biography:' {artist_bio_dict}")

        return artist_bio_dict

    except Exception as e:
        logger.warning(f"Failed to get the artist's biography information, exception: {e}. Reloading")
        driver.get(url)
        return artist_bio_dict


def navigate_songs(driver, url):
    """ returns a dictionary of songs and their data dictionaries, from all the pages for this artist """

    next_page_nav_xpath = "//div[@class='pagination row']"
    songs_data_dict = {}

    # check if there are multiple pages
    try:
        find_element_by_xpath(driver, next_page_nav_xpath)
        return navigate_songs_multiple_page(driver, url, songs_data_dict)

    except NoSuchElementException as e:
        return navigate_songs_single_page(driver, url, songs_data_dict)


def navigate_songs_multiple_page(driver, url, songs_data_dict):
    """ returns a dictionary of songs and their data dictionaries, from all the pages for this artist """

    next_page_str = "עמוד הבא"
    next_page_a_xpath = "//a[@class='nextPre'][1]"

    # get current page songs data
    navigate_songs_single_page(driver, url, songs_data_dict)

    try:
        # check for more pages for this artist
        next_page_a_element = find_element_by_xpath(driver, next_page_a_xpath)
        next_page_a_text = next_page_a_element.text

        if next_page_str in next_page_a_text:
            try:
                logger.log("clicking on the next page for this artist")
                try_click(url, next_page_a_element)
                url = driver.current_url
                navigate_songs_multiple_page(driver, url, songs_data_dict)

            except Exception as e:
                logger.warning(f"Failed to go to the next page, exception: {e}. Reloading")
                driver.get(url)

    except Exception as e:
        logger.warning(f"Failed to find next page element by xpath: {next_page_a_xpath}, exception: {e}. Reloading")
        driver.get(url)

    return songs_data_dict


def navigate_songs_single_page(driver, url, songs_data_dict):
    """ returns a dictionary of songs and their data dictionaries  """

    songs_xpath = "//td[@class='song']"
    songs_a_xpath = "//td[@class='song']/a"

    try:
        songs_elements = find_elements_by_xpath(driver, songs_xpath)

        song_href = ""  # needed for warning msg in case of failure
        song_name = ""  # needed for warning msg in case of failure

        for idx, _ in enumerate(songs_elements):

            try:
                xpath_by_idx = "({})[{}]".format(songs_a_xpath, str(idx + 1))  # note: xpath arr starts from 1
                song_a_element = find_element_by_xpath(driver, xpath_by_idx)

                # get song's name
                song_name = song_a_element.text

                # get the link to the song's page and move to the page
                song_href = song_a_element.get_attribute('href')

                try_click(url, song_a_element)

                # get song's chords and words data
                chords_dict = get_song_chords(driver)
                songs_data_dict[song_name] = chords_dict

                logger.log(f"parsed song {(idx+1)} for this page; name: {song_name}, href: {song_href}")

            except Exception as e:
                logger.warning(f"Failed to parse a song {idx} of current page, song href: {song_href}, song text: "
                               f"{song_name}, exception: {e}. Reloading")
                driver.get(url)

            try:
                # go back to the previous page, (driver.back() might cause weird behavior)
                # driver.execute_script("window.history.go(-1)")
                # driver.back()
                driver.get(url)

            except Exception as e:
                logger.warning(f"Failed go back (-1) in history, exception: {e}. Reloading")
                driver.get(url)

        return songs_data_dict

    except Exception as e:
        logger.warning(f"Failed to find songs by xpath: {songs_xpath}, exception: {e}. Reloading")
        driver.get(url)
        return {}



#####################


def get_song_chords(driver):
    """ returns key, value. key=song name, value=chords dictionary """
    # TODO: change
    return "** tmp **"


def get_chords(driver):
    """ returns all chords in the page in a dictionary """
    # TODO: change
    return {}
#######################





if __name__ == "__main__":
    driver = get_chrome_driver(consts.CHROME_DRIVER_PATH)

    try:

        url = "https://www.tab4u.com/tabs/artists/112_%D7%94%D7%A8%D7%90%D7%9C_%D7%A1%D7%A7%D7%A2%D7%AA.html"

        driver.get(url)
        print(get_data_by_artist(driver, url, "הראל סקעת"))

    finally:
        driver.close()
