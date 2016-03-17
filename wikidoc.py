#!/usr/bin/python

##############################################################################
#                                                                            #
# Copyright 2016, John Bieling                                               #
#                                                                            #
# This program is free software; you can redistribute it and/or modify       #
# it under the terms of the GNU General Public License as published by       #
# the Free Software Foundation; either version 2 of the License, or          #
# any later version.                                                         #
#                                                                            #
# This program is distributed in the hope that it will be useful,            #
# but WITHOUT ANY WARRANTY; without even the implied warranty of             #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
# GNU General Public License for more details.                               #
#                                                                            #
# You should have received a copy of the GNU General Public License          #
# along with this program; if not, write to the Free Software                #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA #
#                                                                            #
##############################################################################

import sys, string, os, time, subprocess

def getFilesInDirectory(dir, FailOnError = True):
	if os.path.exists(dir):
		return next(os.walk(dir))[2]
	elif not FailOnError:
		return False
	else:
		print "Folder <"+ dir +"> does not exist. Aborting."
		sys.exit(0)

def getTitleFromFilename(file):
	base = os.path.splitext(file)[0]
	return base.replace("-"," ")

def includeFile(path,file):
	html = list()
	if not file == "Home.md":
		html.append("<h1>" + getTitleFromFilename(file) + "</h1>")
	with open (path + file, "r") as myfile:
    		html.append(myfile.read())
	
	return "\n".join(html)

def extractStartStop(startString, endString , filestr):
	return filestr[filestr.find(startString)+len(startString):filestr.find(endString)].strip('\n\r ')


def readComments(file):
	wikidocConfig = {}
	wkhtmltopdfConfig = []

	try:
		with open (file, "r") as myfile:
    			filecontent = myfile.read()
			wikidocConfig["HEAD"] = extractStartStop("<!-- WIKIDOC HEAD", "WIKIDOC HEAD -->" , filecontent)
			wikidocConfig["FOOT"] = extractStartStop("<!-- WIKIDOC FOOT", "WIKIDOC FOOT -->" , filecontent)

			parameters = extractStartStop("<!-- WIKIDOC CONFIG", "WIKIDOC CONFIG -->" , filecontent).splitlines()
			for line in parameters:
				stripline = line.strip()
				if stripline.startswith("--filename "):
					wikidocConfig["filename"] = stripline.replace("--filename ","").strip()
				else:
					wkhtmltopdfConfig.append(stripline)

			if not wikidocConfig.has_key("filename"):
				wikidocConfig["filename"] = "wikidoc.pdf"

			return (wikidocConfig, wkhtmltopdfConfig)

	except Exception as error: 
    		print "Could not read file " + file + " or did not find required wikidoc comments!\n"
		exit()

	


##############################################################################
### Main #####################################################################
##############################################################################


# Get path-to-wkhtmltox and path to wiki
if not len(sys.argv) == 3:
	print "usage:\n\t" + sys.argv[0] + " <path-to-wkhtmltopdf> <path-to-wiki-folder>\n\n"
	exit()

pathWkhtmltopdf = sys.argv[1]
pathWiki = sys.argv[2]

if not pathWiki.endswith("/"):
	pathWiki = pathWiki + "/"

 

# Home.md must be present and it must contain special comments with additional
# informations
(wikidocConfig, wkhtmltopdfConfig) = readComments(pathWiki + "Home.md")

# Build html
html = list()
html.append(wikidocConfig["HEAD"].replace("###_WIKIDOC_GENDATE_###",time.strftime("%d.%m.%Y")))

# Append Home.md
html.append(includeFile(pathWiki, "Home.md"))

# get all markdown files
files = sorted(getFilesInDirectory(pathWiki), key=lambda s: s.lower())

# Append all other files, except Home.md
for file in files:
	if file.endswith(".md") and not file == "Home.md":
		html.append(includeFile(pathWiki, file))
	
html.append(wikidocConfig["FOOT"])



# Write html into temp file
with open(wikidocConfig["filename"] + ".html", "w") as html_file:
    html_file.write("\n".join(html))


# Convert HTML 2 PDF
try:
	subprocess.call(pathWkhtmltopdf + " " + " ".join(wkhtmltopdfConfig) + " " + wikidocConfig["filename"] + ".html" +  " " + wikidocConfig["filename"], shell=True)
except OSError:
	print "Something went wrong calling " + pathWkhtmltopdf + " on " + wikidocConfig["filename"] + ".html"
	exit()
