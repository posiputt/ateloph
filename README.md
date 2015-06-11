# ateloph
a logging irc bot written in python

files
-----

ateloph.py	the main program. start this to start logging
index.php	put this in the same directory as the log-files
		it generates an html document with links to each
		logfile
viewlog		this goes into the same directory as index.php
		it shows the a log file specified by the
		GET-parameter l=<filename>, and makes clickable
		hyperlinks from any word starting with either of
		the following: 'http://', 'https://', or 'ftp://'
the log files	simple text files each containing the log of a
		specific date.
