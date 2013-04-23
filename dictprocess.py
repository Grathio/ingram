import argparse
import os
import sys
import codecs
import gzip
import time
from operator import itemgetter
from process_dict import *


def clean_exit(config):
    """ Triggers a clean exit, with removal of in-process files, when Control-C is pressed. """
    print("Canceling!\nRemoving partial files.\n")
    cleanup(config)


def cleanup(config):
    """Cleans up (removes) any partially created files from a previous abnormal termination."""
    # TODO: Be more error-checky.

    # Look for "_currently_woring_on_XX.txt" files. If found, remove all associated files.
    for a in config["char_list"]:
        if os.path.exists(config["outpath"] + a + "/"):
            for b in config["char_list"]:
                fname = config["outpath"] + a + "/" + config["ip_file_name"] + a + b + ".txt"
                if os.path.isfile(fname):
                    print("Removing partial dictionary for [" + a + b + "].")
                    for c in config["char_list"]:
                        tname = config["outpath"] + a + "/" + a + b + c + ".txt"
                        if os.path.isfile(tname):
                            os.remove(tname)
                    os.remove(fname)


def file_consolidate(filename):
    """ Consolidates duplicates and sorts by frequency for speedy lookup. """
    # TODO: Really big files should not be loaded fully into memory to sort them.
    # TODO: Make it more robust, actually checking for errors, etc.

    sorting_hat = []
    in_file = codecs.open(filename, 'r', 'utf-8')
    for data_in in in_file:
        sorting_hat.append(data_in)
    in_file.close()
    sorting_hat.sort()      # Put all the duplicate entires next to each other.

    # Consolidate duplicates while writing to an external file.
    old_ngram = ""
    old_total = 0
    out_file = codecs.open(filename+".tmp", 'w', 'utf-8')
    for i in sorting_hat:
        line = i.split("\t")
        if old_ngram == line[0]:
            old_total += int(line[1])
        else:
            if old_ngram != "" and old_total > 0:
                out_file.write(old_ngram)
                out_file.write("\t")
                out_file.write(str(old_total))
                out_file.write("\n")
            old_ngram = line[0]
            old_total = int(line[1])
    out_file.write(old_ngram)
    out_file.write("\t")
    out_file.write(str(old_total))
    out_file.write("\n")

    out_file.close()
    os.remove(filename)
    os.rename(filename+".tmp", filename)

    # Now sort it by frequency for high-speed lookups. TODO: put this in with the consolidation loop above.
    in_file = codecs.open(filename, 'r', 'utf-8')
    sorting_hat = []
    for data_in in in_file:
        split_data = data_in.split("\t")
        if len(split_data) == 2:
            data_dict = {"name": split_data[0], "value": int(split_data[1])}
            sorting_hat.append(data_dict)
    in_file.close()
    sorting_hat.sort(key=itemgetter('value'), reverse=True)
    out_file = codecs.open(filename + ".tmp", 'w', 'utf-8')
    for item in sorting_hat:
        out_file.write(item["name"])
        out_file.write("\t")
        out_file.write(str(item["value"]))
        out_file.write("\n")
    out_file.close()
    os.remove(filename)
    os.rename(filename + ".tmp", filename)

    return len(sorting_hat)


def process_dict(source_name, outpath, a, b):
    """ Rend a single source n-gram file down to the bare bones that we need. """

    # Be sure the destination folder exists
    if not os.path.exists(outpath + "/" + a + "/"):
        os.makedirs(outpath + "/" + a + "/", mode=0o755)

    # Does "in progress" file exist? If so, skip (probably being worked on by another thread.)
    ip_file_name = outpath + "/" + a + "/_currently_woring_on_" + a + b + ".txt"
    if os.path.isfile(ip_file_name):
        return
    else:
        start_time = time.clock()
        print ("Processing ["+a+b+"]. Started at " + time.asctime(time.localtime())+".")

        out_file = codecs.open(ip_file_name, "w")    # Create the "in progress" file just in case the process gets interrupted.
        out_file.write("This file will be removed when processing this dictionary entry (" + a + b + ") is complete.")
        out_file.close()

        # Create empty files to append entries to
        for c in config["char_list"]:
            out_file = codecs.open(outpath + "/" + a + "/" + a + b + c + ".txt", 'w', 'utf-8')
            out_file.close()

        # Process the input file
        in_file = gzip.open(source_name, "r")
        last_pair = ""
        running_total = 0
        pub_count = 0
        in_count = 0
        for data_in in in_file:
            data_in = data_in.decode('utf-8')
            in_count += 1
            if in_count % 100000 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
            ngram_data = data_in.split("\t")
            this_pair = ngram_data[0]
            this_pair = clean_string(this_pair)
            if this_pair is not None:
                this_year = int(ngram_data[1])
                this_count = int(ngram_data[2])
                pub_count += int(ngram_data[3])
                if this_pair == last_pair:       # Same as the last, keep adding them up.
                    if this_year >= config["startyear"] and this_year <= config["endyear"]:   # If the year is good, add the count
                        running_total += this_count
                else:   # It's a new ngram. Save the old one.
                    if running_total >= config["minfreq"] and pub_count >= config["minpubs"]:   # If we have enough of them add it to the dictionary
                        out_file_name = last_pair[0:3]
                        out_file_name = out_file_name.ljust(3, "_")
                        out_file_name = out_file_name.replace(" ", "_")
                        out_file = codecs.open(outpath + "/" + a + "/" + out_file_name + ".txt", 'a', 'utf-8')
                        out_file.write(last_pair)
                        out_file.write("\t")
                        out_file.write(str(running_total))
                        out_file.write("\n")
                        out_file.close()
                    last_pair = this_pair
                    running_total = 0
                    pub_count = 0
        in_file.close()

        # Optimize the new files (merge duplicates)
        sys.stdout.write("\nOptimizing...")
        out_count = 0
        for c in config["char_list"]:
            sys.stdout.write('.')
            sys.stdout.flush()
            out_count += file_consolidate(outpath + "/" + a + "/" + a + b + c + ".txt")

        end_time = time.clock()
        print("\nReduced [%s%s] from %i to %i in %.1f seconds at %s." % (a, b, in_count, out_count, (end_time - start_time), time.asctime(time.localtime())))

        # remove "in-progress" file since we're done!
        try:
            os.remove(ip_file_name)
        except OSError:                         # If you want to stop the run only after the current data set is complete, remove the in-progress file.
            print("In-progress file not found. Stopping with [%s%s] completed." % (a, b))
            exit(0)


def start_process(config):
    """ Find available dictionaries that need to be processed. """

    # TODO More (e.g. some) error checks on file operations.

    source_files_found = 0
    # Increment through the available source files
    for a in config["char_list"][1:]:           # valid dicts don't start with underscore
        for b in config["char_list"]:
            source_name = config["inpath"] + config["inbase"] + a + b + ".gz"
            if os.path.isfile(source_name):
                # See if this source file has been done
                output_name = config["outpath"] + a + "/" + a + b + "_.txt"    # (or at least the first file created)
                if not os.path.isfile(output_name):
                    process_dict(source_name, config["outpath"], a, b)
                    source_files_found += 1
    if source_files_found == 0:
        print("Note: No source ngram files found matching '%s%s??.gz'" % (config["inpath"], config["inbase"]))
    else:
        print("Processed %i source files." % (source_files_found))


def get_config():
    """ Parse the command line arguments and otherwise get things ready to go. """
    parser = argparse.ArgumentParser(description='Reduce Google N-Gram 2-gram files from http://storage.googleapis.com/books/ngrams/books/datasetsv2.html to something much more manageable.')
    parser.add_argument('-inpath', help='Path to Google ngram v2 files. Default: (current folder)', required=False, default="", metavar="PATH")
    parser.add_argument('-inbase', help='Base file name for incoming nagram files. Default: "googlebooks-eng-us-all-2gram-20120701-"', required=False, default="googlebooks-eng-us-all-2gram-20120701-", metavar="STRING")
    parser.add_argument('-outpath', help='Created dictionary path. Default: dictionary/.', required=False, default="dictionary/", metavar="PATH")
    parser.add_argument('-cleanup', nargs="?", help="Flag to clean up any in-progress files in -outpath. Use after abnormal termination. Don't use when running in another process.", default=False)
    parser.add_argument('-startyear', help="Earliest year for acceptable dictionary data. Default: 1972", required=False, default=1972, type=int, metavar="YEAR")
    parser.add_argument('-endyear', help="Latest year for acceptable dictionary data. Default: 2012", required=False, default=2012, type=int, metavar="YEAR")
    parser.add_argument('-minfreq', help="Minimum n-gram frequency before it's noticed. Default: 250", required=False, default=250, type=int)
    parser.add_argument('-minpubs', help="Minimum number of publications an n-gram is found in before it's noticed. Default: 2", required=False, default=2, type=int)

    config = vars(parser.parse_args())

    #Add some useful info to the config.
    config["char_list"] = "_abcdefghijklmnopqrstuvwxyz"  # Characters used to iterate through the file names.
    config["ip_file_name"] = "_currently_woring_on_"     # Base name of the file created to show the world what's in progress. Used for resuming.

    return config

config = get_config()

# basic validation of the command line input.
if config["startyear"] > config["endyear"] or config["startyear"] > 2012:
    print("Check your date range for dates that actually exist.")
    exit(1)

if config["inpath"] != "":
    if not os.path.exists(config["inpath"]):
        print("Input path '"+config["inpath"]+"' not found.")
        exit(1)

if config["cleanup"] is not False:
    if os.path.exists(config["outpath"]):
        cleanup(config)
    else:
        print("Can't find the output path '" + config["outpath"] + "' to clean up.")
        exit(1)
else:
    try:
        start_process(config)
    except KeyboardInterrupt:  # Let a ^C exit without having to call -cleanup afterward.
        clean_exit(config)

print("Complete!")
