import json
from os import listdir
from os.path import isfile, join
from os import walk
import pdb
import logger

import consts


all_chords_set = set()


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


if __name__ == "__main__":
    get_chords_all_artists("/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_edit")
    logger.log(all_chords_set)
    logger.log(len(all_chords_set))

    # delete_buggy_chords_from_single_artist(
    #     "/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_edit/הפרויקט של רביבו.json")

    delete_buggy_chords_all_artist(
        "/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_edit")

    # find_chord("/Users/Yuval/Desktop/miniDigitalHumanities/virEnvProj/ChordsAnalizer/json_files_edit", "Cm/[]/[]/Fm/[]/[]/Bb/[]/[]/Eb")
