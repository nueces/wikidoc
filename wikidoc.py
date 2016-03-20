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


def substitute(section, filename):
	section = section.replace("###_WIKIDOC_GENDATE_###", time.strftime("%d.%m.%Y"))
	section = section.replace("###_WIKIDOC_TITLE_###", getTitleFromFilename(filename))
	return section


def parseFile(path,file):
	html = ""

	with open (path + file, "r") as myfile:
		html = myfile.read()
		# remove wikidoc only comments (start and stop, keep the content!)
		html = html.replace("<!-- WIKIDOC PDFONLY","")
		html = html.replace("WIKIDOC PDFONLY -->","")

	return substitute(html,file)


def extractStartStop(startString, endString , filestr):
	start = filestr.find(startString)
	end = filestr.find(endString)
	if start == -1 or end == -1 or start > end:
		return ""

	return filestr[start+len(startString):end].strip('\n\r ')

	
def readGlobalWikidocComments(file):
	wikidocConfig = {}
	wkhtmltopdfConfig = []

	try:
		with open (file, "r") as myfile:
			filecontent = myfile.read()
			wikidocConfig["HEAD"] = extractStartStop("<!-- WIKIDOC HTMLHEAD", "WIKIDOC HTMLHEAD -->" , filecontent)
			wikidocConfig["FOOT"] = extractStartStop("<!-- WIKIDOC HTMLFOOT", "WIKIDOC HTMLFOOT -->" , filecontent)
			if (not wikidocConfig["HEAD"]  or  not wikidocConfig["FOOT"]):
					print ("Could not find HTMLHEAD and/or HTMLFOOT comment in home.md. Aborting.\n")
					exit()
					
			wikidocConfig["COVER"] = extractStartStop("<!-- WIKIDOC COVER", "WIKIDOC COVER -->" , filecontent)
			wikidocConfig["COVER"] = substitute(wikidocConfig["COVER"],"Cover.md")

			wikidocConfig["TOCXSL"] = extractStartStop("<!-- WIKIDOC TOCXSL", "WIKIDOC TOCXSL -->" , filecontent)

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
(wikidocConfig, wkhtmltopdfConfig) = readGlobalWikidocComments(pathWiki + "Home.md")


# Build html, start with global head
html = list()
html.append(wikidocConfig["HEAD"])


# Append Home.md
html.append(parseFile(pathWiki, "Home.md"))


# get all markdown files
files = sorted(getFilesInDirectory(pathWiki), key=lambda s: s.lower())


# Append all other files, except Home.md
for file in files:
	if file.endswith(".md") and not file == "Home.md":
		html.append(parseFile(pathWiki, file))


# Append global foot
html.append(wikidocConfig["FOOT"])


tempfiles = list()

# Write html into temp file
tempfiles.append(wikidocConfig["filename"] + ".html")
with open(wikidocConfig["filename"] + ".html", "w") as html_file:
    html_file.write("\n".join(html))

# Write cover into temp file - if present
if (wikidocConfig["COVER"]):
	tempfiles.append(wikidocConfig["filename"] + ".cover.html")
	with open(wikidocConfig["filename"] + ".cover.html", "w") as cover_file:
    		cover_file.write(wikidocConfig["HEAD"] + "\n" + wikidocConfig["COVER"] + "\n" + wikidocConfig["FOOT"])

# Write tocxsl into temp file - if present
if (wikidocConfig["TOCXSL"]):
	tempfiles.append(wikidocConfig["filename"] + ".toc.xsl")
	with open(wikidocConfig["filename"] + ".toc.xsl", "w") as toc_file:
    		toc_file.write(wikidocConfig["TOCXSL"])



# Build cmd for wkhtmltopdf
cmd = pathWkhtmltopdf + " " + " ".join(wkhtmltopdfConfig) + " "
if (wikidocConfig["COVER"]):
	cmd = cmd + "cover " + wikidocConfig["filename"] + ".cover.html "
if (wikidocConfig["TOCXSL"]):
	cmd = cmd + "toc --xsl-style-sheet " + wikidocConfig["filename"] + ".toc.xsl "
cmd = cmd + wikidocConfig["filename"] + ".html" +  " " + wikidocConfig["filename"]


# Convert HTML to PDF
try:
	subprocess.call(cmd, shell=True)
except OSError:
	print "Something went wrong calling " + pathWkhtmltopdf + " on " + wikidocConfig["filename"] + ".html"


# Delete all created temp files
for tempfile in tempfiles:
	if (os.path.isfile(tempfile)): 
		os.unlink(tempfile)
