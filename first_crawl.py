

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

import logging
import time
import pdb


# consts
CHROME_DRIVER_PATH = "../chromedriver"


def get_chrome_driver(path):
    chrome_options = Options()
    # chrome_options.add_argument("headless")
    chrome_options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


def navigate_between_songs(driver):
    """ returns a dictionary of songs and their chords dictionaries  """

    songs_a_xpath = "//a[@class='list-group-item']"
    songs_a_elements = driver.find_elements_by_xpath(songs_a_xpath)

    chords_by_songs_dict = {}
    song_href = ""
    song_text = ""

    # click to enter song's page and get it's chords dictionary
    for idx, _ in enumerate(songs_a_elements):

        try:
            song_xpath = songs_a_xpath + "[" + str(idx+1) + "]"
            song_a_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, song_xpath)))

            song_href = song_a_element.get_attribute('href')
            song_text = song_a_element.text

            song_a_element.click()

            song_name, chords_dict = get_song_chords(driver)
            chords_by_songs_dict[song_name] = chords_dict

            # go back to the previous page, (driver.back() might cause weird behavior)
            driver.execute_script("window.history.go(-1)")

        except Exception as e:
            logging.warning("Failed to parse a song, song href: {}, song text: {}, exception: {}"
                            .format(song_href, song_text, e))

    return chords_by_songs_dict


def get_song_chords(driver):
    """ returns key, value. key=song name, value=chords dictionary """

    song_name_xpath = "//div[@id='songName']"
    song_name = driver.find_elements_by_xpath(song_name_xpath)[0].text

    return song_name, get_chords(driver)


def get_chords(driver):
    """ returns all chords in the page in a dictionary """

    # TODO: work on the slash

    chords_xpath = "//span[@class='chord']"
    chord_web_elements = driver.find_elements_by_xpath(chords_xpath)

    chords_dict = {}

    for chord_web_element in chord_web_elements:
        chord = chord_web_element.text

        if chord in chords_dict:
            chords_dict[chord] += 1
        else:
            chords_dict[chord] = 1

    return chords_dict


def main():
    # TODO: wrap each function ith try and catch, get to prev url in every function to be able to go back

    driver = get_chrome_driver(CHROME_DRIVER_PATH)

    songs_url = "http://www.nagnu.co.il/%D7%90%D7%A7%D7%95%D7%A8%D7%93%D7%99%D7%9D/%D7%90%D7%91%D7%98%D7%99%D7%" \
                "A4%D7%95%D7%A1"
    driver.get(songs_url)
    print(navigate_between_songs(driver))




    # chords_url = "http://www.nagnu.co.il/%D7%90%D7%A7%D7%95%D7%A8%D7%93%D7%99%D7%9D/%D7%90%D7%A8%D7%99%D7%A7_%D7%90%D7" \
    #       "%99%D7%99%D7%A0%D7%A9%D7%98%D7%99%D7%99%D7%9F/%D7%A2%D7%98%D7%95%D7%A8_%D7%9E%D7%A6%D7%97%D7%9A"
    # driver.get(chords_url)
    # time.sleep(5)
    # print(get_song_chords(driver))


    driver.close()


if __name__ == "__main__":
    main()
