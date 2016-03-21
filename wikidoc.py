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
			
		# define search strings
		startstring = '<!-- WIKIDOC PDFONLY'
		endstring = 'WIKIDOC PDFONLY -->'
		
		# reverse loop through all PDFONLY sections 
		start = html.rfind(startstring)
		end = html.rfind(endstring)+len(endstring)
		while not start == -1 and not end == -1 and start < end:
			# get arary of lines of section - first and last line is to be dropped
			sectionlines = html[start:end].splitlines()
			
			# get name of section (if any) from first line
			name = (sectionlines[0].replace(startstring,"")).strip()
			
			# get section without enclosing html comment tags
			section = substitute("\n".join(sectionlines[1:-1]),file).strip()
			
			# generate images from PDFONLY segments
			if (generateImages and name):
				with open("wikidoc_image.html", "w") as image_file:
					image_file.write(wikidocConfig["HEAD"] + "\n" + section + "\n" + wikidocConfig["FOOT"])
				
				# Convert HTML to IMAGE
				print " -> Converting PDFONLY section <" + name + "> to PNG."
				cmd = pathWkhtmltoimage + " --width 700 wikidoc_image.html " + pathWiki + "generated-images/" + name + ".PNG"
				try:
					subprocess.call(cmd, shell=True)
				except OSError:
					print "Something went wrong converting PDFONLY section to PNG."

				# Delete temp file
				os.unlink("wikidoc_image.html")
		
			# replace section by modified section
			html = html[:start] + section + html[end:]
			start = html.rfind(startstring)
			end = html.rfind(endstring)+len(endstring)
		

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


generateImages = True
# Check if wkhtmltoimage is present
pathWkhtmltoimage = os.path.dirname(pathWkhtmltopdf) + "/wkhtmltoimage"
if (not os.path.isfile(pathWkhtmltoimage)):
	print "PDFONLY segements will not be saved as images, because 'wkhtmltoimage'"
	print "is not found next to wkhtmltopdf.\n"
	generateImages = False	

# Check, if generated-images folder exists in pathWiki
if (generateImages and not os.path.isdir(pathWiki + "generated-images")):
	print "PDFONLY segements will not be saved as images, because 'generated-images'"
	print "folder not found in wiki repository.\n"
	generateImages = False

11
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


tempfiles = dict()

# Write html into temp file
tempfiles["main"] = "wikidoc.html"
with open(tempfiles["main"], "w") as html_file:
    html_file.write("\n".join(html))

# Write cover into temp file - if present
if (wikidocConfig["COVER"]):
	tempfiles["cover"] = "wikidoc_cover.html"
	with open(tempfiles["cover"], "w") as cover_file:
    		cover_file.write(wikidocConfig["HEAD"] + "\n" + wikidocConfig["COVER"] + "\n" + wikidocConfig["FOOT"])

# Write tocxsl into temp file - if present
if (wikidocConfig["TOCXSL"]):
	tempfiles["toc"] = "wikidoc_toc.xsl"
	with open(tempfiles["toc"], "w") as toc_file:
    		toc_file.write(wikidocConfig["TOCXSL"])



# Build cmd for wkhtmltopdf
cmd = pathWkhtmltopdf + " " + " ".join(wkhtmltopdfConfig) + " "
if (tempfiles["cover"]):
	cmd = cmd + "cover " + tempfiles["cover"] + " "
if (tempfiles["toc"]):
	cmd = cmd + "toc --xsl-style-sheet " + tempfiles["toc"] + " "
cmd = cmd +tempfiles["main"] + " " + pathWiki + wikidocConfig["filename"]


# Convert HTML to PDF
try:
	subprocess.call(cmd, shell=True)
except OSError:
	print "Something went wrong calling " + pathWkhtmltopdf + " on " + wikidocConfig["filename"] + ".html"


# Delete all created temp files
for tempfile in tempfiles.itervalues():
	if (os.path.isfile(tempfile)): 
		os.unlink(tempfile)
