import json
from os import listdir
from os.path import isfile, join
from os import walk
import pdb
import logger

import consts


# consts
all_chords_set = set()
global_categories_lst = []
global_chords_weights_dict = {}
global_weights_by_genres = {}
global_weights_by_artists = {}
global_artists_urls = {}
global_famous_artists = []


def get_all_files_paths(directory_path):
    """ Gets all the json data files path as a list """

    files_names = []
    for (dirpath, dirnames, filenames) in walk(directory_path):
        files_names.extend(filenames)
        break

    files_paths = []
    for file_name in files_names:
        files_paths.append(f"{directory_path}/{file_name}")

    return files_paths


def activate_processing_function_on_all_artists(directory_path, processing_function):
    """ Goes through all the json files and activate a function on each """

    files_paths = get_all_files_paths(directory_path)

    for file_path in files_paths:
        processing_function(file_path)


def activate_processing_function_on_single_artists(file_path, reading_processing_function, write_file=False):
    """ activate a processing function on an artist's json file """

    with open(file_path) as json_file:
        try:
            artist_json = json.load(json_file)

        except Exception as e:
            logger.warning(f"Could not load file: {file_path}, e: {e}")

        try:
            reading_processing_function(artist_json)

        except Exception as e:
            logger.warning(f"Failed to process file: {file_path}, e: {e}")

    if write_file:
        with open(file_path, 'w', encoding='utf8') as json_file:
            try:
                json.dump(artist_json, json_file, ensure_ascii=False)
                logger.log(f"updated file: {file_path}")

            except Exception as e:
                logger.warning(f"Could not dump to file: {file_path}, e: {e}")


def get_data_all_artists(directory_path, data_file_path):
    """ Get weights data on all artists """

    # fill global data list and dicts
    files_paths = get_all_files_paths(directory_path)
    for file_path in files_paths:
        activate_processing_function_on_single_artists(file_path, get_data_single_artist)

    # note: manually delete - Pop, Undefined, Eurovision Songs, Rock, בשפה הספרדית

    # create json
    all_data_dict = {
        consts.CATEGORIES_GENERAL_DATA: global_categories_lst,
        consts.CHORDS_WEIGHT_GENERAL_DATA: global_chords_weights_dict,
        consts.CHORDS_WEIGHT_BY_GENRES: global_weights_by_genres,
        consts.CHORDS_WEIGHT_BY_ARTISTS: global_weights_by_artists,
        consts.ARTISTS_URLS: global_artists_urls
    }

    with open(data_file_path, 'w', encoding='utf8') as json_file:
        try:
            json.dump(all_data_dict, json_file, ensure_ascii=False)
            logger.log(f"updated file: {data_file_path}")

        except Exception as e:
            logger.warning(f"Could not dump to file: {data_file_path}, e: {e}")


def add_data_to_data_json(data_file_path, key, value):

    # read and update
    with open(data_file_path) as json_file:
        try:
            json_data = json.load(json_file)
            json_data.update({key: value})

        except Exception as e:
            logger.warning(f"Could not load or add to file: {data_file_path}, e: {e}")

    # write
    with open(data_file_path, 'w', encoding='utf8') as json_file:
        try:
            json.dump(json_data, json_file, ensure_ascii=False)
            logger.log(f"updated file: {data_file_path}")

        except Exception as e:
            logger.warning(f"Could not dump to file: {data_file_path}, e: {e}")


def find_famous_all_artists(directory_path):
    """ Gets all the famous artists """

    # fill global data list and dicts
    files_paths = get_all_files_paths(directory_path)
    for file_path in files_paths:
        activate_processing_function_on_single_artists(file_path, add_to_lst_if_famous_single_artist)


def add_to_lst_if_famous_single_artist(artist_json):
    """ Adds this artist to the global famous artists if they have more than 30 songs """

    try:
        song_data = artist_json[consts.SONGS_DATA]
        artist_name = artist_json[consts.ARTIST_DATA][consts.ARTIST_NAME]

        if len(song_data) >= 25:
            global_famous_artists.append(artist_name)

    except Exception as e:
        logger.warning(f"Could not get number of songs for this artist: {artist_name}, e: {e}")


def get_data_single_artist(artist_json):
    """ Append all data for this artist and return the updated global data """

    try:

        songs_data = artist_json[consts.SONGS_DATA]
        artist_name = artist_json[consts.ARTIST_DATA][consts.ARTIST_NAME]

        # artist url
        global_artists_urls.update({artist_name: artist_json[consts.URL]})

        artist_weights_dict = {}

        for idx, song_data in enumerate(songs_data):

            # pdb.set_trace()

            try:
                categories = song_data[consts.CATEGORIES]
                weights_dict = song_data[consts.CHORDS_WEIGHT]

                # categories
                for category in categories:
                    if category not in global_categories_lst:
                        global_categories_lst.append(category)

                # global weights
                for (chord, weight) in weights_dict.items():
                    add_or_append_to_weights_dict(chord, weight, global_chords_weights_dict)

                # weights by genres
                for category in categories:
                    if category not in global_weights_by_genres:
                        global_weights_by_genres.update({category: {}})

                    for (chord, weight) in weights_dict.items():
                        add_or_append_to_weights_dict(chord, weight, global_weights_by_genres[category])

                # weights by artists
                for (chord, weight) in weights_dict.items():
                    add_or_append_to_weights_dict(chord, weight, artist_weights_dict)

            except Exception as e:
                logger.warning(f"Could not get data for song idx: {idx}")

        global_weights_by_artists.update({artist_name: artist_weights_dict})

        logger.log(f"Successfully got data for artist: {artist_name}")

    except Exception as e:
        logger.warning(f"Could not get data for artist: {artist_name}")


def add_or_append_to_weights_dict(chord, weight, weights_dict):
    """ Add a weight to the weight dict """

    if chord not in weights_dict:
        weights_dict.update({chord: 0})
    weights_dict[chord] += weight


def update_weights_dicts_for_artist(file_path):
    """ Create the weights list for an artist """

    with open(file_path) as json_file:
        try:
            artist_json = json.load(json_file)
            songs_data = artist_json[consts.SONGS_DATA]

            try:

                for idx, song_data in enumerate(songs_data):

                    try:
                        weights_dict = {}
                        paragraphs = song_data[consts.PARAGRAPHS]

                        for paragraph in paragraphs:
                            chords_lines = paragraph[consts.CHORDS_LINES]
                            get_weights_dict_from_single_paragraph(chords_lines, weights_dict)

                        artist_json[consts.SONGS_DATA][idx].update({consts.CHORDS_WEIGHT: weights_dict})

                    except Exception as e:
                        logger.warning(f"Could not get weights for song idx: {idx}")

            except Exception as e:
                logger.warning(f"Could not get weights for song: {file_path}")

        except Exception as e:
            logger.warning(f"Could not load file: {file_path}, e: {e}")

    with open(file_path, 'w', encoding='utf8') as json_file:
        try:
            json.dump(artist_json, json_file, ensure_ascii=False)
            logger.log(f"updated file: {file_path}")

        except Exception as e:
            logger.warning(f"Could not dump to file: {file_path}, e: {e}")


def get_chords_single_artist_from_json(file_path):
    """ Adds the chords to the global set from a single json file"""

    with open(file_path) as json_file:
        try:
            artist_json = json.load(json_file)

            artist_songs_data_list = artist_json[consts.SONGS_DATA]

            for artist_song_data in artist_songs_data_list:
                chords_weights_list = artist_song_data[consts.CHORDS_WEIGHT]
                unique_chords_list = chords_weights_list.keys()

                all_chords_set.update(unique_chords_list)

        except Exception as e:
            logger.warning(f"### Could not load file: {file_path}")


def get_weights_dict_from_single_paragraph(chords_lines, weights_dict):
    """ Updates the weights dict from a list of strings that represents the chords lines """

    last_chord_in_line = ""
    need_to_be_added_to_prev_line = False

    # handle repeated lines
    try:
        chords_lines_backup = chords_lines

        if len(chords_lines) == 1 and " x" in chords_lines[0]:

            multiply_location = chords_lines[0].index(" x") + len(" x")

            if len(chords_lines[0]) > multiply_location:
                multiply = int(chords_lines[0][multiply_location])

                chords_line = chords_lines[0][:multiply_location - len(" x")]
                chords_lines = []

                for _ in range(multiply):
                    chords_lines.append(chords_line)

    except Exception as e:
        logger.warning(f"Could not handle multiplication")
        chords_lines = chords_lines_backup

    for chords_line in chords_lines:

        idx = 0
        while len(chords_line) > idx:

            cnt_spaces = 0
            chord = ""

            while len(chords_line) > idx and not chords_line[idx] == " ":
                chord += chords_line[idx]
                idx += 1

            while len(chords_line) > idx and chords_line[idx] == " ":
                if idx == 0:
                    need_to_be_added_to_prev_line = True

                cnt_spaces += 1
                idx += 1

            if need_to_be_added_to_prev_line:
                need_to_be_added_to_prev_line = False

                if last_chord_in_line:
                    weights_dict[last_chord_in_line] += cnt_spaces

            else:

                chord_weight = cnt_spaces + len(chord)

                if chord in weights_dict:
                    weights_dict[chord] += chord_weight
                else:
                    weights_dict.update({chord: chord_weight})

            last_chord_in_line = chord

    return weights_dict


def delete_multiply_chords_for_single_artist(file_path):
    """ Delete multipliers since they are not chords """

    with open(file_path) as json_file:
        try:
            artist_json = json.load(json_file)
            songs_data = artist_json[consts.SONGS_DATA]

            try:
                for idx, song_data in enumerate(songs_data):
                    weights_dict = song_data[consts.CHORDS_WEIGHT]
                    new_weights_dict = {}

                    for chord in weights_dict.keys():
                        if "x" not in chord:
                            new_weights_dict.update({chord: weights_dict[chord]})

                    artist_json[consts.SONGS_DATA][idx].update({consts.CHORDS_WEIGHT: new_weights_dict})

            except Exception as e:
                logger.warning(f"Could not get weights for song: {file_path}")

        except Exception as e:
            logger.warning(f"Could not load file: {file_path}, e: {e}")

    with open(file_path, 'w', encoding='utf8') as json_file:
         try:
            json.dump(artist_json, json_file, ensure_ascii=False)
            logger.log(f"updated file: {file_path}")

         except Exception as e:
            logger.warning(f"Could not update weights for song: {file_path}")


def find_chord_single_artist(file_path, chord):
    """ Find the song that the parameter chord appear in """

    with open(file_path) as json_file:
        try:
            artist_json = json.load(json_file)
            songs_data = artist_json[consts.SONGS_DATA]

            try:
                for idx, song_data in enumerate(songs_data):
                    paragraphs = song_data[consts.PARAGRAPHS]

                    for paragraph in paragraphs:
                        chords_lines = paragraph[consts.CHORDS_LINES]

                        for chords_line in chords_lines:
                            if chord in chords_lines:

                                logger.notice(f"Chord is in song: {song_data[consts.SONG_NAME]}, artist: {artist_json[consts.ARTIST_DATA][consts.ARTIST_NAME]}")


            except Exception as e:
                logger.warning(f"Could not get weights for song: {file_path}")

        except Exception as e:
            logger.warning(f"Could not load file: {file_path}, e: {e}")


def delete_buggy_chords_from_single_artist(file_path):
    """ Delete buggy chords (such as chords that include "[") since they are not chords """

    with open(file_path) as json_file:
        try:
            artist_json = json.load(json_file)
            songs_data = artist_json[consts.SONGS_DATA]

            try:
                for idx, song_data in enumerate(songs_data):
                    weights_dict = song_data[consts.CHORDS_WEIGHT]
                    new_weights_dict = {}

                    for chord in weights_dict.keys():
                        if "[" in chord or "]" in chord:

                            if weights_dict[chord] > 10:
                                handle = False
                                pdb.set_trace()
                                if handle:
                                    old_chord = chord
                                    chord = chord[1:len(chord)-1]

                                    if chord in weights_dict:
                                        new_weights_dict.update({chord: weights_dict[old_chord] + weights_dict[chord]})
                                    else:
                                        new_weights_dict.update({chord: weights_dict[old_chord]})

                                    new_weights_dict.update({chord: weights_dict[old_chord]})
                            continue

                        new_weights_dict.update({chord: weights_dict[chord]})

                    artist_json[consts.SONGS_DATA][idx].update({consts.CHORDS_WEIGHT: new_weights_dict})

            except Exception as e:
                logger.warning(f"Could not get weights for song: {file_path}")

        except Exception as e:
            logger.warning(f"Could not load file: {file_path}, e: {e}")

    with open(file_path, 'w', encoding='utf8') as json_file:
        try:
            json.dump(artist_json, json_file, ensure_ascii=False)
            logger.log(f"updated file: {file_path}")

        except Exception as e:
            logger.warning(f"Could not update weights for song: {file_path}")


def find_chord(directory_path, chord):
    """ Goes through all the json files searches a certain chord """

    files_paths = get_all_files_paths(directory_path)

    for file_path in files_paths:
        find_chord_single_artist(file_path, chord)


def delete_buggy_chords_all_artist(directory_path):
    """ Goes through all the json files and delete buggy chords since they are not chords """

    activate_processing_function_on_all_artists(directory_path, delete_buggy_chords_from_single_artist)


def delete_multiply_chords_all_artists(directory_path):
    """ Goes through all the json files and delete multipliers since they are not chords """

    activate_processing_function_on_all_artists(directory_path, delete_multiply_chords_for_single_artist)


def collect_chords_weights_all_artists(directory_path):
    """ Goes through all the json files and collects the chords to a set """

    activate_processing_function_on_all_artists(directory_path, update_weights_dicts_for_artist)


def get_chords_all_artists(directory_path):
    """ Goes through all the json files and collects the chords to a set """

    activate_processing_function_on_all_artists(directory_path, get_chords_single_artist_from_json)


# ############################# Chords Groups Division ##############################

def update_general_data_to_chord_groups(file_path, new_file_path, write=False):
    """ Update the general data file with all chords weight dictionary divided to groups """

    # read and update
    with open(file_path) as json_file:
        try:
            json_data = json.load(json_file)

            # all chords weight and groups
            chords_weight_dict = json_data[consts.CHORDS_WEIGHT]
            chords_weight_in_groups_dict, chords_groups = divide_chords_to_groups(chords_weight_dict)

            json_data.update({consts.CHORDS_WEIGHT_IN_GROUPS: chords_weight_in_groups_dict})
            json_data.update({consts.CHORDS_GROUPS: chords_groups})

            # chords by genres groups
            chords_weight_by_genres = json_data[consts.CHORDS_WEIGHT_BY_GENRES]
            chords_weight_in_groups_by_genres = {}

            for genre in chords_weight_by_genres:
                chords_weight_in_groups_by_genre, _ = divide_chords_to_groups(chords_weight_by_genres[genre])
                chords_weight_in_groups_by_genres.update({genre: chords_weight_in_groups_by_genre})

            json_data.update({consts.CHORDS_WEIGHT_IN_GROUPS_BY_GENRES: chords_weight_in_groups_by_genres})

            # chords by artists groups
            chords_weight_by_artists = json_data[consts.CHORDS_WEIGHT_BY_ARTISTS]
            chords_weight_in_groups_by_artists = {}

            for artist in chords_weight_by_artists:
                chords_weight_in_groups_by_artist, _ = divide_chords_to_groups(chords_weight_by_artists[artist])
                chords_weight_in_groups_by_artists.update({artist: chords_weight_in_groups_by_artist})

            json_data.update({consts.CHORDS_WEIGHT_IN_GROUPS_BY_ARTISTS: chords_weight_in_groups_by_artists})


            pdb.set_trace()

        except Exception as e:
            logger.warning(f"Could not load or add to file: {file_path}, e: {e}")

    # write
    if write:
        with open(new_file_path, 'w', encoding='utf8') as json_file:
            try:
                json.dump(json_data, json_file, ensure_ascii=False)
                logger.log(f"updated file: {new_file_path}")

            except Exception as e:
                logger.warning(f"Could not dump to file: {new_file_path}, e: {e}")


def divide_chords_to_groups(chord_dict):
    """ divide the chords to groups by some rules and return a new dictionary
        Major - happy and simple - contains "M", "Ma", "Maj"
        Minor - sad or serious - contains "m", "min"
        Diminished - tense and unpleasant - contains "dim"
        Major Seventh - thoughtful, soft - contains Major symbols + "7"
        Minor Seventh - moody, or contemplative - contains Minor symbols + "7"
        Dominant Seventh - strong and restless - contains "7" (without Major or Minor symbols), "alt", "dom"
        Suspended - bright and nervous - contains "sus"
        Augmented - anxious and suspenseful - contains "+", "aug"
        other
     """

    groups_chord_weight_dict = {
        consts.MAJOR: 0,
        consts.MINOR: 0,
        consts.DIMINISHED: 0,
        consts.MAJOR_SEVENTH: 0,
        consts.MINOR_SEVENTH: 0,
        consts.DOMINANT_SEVENTH: 0,
        consts.SUSPENDED: 0,
        consts.AUGMENTED: 0,
        consts.OTHER: 0,
    }

    groups_chord_dict = {
        consts.MAJOR: [],
        consts.MINOR: [],
        consts.DIMINISHED: [],
        consts.MAJOR_SEVENTH: [],
        consts.MINOR_SEVENTH: [],
        consts.DOMINANT_SEVENTH: [],
        consts.SUSPENDED: [],
        consts.AUGMENTED: [],
        consts.OTHER: [],
    }

    for chord in chord_dict:

        chords = chord.split("/")
        chord_weight = chord_dict[chord]

        for single_chord in chords:
            put_chord_in_group(single_chord, groups_chord_weight_dict, groups_chord_dict, chord_weight)

    return groups_chord_weight_dict, groups_chord_dict


def put_chord_in_group(chord, groups_chords_weight_dict, groups_chords_dict, chord_weight):
    """ Add the chord's weight to the correct group in the dictionary """

    if "dim" in chord:
        add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.DIMINISHED, chord,
                            chord_weight)  # Diminished

    elif "sus" in chord:
        add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.SUSPENDED, chord,
                            chord_weight)  # Suspended

    elif "+" in chord or "aug" in chord:
        add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.AUGMENTED, chord,
                            chord_weight)  # Augmented

    elif "M" in chord or "Ma" in chord or "Maj" in chord or "maj" in chord or "ma" in chord:
        if "7" in chord:
            add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.MAJOR_SEVENTH, chord,
                                chord_weight)  # Major
        else:
            add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.MAJOR, chord,
                                chord_weight)  # Major Seventh

    elif "m" in chord or "min" in chord:
        if "7" in chord:
            add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.MINOR_SEVENTH, chord,
                                chord_weight)  # Minor
        else:
            add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.MINOR, chord,
                                chord_weight)  # Minor Seventh

    elif "dom" in chord or "alt" in chord or "7" in chord:
        add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.DOMINANT_SEVENTH, chord,
                            chord_weight)  # Dominant Seventh

    elif "A" in chord or "B" in chord or "C" in chord or "D" in chord or "E" in chord or "F" in chord or "G" in chord:
        add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.MAJOR, chord, chord_weight)  # Major

    else:
        add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, consts.OTHER, chord, chord_weight)  # Other


def add_to_chords_dicts(groups_chords_weight_dict, groups_chords_dict, key, chord, weight):
    """ Add the chord to the chords dict and the weight to the weights dict """

    groups_chords_weight_dict[key] += weight

    if chord not in groups_chords_dict[key]:
        groups_chords_dict[key].append(chord)



# ############################# Main ##############################

if __name__ == "__main__":
    # get_chords_all_artists("/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_processed")
    # logger.log(all_chords_set)
    # logger.log(len(all_chords_set))

    # delete_buggy_chords_from_single_artist(
    #     "/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_processed/הפרויקט של רביבו.json")

    # delete_buggy_chords_all_artist(
    #     "/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_processed")

    # find_chord("/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_processed", "Cm/[]/[]/Fm/[]/[]/Bb/[]/[]/Eb")

    # get_data_all_artists(directory_path="/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_processed",
    #                      data_file_path="/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/general_data.json")


    # pdb.set_trace()
    #
    # find_famous_all_artists(directory_path="/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_processed")
    #
    # add_data_to_data_json("/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/general_data.json",
    #                       consts.FAMOUS_ARTISTS, global_famous_artists)

    update_general_data_to_chord_groups("/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/general_data.json",
                                        "/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/updated_general_data.json",
                                        True)
