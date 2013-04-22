import unicodedata
def clean_string(s):
	''' Formats an ngram how we like, discarding any info we don't like.'''
	try:
		s = unicodedata.normalize("NFKD", s.decode('utf-8', 'ignore'))
	except UnicodeEncodeError:
		return ""	#some crazy untranslatable unicode got in here, 
	s = s.lower()
	#rebuild the string without numbers or punctuation
	new_string = ""
	for i in s:
		skip = False
		c = ord(i)
		if c < 97 or c > 122: #Non alpha
			if c >= 48 and c <= 57: 
				return ""        # Don't parse entries with numbers
			if c != 32 and c != 95: skip = True
		if skip == False: new_string += i

	#remove google-added cruft.
	remove = ["_adj", "_verb", "_noun", "_adj", "_adv", "_pron", "_det", "_adp", "_num", "_conj", "_prt", "_x", "__"] #double underscore at the end is to remove some cruft
	for i in remove: new_string= new_string.replace(i,"")

	#check to see if it's still 2 (or more) words
	new_string = new_string.rstrip(" ").lstrip(" ")
	# Sometimes there is only an "_" remaining as a word. Check for it.
	if new_string.endswith(" _"):
		new_string = ""
	if new_string.find(" ") == -1:
		new_string = ""	# If, after all this reduction, it's only one word it's not what we need.

	return new_string