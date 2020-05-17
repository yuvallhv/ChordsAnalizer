

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import urllib

import consts
import logger
import pdb


###############################################################
# TODO: move to driver helpers
def get_chrome_driver(path):
    chrome_options = Options()
    chrome_options.add_argument("headless")
    # chrome_options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(options=chrome_options, executable_path=path)


def find_element_by_xpath(driver, xpath):
    """ find the required element (single) by xpath and wait for it to load """
    return WebDriverWait(driver, consts.WEB_DRIVER_WAIT_TIME).until(
        EC.presence_of_element_located((By.XPATH, xpath)))


def find_elements_by_xpath(driver, xpath):
    """ find the required elements (multiple) by xpath and wait for them to load """
    WebDriverWait(driver, consts.WEB_DRIVER_WAIT_TIME).until(
        EC.presence_of_element_located((By.XPATH, xpath)))
    return driver.find_elements_by_xpath(xpath)


def xpath_by_idx(xpath, idx):
    return "({})[{}]".format(xpath, str(idx + 1))  # note: xpath arr starts from 1


def try_click(url, element, cnt_try=consts.CNT_TRY):
    """ try click cnt_try times to try avoid losing data """

    try:
        element.click()

    except Exception as e:
        if cnt_try > 0:
            try_click(url, element, cnt_try-1)
        else:
            raise e


def go_back(driver, url):
    # (driver.back() might cause weird behavior)
    try:
        # driver.execute_script("window.history.go(-1)")
        # driver.back()
        driver.get(url)

    except Exception as e:
        logger.warning(f"Failed go back (-1) in history, exception: {e}. Reloading")
        driver.get(url)

###############################################################
###############################################################


def navigate_pages(driver, url, data_dict, single_page_func):
    """ returns a dictionary of data, from all the pages """

    next_page_nav_xpath = "//div[@class='pagination row']"

    # check if there are multiple pages
    try:
        find_element_by_xpath(driver, next_page_nav_xpath)
        return navigate_multiple_page(driver, url, data_dict, single_page_func)

    except Exception as e:
        return single_page_func(driver, url) if data_dict is None else single_page_func(driver, url, data_dict)


def navigate_multiple_page(driver, url, data_dict, single_page_func):
    """ returns a dictionary of data, from all the pages """

    next_page_str = "עמוד הבא"
    next_page_a_xpath = "//a[@class='nextPre'][1]"

    # get current page data
    single_page_func(driver, url) if data_dict is None else single_page_func(driver, url, data_dict)

    try:
        # check for more pages for this artist
        next_page_a_element = find_element_by_xpath(driver, next_page_a_xpath)
        next_page_a_text = next_page_a_element.text

        if next_page_str in next_page_a_text:
            try:
                url = next_page_a_element.get_attribute('href')  # no point to go back to the prev url
                try_click(url, next_page_a_element)
                logger.notice(f"moved to the next page for this artist, current url is {urllib.parse.unquote(url)}")

                navigate_multiple_page(driver, url, data_dict, single_page_func)

            except Exception as e:
                logger.warning(f"Failed to go to the next page, exception: {e}. Reloading")
                driver.get(url)

    except Exception as e:
        logger.warning(f"Failed to find next page element by xpath: {next_page_a_xpath}, exception: {e}. Reloading")
        driver.get(url)

    return data_dict


def navigate_artists(driver, url):
    navigate_pages(driver, url, None, navigate_artists_single_page)


def navigate_artists_single_page(driver, url):
    """ navigate through artists pages and dump a json file for each artist """

    artists_a_xpath = "//a[@class='searchLink']"
    artist_name = ""    # this is needed in case of warning

    # this shouldn't fail all page - might give empty data
    artists_albums_songs_cnt_dict = get_albums_songs_cnt_data(driver, url)

    try:
        artists_a_element = find_elements_by_xpath(driver, artists_a_xpath)

        for idx, _ in enumerate(artists_a_element):

            artist_a_xpath_by_idx = xpath_by_idx(artists_a_xpath, idx)
            artist_a_element = find_element_by_xpath(driver, artist_a_xpath_by_idx)

            artist_name = artist_a_element.text

            artist_albums_cnt, artist_songs_cnt = get_artist_albums_songs_cnt(artist_name,
                                                                              artists_albums_songs_cnt_dict)

            # go to the artist's page and create a json file for him
            try:
                artist_url = artist_a_element.get_attribute('href')
                try_click(url, artist_a_element)
                logger.notice(f"clicked successfully, current url is {urllib.parse.unquote(artist_url)}")

                get_data_as_json_file_by_artist(driver, artist_url, artist_name, artist_albums_cnt, artist_songs_cnt)

                # go back to the previous page
                go_back(driver, url)

            except Exception as e:
                logger.warning(f"Failed to click on the artist {artist_name} page, exception: {e}. Reloading")
                driver.get(url)

    except Exception as e:
        logger.warning(f"Failed to get artists links, exception: {e}.")


def get_artist_albums_songs_cnt(artist_name, artists_albums_songs_cnt_dict):
    if artist_name not in artists_albums_songs_cnt_dict:
        artist_albums_cnt = None
        artist_songs_cnt = None
    else:
        artist_albums_cnt = artists_albums_songs_cnt_dict[artist_name][consts.ALBUMS_CNT]
        artist_songs_cnt = artists_albums_songs_cnt_dict[artist_name][consts.SONGS_CNT]
    return artist_albums_cnt, artist_songs_cnt


def get_albums_songs_cnt_data(driver, url):
    """ returns a dictionary of key is the artist name, value is a dictionary of albums cnt and songs cnt """

    artists_table_trs_xpath = "//table[@class='tbl_type5']/tbody/tr"
    albums_songs_cnt_dct = {}

    try:
        artists_table_trs = find_elements_by_xpath(driver, artists_table_trs_xpath)[1:]     # remove table header

        for idx, _ in enumerate(artists_table_trs):

            try:
                artist_data = artists_table_trs[idx].text

                if artist_data is not None:
                    artist_data_lst = artist_data.split(" ")

                    if len(artist_data) >= 3:
                        artist_name = " ".join(artist_data_lst[:-2])

                        albums_songs_cnt_dct.update(
                            {artist_name: {
                                consts.ALBUMS_CNT: artist_data_lst[-2],
                                consts.SONGS_CNT: artist_data_lst[-1]
                            }})

            except Exception as e:
                logger.warning(f"Failed to get artist data, return empty albums and songs cnt, exception: {e}")

    except Exception as e:
        logger.warning(f"Failed to get artists table, return empty albums and songs cnt, exception: {e}")

    logger.log(f"Parsed artists albums and songs count: {albums_songs_cnt_dct}")
    return albums_songs_cnt_dct


def get_data_as_json_file_by_artist(driver, curr_url, artist_name, artist_albums_cnt, artist_songs_cnt):
    """ returns a data dictionary of the artist's biography information and songs data """

    # get data
    data_by_artist_dict = {
        consts.SONGS_DATA: navigate_pages(driver, curr_url, {}, navigate_songs_single_page),
        consts.ARTIST_DATA: {
            consts.ARTIST_NAME: artist_name,
            consts.ARTIST_BIO: get_artist_data(driver, curr_url),
            consts.ALBUMS_CNT: artist_albums_cnt,
            consts.SONGS_CNT: artist_songs_cnt
        }
    }

    # dump dictionary to json file by artist name
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


def navigate_songs_single_page(driver, url, songs_data_dict):
    """ returns a dictionary of songs and their data dictionaries  """

    songs_xpath = "//td[@class='song']"
    songs_a_xpath = "//td[@class='song']/a"

    try:
        songs_elements = find_elements_by_xpath(driver, songs_xpath)

        song_url = ""  # needed for warning msg in case of failure
        song_name = ""  # needed for warning msg in case of failure

        for idx, _ in enumerate(songs_elements):

            try:
                songs_a_xpath_by_idx = xpath_by_idx(songs_a_xpath, idx)  # note: xpath arr starts from 1
                song_a_element = find_element_by_xpath(driver, songs_a_xpath_by_idx)

                # get song's name
                song_name = song_a_element.text

                # get the link to the song's page and move to the page
                song_url = song_a_element.get_attribute('href')
                try_click(url, song_a_element)

                # get song's chords and words data
                chords_dict = get_song_chords(driver, song_url)
                songs_data_dict[song_name] = chords_dict

                logger.log(f"parsed song {(idx+1)} for this page; name: {song_name}, href: {urllib.parse.unquote(song_url)}")

            except Exception as e:
                logger.warning(f"Failed to parse a song {idx} of current page, song href: "
                               f"{urllib.parse.unquote(song_url)}, song text: "
                               f"{song_name}, current url: {urllib.parse.unquote(url)}, exception: {e}. Reloading")
                driver.get(url)

            # go back to the previous page
            go_back(driver, url)

        return songs_data_dict

    except Exception as e:
        logger.warning(f"Failed to find songs by xpath: {songs_xpath}, exception: {e}. Reloading")
        driver.get(url)
        return {}



#####################


def get_song_chords(driver, url):
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

        url = "https://www.tab4u.com/results?tab=artists&q=%D7%9B"


        driver.get(url)
        print(navigate_artists(driver, url))

    finally:
        driver.close()
