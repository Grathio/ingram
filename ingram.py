"""A proofreading tool using Google's N-gram corpus."""

import argparse
from cleanstring import *
import codecs
import csv
import os
import sys


def find_frequency(dictionary_location, s):
    """Reports the raw frequency of the two word string [s] in the specified dictionary location."""
    frequency = 0
    s = clean_string(s)
    if s == "":
        return None
    else:
        # See if the appropriate dictionary exists
        path = dictionary_location + s[0]
        if os.path.exists(path):
            file_name = path + "/" + s[0]
            if len(s) < 2 or s[1] == " ":
                file_name += "_"
            else:
                file_name += s[1]
            if len(s) < 3 or s[2] == " ":
                file_name += "_"
            else:
                file_name += s[2]
            file_name += ".txt"
            if os.path.isfile(file_name):
                # Read through the dictionary until we find a match (or not.)
                in_file = codecs.open(file_name, 'r', 'utf-8')
                for data_in in in_file:
                    data_list = data_in.split("\t")
                    if data_list[0] == s:
                        frequency = int(data_list[1])
                        break
                in_file.close()
            else:
                frequency = None    # No dictionary found for this guy.
    return frequency


def whitelisted(config, word):
    """Report True if the word is in the whitelist or should otherwise be given a passing grade."""
    for char in word:
        ascii = ord(char)
        if ascii >= 48 and ascii <= 57:
            return True      # Numbers get a free pass
    word = strip_word(word)
    if word in config["custom_dict"]:
        return True
    return False


def report_familiarity(config, word_trio, previous_report={}):
    """Takes a three word list and returns the familiarity rating for the one in the middle."""
    edge_frequency = config["maxfreq"] * 0.7       # How much artificial frequency is added to edge words. (Very first and last words.)
    report = {"word": word_trio[1]}

    if whitelisted(config, word_trio[1]):
        report["frequency_before"] = config["maxfreq"]
        report["frequency_after"] = config["maxfreq"]
        report["score"] = 100
        return report

    if whitelisted(config, word_trio[0]):
            report["frequency_before"] = config["maxfreq"]
    else:
        if "frequency_after" in previous_report and type(previous_report["frequency_after"]) == int:
            report["frequency_before"] = previous_report["frequency_after"]
        else:
            report["frequency_before"] = find_frequency(config["dict"], word_trio[0]+" "+word_trio[1])
    frequency_before = report["frequency_before"]

    if whitelisted(config, word_trio[2]):
        report["frequency_after"] = config["maxfreq"]
    else:
        report["frequency_after"] = find_frequency(config["dict"], word_trio[1]+" "+word_trio[2])
    frequency_after = report["frequency_after"]

    if frequency_before is None and frequency_after is None:
        frequency_before = 0
        frequency_after = 0
    else:   # It's either the very first or very last word. Artificially boost its rating accordingly.
        if frequency_before is None:
            frequency_before = edge_frequency
        if frequency_after is None:
            frequency_after = edge_frequency
    if frequency_before > config["maxfreq"]:
        frequency_before = config["maxfreq"]
    if frequency_after > config["maxfreq"]:
        frequency_after = config["maxfreq"]
    report["score"] = frequency_before + frequency_after
    if frequency_before == 0 or frequency_after == 0:
        report["score"] -= report["score"] * (config["missinghit"]/100)

    # Normalize the number 0-100
    report["score"] = int(((report["score"] / 200) * 100)/(config["maxfreq"]/100))
    return report


def start_report(config):
    """ Does the housekeeping necessary before saving/displaying the report."""
    out_string = ""
    if config["out"] is not None:            # Remove any existing file if we're saving one.
        if os.path.isfile(config["out"]):
            os.remove(config["out"])
    if config["type"] == "full_html":
        out_string = """<!doctype html>\n<html lang="en">\n<head>\n\t<meta charset="utf-8">\n\t<title>"""
        out_string += config["in"]
        out_string += """</title>\n\t<meta name="description" content="Ingram processed text.">\n\t<meta name="author" content="Ingram">\n\t<link rel="stylesheet" href="ingram.css">\n</head>\n<body>\n<p>"""

    if config["out"] is not None:
        out_file = codecs.open(config["out"], 'a', 'utf-8')
        out_file.write(out_string)
        out_file.close()


def end_report(config):
    """ Does the housekeeping necessary after saving/displaying the report."""
    out_string = ""
    if config["type"] == "full_html":
        out_string = "\n\t</p>\n</body>\n</html>\n"

    if config["out"] is not None:
        out_file = codecs.open(config["out"], 'a', 'utf-8')
        out_file.write(out_string)
        out_file.close()


def show_report(config, report, fragment=""):
    """ Display/save a line of data in the requested output format. """
    if fragment != "":
        fragment = " " + fragment
    if config["type"] == "text":
        if "score" in report:
            out_string = report["word"] + fragment + "\t" + str(report["score"]) + "\n"
        else:
            out_string = report["word"] + fragment + "\t\n"
    elif config["type"] in ["html", "full_html"]:
        if "score" in report:
            class_number = round((report["score"]+9) / 10) * 10
            if config["type"] == "full_html":
                out_string = '<span class="ngram%i ngramPopup">%s%s<span>Score:&nbsp;%i<br>Frequency&nbsp;before:&nbsp;%s<br>Frequency&nbsp;after:&nbsp;%s</span></span> ' % (class_number, report["word"], fragment, report["score"], report["frequency_before"], report["frequency_after"])
            else:
                out_string = '<span class="ngram%i">%s</span>%s ' % (class_number, report["word"], fragment)
        else:
            out_string = report["word"] + " "
        if "\n" in report["word"]:
            out_string += "</p>\n<p>"
    elif config["type"] == "tsv":
        out_string = str(config["word_count"]) + "\t" + report["word"] + fragment + "\t" + str(report["score"]) + "\t" + str(report["frequency_before"]) + "\t" + str(report["frequency_after"]) + "\n"

    if config["type"] == "csv":   # CSV writer does its own wacky thing.
        if config["out"] is not None:
            out_file = codecs.open(config["out"], 'a', 'utf-8')
            output = csv.writer(out_file, dialect='excel')
            output.writerow([config["word_count"], report["word"], report["score"], report["frequency_before"], report["frequency_after"]])
            out_file.close()
        else:
            output = csv.writer(sys.stdout, dialect='excel')
            output.writerow([config["word_count"], report["word"]+fragment, report["score"], report["frequency_before"], report["frequency_after"]])

    else:    # Dump the output to its chosen locaiton.
        if config["out"] is not None:
            out_file = codecs.open(config["out"], 'a', 'utf-8')
            out_file.write(out_string)
            out_file.close()
        else:
            sys.stdout.write(out_string)


def process_text(config):
    """ Processes the input text. """
    if os.path.isfile(config["in"]):
        if os.path.isfile(config["dict"]+config["custom_dict_name"]):
            in_file = codecs.open(config["in"], 'r', 'utf-8')
            word_trio = ["", "", ""]
            config["word_count"] = 0
            last_report = {}
            for data_in in in_file:
                word_list = data_in.split(" ")
                for word in word_list:
                    if len(strip_word(word)) > 0:
                        word = word.strip(" ")
                        if word not in ["", "\t", "\n", "\r", " "]:
                            word_trio.append(word)
                            word_trio.pop(0)
                            if word_trio[1] != "":
                                report = report_familiarity(config, word_trio, last_report)
                                if "fragment" in last_report:
                                    show_report(config, report, last_report["fragment"])
                                else:
                                    show_report(config, report, "")
                                config["word_count"] += 1
                                last_report = report
                    else:
                        if word not in ["", "\t", "\n", "\r", " "]:   # There's a fragment of something (probably punctuation) save for later.
                            report = {"fragment": word}
                            last_report = report
            # Process the last word in the file.
            word_trio.append("")
            word_trio.pop(0)
            report = report_familiarity(config, word_trio)
            show_report(config, report)

    else:
        print("Error: the input file [%s] was not found." % config["in"])


def add_custom(config):
    """ Add a custom word to the custom dictionary. """

    # Only add it if it doesn't exist yet.
    clean_add_text = config["add"].lower().strip("\n\r\t ")
    if not clean_add_text in config["custom_dict"]:
        f = codecs.open(config["dict"]+config["custom_dict_name"], 'a', 'utf-8')
        f.write("\n"+config["add"])
        f.close()
        load_custom_dict(config)
        print("Word [%s] will now be ignored when using this dictionary." % config["add"])
    else:
        print("Word not added to the dictionary. [%s] is already in the custom dictionary." % config["add"])


def remove_custom(config):
    """ Remove a custom word from the dictionary. """
    if os.path.isfile(config["dict"]+config["custom_dict_name"]):
        in_file = codecs.open(config["dict"]+config["custom_dict_name"], 'r', 'utf-8')
        out_file = codecs.open(config["dict"]+config["custom_dict_name"]+".tmp", 'w', 'utf-8')
        found_count = 0
        clean_remove_text = config["remove"].lower().strip("\n\r\t ")
        for data_in in in_file:
            if not clean_remove_text == data_in.lower().strip("\n\r\t "):
                out_file.write(data_in)
            else:
                found_count += 1
        in_file.close()
        out_file.close()

        os.remove(config["dict"]+config["custom_dict_name"])
        os.rename(config["dict"]+config["custom_dict_name"]+".tmp", config["dict"]+config["custom_dict_name"])
        load_custom_dict(config)
        print("Found and removed %i instances of [%s]." % (found_count, config["remove"]))


def strip_word(word):
    """Converts a word to lowercase and strips out all non alpha characters."""
    stripped = ""
    word = word.lower()
    for char in word:
        ascii = ord(char)
        if ascii >= 97 and ascii <= 122:
            stripped += char
    return stripped


def load_custom_dict(config):
    """ Load the custom dictionary. Returns False if dictionary folder does not exist."""

    config["custom_dict"] = []

    # Create the file if it doesn't exist.
    if not os.path.isfile(config["dict"]+config["custom_dict_name"]):
        f = codecs.open(config["dict"]+config["custom_dict_name"], 'w', 'utf-8')
        f.write("# Custom dictionary white list.\n")
        f.write("# Each entry should be on a line by its self.\n")
        f.close()

    if os.path.exists(config["dict"]):
        if os.path.isfile(config["dict"]+config["custom_dict_name"]):
            # load the file, each line that doesn't start with "#" is a word for the dictionary.
            in_file = codecs.open(config["dict"]+config["custom_dict_name"], 'r', 'utf-8')
            for data_in in in_file:
                if data_in[0] != "#":
                    data_in = strip_word(data_in)
                    data_in = data_in.lower()
                    if len(data_in) > 0:
                        config["custom_dict"].append(data_in)
        return True
    else:
        print("Error: No dictionary found in path [%s]." % config["dict"])
        return False


def get_config():
    """ Parse the command line arguments. """
    parser = argparse.ArgumentParser(description="A tool for checking spelling and grammar using Google's ngram corpus.")
    parser.add_argument('-in', help='Text file to process.', required=False, default="", metavar="FILE")
    parser.add_argument('-out', help='Name to save output. Will be overwritten if it exists. If not defined output is echoed to stdout.', required=False, metavar="FILE")
    parser.add_argument('-type', help='[text, csv, tsv, html, full_html] Type of output to produce.', required=False, default="text", metavar="TYPE")
    parser.add_argument('-dict', help="Dictionary to use. (default /dictionary/)", required=False, default="dictionary/", metavar="PATH")
    parser.add_argument('-add', help="Add a word to the custom whitelist.", required=False, default="", metavar="STRING")
    parser.add_argument('-remove', help="Remove a word from the custom whitelist.", required=False, default="", metavar="STRING")
    parser.add_argument('-maxfreq', help="[Advanced] Frequency hits above this will not improve the familiarity score. Higher = more sensitive. (Default: 20,000.)", default=20000, type=int, required=False, metavar="INT")
    parser.add_argument('-missinghit', help="[Advanced] Percentage points removed from a word's score if there's no record of a pairing. Higher = missing matches are more visible. (Default: 55)", default=55, type=int, required=False, metavar="INT")
    config = vars(parser.parse_args())

    # Add some useful things to the config.
    config["custom_dict_name"] = "custom.txt"

    # Some super basic verification.
    if config["type"] not in ["text", "html", "csv", "full_html", "tsv"]:
        print("Error: Output type [%s] not recognized." % config["type"])
        exit(1)

    return config


# Begin Main
config = get_config()
if not load_custom_dict(config):
    config = None
if config is not None:
    if config["add"] != "":
        add_custom(config)
    if config["remove"] != "":
        remove_custom(config)
    if config["in"] != "":
        start_report(config)
        process_text(config)
        end_report(config)
