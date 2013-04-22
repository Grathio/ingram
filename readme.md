# Ingram
A tool for checking spelling and grammar using Google's N-gram corpus.

## Description
Ingram analyzes the familiarity of text using [Google's Ngram collection](http://storage.googleapis.com/books/ngrams/books/datasetsv2.html), a data set that shows the frequency of words and phrases gleaned from scanning 4.5 million books. Feeding it English text will result in output that highlights uncommon words or word usage.

Use it to catch things that spelling and grammar checkers won't. Take the sentence "The dessert sand flowed trough his fingers." All the words are spelled correctly and Word (2011) doesn't find any grammatical errors. But Ingram knows that "dessert" is rarely paired with "sand" and "trough" is rarely paired with "flowed" or "his".

* Unlike most spell checkers, Ingram uses surrounding words to see if it's the word you intend.
* Unlike grammar checkers, it doesn't try to apply the arbitrary rules of grammar, but compares your usage to how others have used those words before. This isn't necessarily more accurate (though it often is) but it's different, and will catch things that are grammatically correct but wrong. (eg: The dessert sand flowed trough his fingers.)

It **_doesn't_** offer suggestions, it merely identifies suspicious words. It's up to you to figure out that "dessert" should be "desert" and "trough" should be "through". It's not intended to be a replacement for spelling or grammar checkers, but a supplement to them.

The default dictionary is from the most common American English word pairs from 1972 to 2012, but tools are provided to make dictionaries for difference languages, frequencies, or time periods. (That's right, you can make a custom dictionary to see how accurate your attempt at 1850's British English is.)

## Use
Ingram is a Python script that runs on Python 2.7+ (likely 3.0+ as well, but untested) with the standard library.

### Setup
Before you use it the first time you need to unzip the dictionary somewhere. (By default it looks for `/dictionary/`.) Or you can make your own if you want. (See below.)

You will also need a plain text file of the document you want to scan.

### Syntax
The most basic use is:
`python ingram.py -in [input file]`
Which will return column of words and familiarity ratings separated by tabs. 

Full syntax:

	-in [FILE] : File name for input.
	-out [FILE] : File for output. Will overwrite any existing file. If not
		specified the output is dumped to stdout.
	-type [text, csv, tsv, html, full_html] : Type of output to dispense.
	-dict [PATH] : Path of the dictionary files (default "/dictionary/")
	-add [STRING] : Add a word to the custom white list.
	-remove [STRING] : Remove a word from the custom white list. (The custom
		whitelist is saved at /dictionary/custom.txt)

	Advanced:
		These settings let you tune the familiarity ratings. 
		-maxfreq [INT] : Frequency hits above this will not improve the
			familiarity score. Higher = more sensitive. (Default: 20000.)
		-missinghit [INT] : Percentage points removed from a word's score if
	 		there's no record of a pairing. Higher = missing matches are more
	 		visible. (Default: 55)

### Output formats
Ingram provides a number of outputs types that can be piped or send to a designated file.

#### text (default)
Each entry is a word (with any attached punctuation) a tab, and a familiarity rating. One entry per line.

		The	85
		quick	100
		brown	100
		fox	99
		…

#### csv
Extended information, separated by commas. The CSV file is Excel-compatible. Each line contains:

- Number of the word (starting with 0)
- Original word in the document, including any attached punctuation.
- Familiarity rating
- Raw n-gram frequency from the word previous (if any) and this word.
- Raw n-gram frequency from this word and the next word (if any).

		0,The,85,,2497757
		1,quick,100,2497757,52060
		2,brown,100,52060,51221
		3,fox,99,51221,19864
		…

#### tsv
Similar to 'csv' but uses tabs as delimiters. It also doesn't do any escaping of strings, so be sure to strip tabs before processing.

#### html
Generates a snippet of HTML (no head or body tags) with each word surrounded by CSS styling indicating the familiarity rating. This is a quick way to visually see the suspicious words. A basic ingram.css file is provided as a starting point.

#### full_html
Wraps the output of the 'html' into a very basic (valid html5) page and links to the ingram.css style sheet. Mousing over words will reveal more information.

### Familiarity ratings
Familiarity ratings range from 0-100 inclusive. A zero rating means that it didn't find any references to the word being paired with one before or after it. A 100 means it's very common pairing or that a word in the pair has been whitelisted. In general a familiarity rating below 50 is suspicious.

### Caveats 
- It works much better (fewer false positives) on formal text than on casual text.
- It's not particularly speedy. On my solid state drive it processes about 34 words per second. Most of this is because it stores its dictionaries as flat text files.
- Comma separated sequences, end of sentence period, quotes, hyphens, etc. can trigger a false positive. At the moment it throws out all punctuation, even sentence-ending periods.
- Any word with numbers in it is ignored.
- It ignores punctuation and capitalization. So "We're" = "were". This will occasionally cause false negatives. And positives.

## Making custom dictionaries
Use the `dictprocess.py` script for distilling Google's 100+GB of gzipped n-grams into something much more manageable.

You'll need to download the source ngram data from <http://storage.googleapis.com/books/ngrams/books/datasetsv2.html> The script should work with any English language 2-gram files. It does some rather ruthless Unicode conversion, so languages not using Roman characters will suffer mightily.

Distilling the massive source down to something more usable with this script takes a lot of time. A single processor on my 1.7 GHz Macbook Air will takes about 2.5 hours to grind through through 1GB of gzipped source.

The easiest way to speed this up is to run `cleanstring.py` through [Cython](http://cython.org/) (without any optimizations) which gives a 20-30% speed increase.

It's not multi-threaded, but you can generally run multiple versions of the script concurrently. It's aware that other scripts are running and won't process the same entires.

If you want to interrupt the processing, the usual control-C will interrupt the process and remove any partial files. 

If you want it to stop when its done with the current ngram file (and thus not lose any parically processed records) find and delete the corresponding "_currently_woring_on_??.txt" in the /dictionary/ folder. (Where "??" are the two letters of the in-progress ngram file.)

Next time you resume dictionary processing it will continue from where it left off.

## Potential Improvements & Other Thoughts
This is my "I think I'll learn Python" project. The code should be clear and readable, but that doesn't mean it's sensible, robust, or particularly pythonic.

- The custom dictionary building process would be a good one to adapt to Amazon Web Services or some other cloud computing so that it doesn't take 100+GB download and days of processing power just to change the dictionary.

- Because it's a learning project it only uses the standard library. There are no shortage of external modules that could improve it.

- The whole punctuation thing. It doesn't handle the end of sentences well. Or at all. The dictionaries contain the "_end_" keyword which marks when a word is used at the end of a sentence, but it's currently unused. Keeping periods and commas in the dictionary would reduce false hits, but vastly expand the dictionary.

- It would be handy to be able to handle input containing markup. (It handles Markdown pretty well.)

- Articles like "the" can cause missed detection. (eg: "He drank the bear.") Using 3-grams (or more) would help catch these, but the 3-gram data set is more than 10x larger than the 2-gram set and I'm not certain it's worth the extra effort.

- There are a great many ways it could be made faster.

- The dictionary creation process currently creates some cruft. It's a very small percentage of the data. Some if from Google's not quite perfect OCR, some is from in gram's dictionary creation. It would be good to understand the latter.

- The distilled dictionary files are very close to being natural language Markov chains. I don't know what to do with that information, but there it is.

## Credits
Thanks to [Jay Graves](http://blog.bockris.com/), who came up with the original idea and did some early work in this direction.

Thanks to the thousands of people who have publicly shared some code that I have learned from.

And thanks to Google for collecting and then sharing a ridiculous amount of data. [http://books.google.com/ngrams/]()

## License
The dictionary is produced from data from [Google](http://storage.googleapis.com/books/ngrams/books/datasetsv2.html) under the [Creative Commons Attribution 3.0 Unported License](http://creativecommons.org/licenses/by/3.0/).

Unless otherwise specified this software is released under the MIT license:

The MIT License (MIT)
Copyright (c) 2013 Steve Hoefer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.