import json
import urllib

import driver_helper
import consts
import logger
import pdb


# ######################################################################################################################
# ########################################### pages navigation #########################################################

def navigate_pages(url, data_lst, artist_name, single_page_func):
    """ returns a dictionary of data, from all the pages """

    next_page_nav_xpath = "//div[@class='pagination row']"

    # check if there are multiple pages
    try:
        my_driver.find_element_by_xpath(next_page_nav_xpath)
        return navigate_multiple_pages(url, data_lst, artist_name, single_page_func)

    except Exception as e:
        return single_page_func(url) if data_lst is None else single_page_func(url, data_lst, artist_name)


def navigate_multiple_pages(url, data_dict, artist_name, single_page_func):
    """ returns a dictionary of data, from all the pages """

    next_page_str = "עמוד הבא"
    next_page_a_xpath = "//a[@class='nextPre'][1]"

    # get current page data
    single_page_func(url) if data_dict is None else single_page_func(url, data_dict, artist_name)

    try:
        # check for more pages for this artist
        next_page_a_element = my_driver.find_element_by_xpath(next_page_a_xpath)
        next_page_a_text = next_page_a_element.text

        if next_page_str in next_page_a_text:
            try:
                url = next_page_a_element.get_attribute('href')  # no point to go back to the prev url
                my_driver.try_click(url, next_page_a_element)
                logger.notice(f"moved to the next page for this artist, current url is {urllib.parse.unquote(url)}")

                navigate_multiple_pages(url, data_dict, artist_name, single_page_func)

            except Exception as e:
                logger.warning(f"Failed to go to the next page, exception: {e}. Reloading")
                my_driver.driver.get(url)

    except Exception as e:
        logger.warning(f"Failed to find next page element by xpath: {next_page_a_xpath}, exception: {e}. Reloading")
        my_driver.driver.get(url)

    return data_dict


def navigate_artists(url):
    """ navigates artist pages, dump a json file for each artist """

    navigate_pages(url, None, None, navigate_artists_single_page)


def navigate_artists_single_page(url):
    """ navigate through artists pages and dump a json file for each artist """

    artists_a_xpath = "//a[@class='searchLink']"
    artist_name = ""    # this is needed in case of warning

    # this shouldn't fail all page - might give empty data
    artists_albums_songs_cnt_dict = get_albums_songs_cnt_data(url)

    try:
        artists_a_element = my_driver.find_elements_by_xpath(artists_a_xpath)

        for idx, _ in enumerate(artists_a_element):

            artist_a_xpath_by_idx = my_driver.xpath_by_idx(artists_a_xpath, idx)
            artist_a_element = my_driver.find_element_by_xpath(artist_a_xpath_by_idx)

            artist_name = artist_a_element.text

            artist_albums_cnt, artist_songs_cnt = get_artist_albums_songs_cnt(artist_name,
                                                                              artists_albums_songs_cnt_dict)

            # go to the artist's page and create a json file for him
            try:
                artist_url = artist_a_element.get_attribute('href')
                my_driver.try_click(url, artist_a_element)
                logger.notice(f"clicked successfully, current url is {urllib.parse.unquote(artist_url)}")

                get_data_as_json_file_by_artist(artist_url, artist_name, artist_albums_cnt, artist_songs_cnt)

                # go back to the previous page
                my_driver.go_back(url)

            except Exception as e:
                logger.warning(f"Failed to click on the artist {artist_name} page, exception: {e}. Reloading")
                my_driver.driver.get(url)

    except Exception as e:
        logger.warning(f"Failed to get artists links, exception: {e}.")


def navigate_songs_single_page(url, songs_data_lst, artist_name):
    """ returns a dictionary of songs and their data dictionaries  """

    songs_xpath = "//td[@class='song']"
    songs_a_xpath = "//td[@class='song']/a"

    try:
        songs_elements = my_driver.find_elements_by_xpath(songs_xpath)

        song_url = ""  # needed for warning msg in case of failure
        song_name = ""  # needed for warning msg in case of failure

        for idx, _ in enumerate(songs_elements):

            try:
                songs_a_xpath_by_idx = my_driver.xpath_by_idx(songs_a_xpath, idx)  # note: xpath arr starts from 1
                song_a_element = my_driver.find_element_by_xpath(songs_a_xpath_by_idx)

                # get song's name
                song_name = song_a_element.text

                # get the link to the song's page and move to the page
                song_url = song_a_element.get_attribute('href')
                my_driver.try_click(url, song_a_element)

                # get song's chords and words data
                song_data_dict = get_song_data_init_page(song_url, artist_name, song_name)
                songs_data_lst.append(song_data_dict)

                logger.log(f"parsed song {(idx+1)} for this page; name: {song_name}, href: {urllib.parse.unquote(song_url)}")

            except Exception as e:
                logger.warning(f"Failed to parse a song {idx} of current page, song href: "
                               f"{urllib.parse.unquote(song_url)}, song text: "
                               f"{song_name}, current url: {urllib.parse.unquote(url)}, exception: {e}. Reloading")
                my_driver.driver.get(url)

            # go back to the previous page
            my_driver.go_back(url)

        return songs_data_lst

    except Exception as e:
        logger.warning(f"Failed to find songs by xpath: {songs_xpath}, exception: {e}. Reloading")
        my_driver.driver.get(url)
        return {}


# ######################################################################################################################
# ########################################### get artist data ##########################################################

def get_artist_albums_songs_cnt(artist_name, artists_albums_songs_cnt_dict):
    """ separates the albums and songs count dictionaty into 2 parameters """
    if artist_name not in artists_albums_songs_cnt_dict:
        artist_albums_cnt = None
        artist_songs_cnt = None
    else:
        artist_albums_cnt = artists_albums_songs_cnt_dict[artist_name][consts.ALBUMS_CNT]
        artist_songs_cnt = artists_albums_songs_cnt_dict[artist_name][consts.SONGS_CNT]
    return artist_albums_cnt, artist_songs_cnt


def get_albums_songs_cnt_data(url):
    """ returns a dictionary of key is the artist name, value is a dictionary of albums cnt and songs cnt """

    artists_table_trs_xpath = "//table[@class='tbl_type5']/tbody/tr"
    albums_songs_cnt_dct = {}

    try:
        artists_table_trs = my_driver.find_elements_by_xpath(artists_table_trs_xpath)[1:]     # remove table header

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


def get_data_as_json_file_by_artist(curr_url, artist_name, artist_albums_cnt, artist_songs_cnt):
    """ returns a data dictionary of the artist's biography information and songs data """

    # get data
    data_by_artist_dict = {
        consts.ARTIST_DATA: {
            consts.ARTIST_NAME: artist_name,
            consts.ARTIST_BIO: get_artist_data(curr_url),
            consts.ALBUMS_CNT: artist_albums_cnt,
            consts.SONGS_CNT: artist_songs_cnt
        },
        consts.SONGS_DATA: navigate_pages(curr_url, [], artist_name, navigate_songs_single_page)
    }

    # dump dictionary to json file by artist name
    try:
        file_name = f"json_files/{artist_name}.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data_by_artist_dict, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.warning(f"Failed to dump artist {artist_name} to json file, exception: {e}.")


def get_artist_data(url):
    """ returns a dictionary of the artist's biography information """

    artist_bios_xpath = "//ul[@class='artist_block_bio']/li"
    artist_bio_dict = {}
    last_artist_bio_key = None

    pdb.set_trace()

    try:
        artist_bios_elements = my_driver.find_elements_by_xpath(artist_bios_xpath)

        for artist_bio_e in artist_bios_elements:

            if ": " in artist_bio_e.text:
                artist_bio = artist_bio_e.text.split(": ")
                artist_bio_dict[artist_bio[0]] = artist_bio[1]
                last_artist_bio_key = artist_bio[0]

            elif last_artist_bio_key:
                artist_bio_dict[last_artist_bio_key] += artist_bio_e.text

        logger.log(f"parsed artist's biography:' {artist_bio_dict}")

        return artist_bio_dict

    except Exception as e:
        logger.warning(f"Failed to get the artist's biography information, exception: {e}. Reloading")
        my_driver.driver.get(url)
        return artist_bio_dict


# ######################################################################################################################
# ########################################### get song data ############################################################

def get_song_data_init_page(url, artist_name, song_name):
    """ get data dict about the song from its initial page """

    song_data_dict = {
        consts.SONG_NAME: song_name,
        consts.RANKING: get_song_ranking(url, song_name),
        consts.AUTHOR_COMPOSER: get_song_author_composer(url, song_name),
        consts.CATEGORIES: get_song_categories(url, song_name),
        consts.COLLABORATORS: get_song_collaborators(url, artist_name, song_name),
        consts.PARAGRAPHS: get_song_paragraphs_content(url, song_name)
    }

    logger.log(f"Found song data for song: {song_data_dict[consts.SONG_NAME]}")
    return song_data_dict


def fix_tab_paragraphs(song_paragraphs):

    fixed_song_paragraphs = []
    paragraph_type = consts.UNIQUE
    definition_name = ""
    tabs_lines = []
    chords_lines = []
    has_chords = False

    for paragraph in song_paragraphs:

        if not paragraph[consts.IS_TAB_PARA]:

            # if there is a tabs paragraph in fixing progress, it is now finished and should be appended
            chords_lines, definition_name, paragraph_type, tabs_lines = append_fixed_tabs_paragraph(
                chords_lines, definition_name, fixed_song_paragraphs, paragraph, paragraph_type, tabs_lines, False)

            paragraph.pop(consts.IS_TAB_PARA)
            fixed_song_paragraphs.append(paragraph)


        # check if this is tabs paragraph of tabs
        elif len(paragraph[consts.TABS_LINES]) > 0:

            #  when reaching to a definition of a new tab paragraph, append the last tab paragraph, if such exists
            if paragraph[consts.TYPE] == consts.DEFINITION:
                chords_lines, definition_name, paragraph_type, tabs_lines = append_fixed_tabs_paragraph(
                    chords_lines, definition_name, fixed_song_paragraphs, paragraph, paragraph_type, tabs_lines)

            tabs_lines.append({
                consts.TABS_LINE: '\n'.join(paragraph[consts.TABS_LINES]),
                consts.HAS_CHORDS: has_chords
            })

            has_chords = False


        # check if this is tabs paragraph of chords
        else:

            has_chords = True

            #  when reaching to a definition of a new tab paragraph, append the last tab paragraph, if such exists
            if paragraph[consts.TYPE] == consts.DEFINITION:
                chords_lines, definition_name, paragraph_type, tabs_lines = append_fixed_tabs_paragraph(
                    chords_lines, definition_name, fixed_song_paragraphs, paragraph, paragraph_type, tabs_lines)

            chords_lines.append(paragraph[consts.CHORDS_LINES][0])


    # if there is a tabs paragraph in fixing progress, it is now finished and should be appended
    if len(tabs_lines) > 0:
        fixed_song_paragraphs.append({
            consts.TYPE: paragraph_type,
            consts.DEFINITION_NAME: definition_name,
            consts.CHORDS_LINES: chords_lines,
            consts.TABS_LINES: tabs_lines,
            consts.LYRICS_LINES: []
        })

    return fixed_song_paragraphs


def append_fixed_tabs_paragraph(chords_lines, definition_name, fixed_song_paragraphs, paragraph, paragraph_type,
                                tabs_lines, is_definition=True):
    """ appends the fixed paragraph and initiate the parameters again to be ready for the next one """

    if len(tabs_lines) > 0:
        fixed_song_paragraphs.append({
            consts.TYPE: paragraph_type,
            consts.DEFINITION_NAME: definition_name,
            consts.CHORDS_LINES: chords_lines,
            consts.TABS_LINES: tabs_lines,
            consts.LYRICS_LINES: []
        })
        # create the parameters for the new paragraph
        tabs_lines = []
        chords_lines = []

    if is_definition:
        definition_name = paragraph[consts.DEFINITION_NAME]
        paragraph_type = paragraph[consts.TYPE]
    else:
        definition_name = ""
        paragraph_type = consts.UNIQUE

    return chords_lines, definition_name, paragraph_type, tabs_lines


def get_song_paragraphs_content(url, song_name):
    """ Returns a list of the song's paragraphs. Each item in the list contains the paragraph definition, chords, tabs
    and lyrics. """

    song_paragraphs_xpath = "//div[@id='songContentTPL']/*"
    song_paragraphs = []
    definitions = {}    # key = definition name, value = paragraph number
    is_current_a_definition = False
    definition_name = ""

    try:
        song_paragraphs_elements = my_driver.find_elements_by_xpath(song_paragraphs_xpath)

        # go through all paragraphs (and br)
        for paragraph_idx, song_paragraph_element in enumerate(song_paragraphs_elements):

            # Do not try to parse tag br paragraphs
            if song_paragraph_element.tag_name == "br":
                continue

            chords_lines = []
            tabs_lines = []
            song_lines = []
            is_tabs_paragraph = False

            song_lines_xpath = f"{my_driver.xpath_by_idx(song_paragraphs_xpath, paragraph_idx)}/tbody/tr/td"
            song_lines_elements = my_driver.find_elements_by_xpath(song_lines_xpath)

            # go through all lines in the paragraph
            for line_idx, song_line_element in enumerate(song_lines_elements):

                line_text = song_line_element.text
                line_type = song_line_element.get_attribute("class")

                if line_type == consts.CHORDS_CLASS:
                    chords_lines.append(line_text)

                if line_type == consts.TABS_CLASS:
                    tabs_lines.append(line_text)
                    is_tabs_paragraph = True

                elif line_type == consts.SONG_CLASS:
                    song_lines.append(line_text)

            # check if this paragraph belongs to a larger tab paragraph - it has no br at the end
            next_idx = paragraph_idx + 1
            if next_idx < len(song_paragraphs_elements) and song_paragraphs_elements[next_idx].tag_name != "br":
                is_tabs_paragraph = True

            # check if this paragraph is part of a definition started at the previous paragraph
            if is_current_a_definition:
                song_paragraphs.append({
                    consts.TYPE: consts.DEFINITION,
                    consts.DEFINITION_NAME: definition_name,
                    consts.CHORDS_LINES: chords_lines,
                    consts.TABS_LINES: tabs_lines,
                    consts.LYRICS_LINES: song_lines,
                    consts.IS_TAB_PARA: is_tabs_paragraph
                })

                is_current_a_definition = False

            else:
                is_current_a_definition, definition_name, paragraph_type, song_lines = get_paragraph_definition(
                    chords_lines, definitions, song_lines, song_paragraphs)

                if not is_current_a_definition:
                    song_paragraphs.append({
                        consts.TYPE: paragraph_type,
                        consts.DEFINITION_NAME: definition_name,
                        consts.CHORDS_LINES: chords_lines,
                        consts.TABS_LINES: tabs_lines,
                        consts.LYRICS_LINES: song_lines,
                        consts.IS_TAB_PARA: is_tabs_paragraph
                    })

        return fix_tab_paragraphs(song_paragraphs)

    except Exception as e:
        logger.warning(f"Failed to find song's words and chords for song {song_name}, exception: {e}. Reloading")
        my_driver.driver.get(url)
        return ""


def get_paragraph_definition(chords_lines, definitions, song_lines, song_paragraphs):
    """ decide if this paragraph is type definition/repetitive/unique """

    is_next_define = False

    # decide if this is a definition of a repetitive section
    if len(song_lines) > 0 and song_lines[0][-1] == ":":

        definition_name = song_lines[0].replace(":", "")
        definition_paragraph_num = len(song_paragraphs)
        definitions.update({definition_name: definition_paragraph_num})

        # decide if the defined paragraph is the next or the current
        if len(song_lines) == 1 and len(chords_lines) == 0:
            is_next_define = True
            paragraph_type = None

        else:
            paragraph_type = consts.DEFINITION
            song_lines = song_lines[1:]

    # decide if this paragraph was already defined before
    elif len(song_lines) == 1 and len(chords_lines) == 0 and song_lines[0] in definitions:
        paragraph_type = consts.REPETITIVE
        definition_name = song_lines[0]
        song_lines = []

    else:
        paragraph_type = consts.UNIQUE
        definition_name = ""

    return is_next_define, definition_name, paragraph_type, song_lines


def get_song_collaborators(url, artist_name, song_name):
    """ Returns a string with the names of the other artists that worked on this song """
    # TODO: we can make this at the end of the crawling to be a list -
    # TODO: by looking for words that starts with " ו" and checking to see if there is an artist with this name....

    all_artists_xpath = "//div[@class='data_block_title_text']/a"
    and_artist = " ו" + artist_name
    collaborators = None

    try:
        all_artists = my_driver.find_element_by_xpath(all_artists_xpath).text
        collaborators = all_artists.replace(and_artist, "") if and_artist in all_artists else all_artists.replace(artist_name, "")

    except Exception as e:
        logger.warning(f"Failed to find collaborators for song {song_name}, exception: {e}. Reloading")
        my_driver.driver.get(url)

    return collaborators


def get_song_categories(url, song_name):
    """ Returns a list of the song's categories """

    categories_xpath = "//a[@class='catLinkInSong']"
    categories_lst = []

    try:
        categories_elements = my_driver.find_elements_by_xpath(categories_xpath)
        categories_lst = [category_element.text for category_element in categories_elements]

    except Exception as e:
        logger.warning(f"Failed to find categories for song {song_name}, exception: {e}. Reloading")
        my_driver.driver.get(url)

    return categories_lst


def get_song_author_composer(url, song_name):
    """ returns a dictionary of the author and composer of the current song """
    # TODO: change the data struct (parse better)

    author_composer_dict = None
    author_composer_headers_spans_xpath = "//div[@id='aAndcArea']/span[@id='koteretInSong']"
    author_composer_info_spans_xpath = "//div[@id='aAndcArea']/span[@id='textInSong']"

    try:
        author_composer_dict = {}
        author_composer_headers_spans = my_driver.find_elements_by_xpath(author_composer_headers_spans_xpath)
        author_composer_info_spans = my_driver.find_elements_by_xpath(author_composer_info_spans_xpath)

        if not isinstance(author_composer_headers_spans, list) or \
                not isinstance(author_composer_info_spans, list) or \
                not len(author_composer_headers_spans) == len(author_composer_info_spans):
            raise Exception()

        for idx, (author_composer_header_span, author_composer_info_span) in \
                enumerate(zip(author_composer_headers_spans, author_composer_info_spans)):
            author_composer_header = author_composer_header_span.text.replace(":", "")
            author_composer_info = author_composer_info_span.text

            # TODO: parse this better
            author_composer_dict.update({author_composer_header: author_composer_info})

    except Exception as e:
        logger.warning(f"Failed to find composer and author for song {song_name}, exception: {e}. Reloading")
        my_driver.driver.get(url)

    return author_composer_dict


def get_song_ranking(url, song_name):
    """ returns the song's ranking as a float """

    ranking = None

    try:
        ranking_xpath = "//span[@class='rankPre']"
        ranking_element = my_driver.find_element_by_xpath(ranking_xpath)
        ranking = float(ranking_element.text)

    except Exception as e:
        logger.warning(f"Failed to find ranking for song {song_name}, exception: {e}. Reloading")
        my_driver.driver.get(url)

    return ranking


# ######################################################################################################################
# ################################################ main ################################################################

if __name__ == "__main__":
    my_driver = driver_helper.DriverHelper()
    my_driver.get_chrome_driver(consts.CHROME_DRIVER_PATH)

    try:
        url = "https://www.tab4u.com/tabs/artists/131_%D7%9B%D7%9C%D7%90_6.html"
        my_driver.driver.get(url)

        print(get_data_as_json_file_by_artist(url, "כלא 6", 2, 2))


    finally:
        my_driver.driver.close()
