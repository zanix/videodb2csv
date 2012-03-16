#!/usr/bin/env python
# This will attempt to convert your XBMC exported library XML into csv format.  It also adds filesize, which for some
# reason was not included in xbmc.
#
# Author: Greg Bosen and an xbmc forum post
# Date: March 12 2012
#
# To Get XBMC XML Export: XBMC->Settings->Video->Export Video Library->Single File->Choose Path
# Script Usage: videodb2csv.py videodb.xml > videodb.csv

import re
import sys
import os
import urllib

from xml.sax.saxutils import unescape
from xml.dom.minidom import parse, parseString
from optparse import OptionParser

# If you have smb:// paths you will have to enable xbmc web interface so we can get the filesize
# You will have to configure these too
username = 'xbmc'
password = 'xbmcpass'
baseurl = '192.168.1.1:8080' # Don't forget the port if it is not 80



# Setup usage and options
usage = "usage: %prog [options] -f parse_file -o output_file\r\n"
parser = OptionParser(usage)
parser.add_option("-f", "--filename", dest = "parsefile", default = False,
                  metavar = "FILE", help = "write output to FILE")
parser.add_option("-o", "--output", dest = "output", default = False,
                  metavar = "FILE", help = "write output to FILE")
parser.add_option("-n", "--nofilesize",
                  action = "store_true", dest = "nofilesize", default = False,
                  help = "exclude filesize lookup")
(options, args) = parser.parse_args()

if options.parsefile is False or options.output is False :
    sys.stderr.write(usage)
    sys.exit(1)


# Gets XML elements
def getElems(fc, elem):
    a = re.findall("<"+elem+">(.+?)</"+elem+">", fc, re.M|re.DOTALL)
    return a

# Gets single XML element
def getElem(fc, elem):
    a = getElems(fc, elem)
    if len(a) > 0:
        return unescape(a[0], {"&apos;": "'", "&quot;": '"'})
    else:
        return ""

# Fix path issues
def correctPath(path):
    if path.find("stack://") >- 1:
        path = path.replace("stack://", "")
        path = path.replace(" , ", "*")
        path = path.replace(",,", ",")
    return path

#filesize human readable format
def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1048576:
        terabytes = bytes / 1048576
        size = '%.2f' % terabytes
    else:
        size = '%.2fb' % bytes
    return size

def clean_video_codec(vcodec):
    #Cleans up codec output
    if vcodec == "divx3low/div3/mpeg-4visual/div3/divx3low" :
        vcodec = "MP4 (DivX 3)"
    elif vcodec == "v_mpeg4/iso/avc/avc/v_mpeg4/iso/avc/avc" :
        vcodec = "MP4 (AVC)"
    elif vcodec == "xvid/xvid/mpeg-4visual/xvid/xvid" :
        vcodec = "MP4 (Xvid)"
    elif vcodec == "divx5/dx50/mpeg-4visual/dx50/divx5" :
        vcodec = "MP4 (DivX 5)"
    elif vcodec == "avc1/avc/avc/avc" or vcodec == "/avc/avc/avc":
        vcodec = "AVC"
    elif vcodec == "xvid":
        vcodec = "Xvid"
    return vcodec

def clean_audio_codec(acodec):
    if acodec == "ac3" or acodec == "ac-3/ac3/ac3":
        acodec = "AC3"
    elif acodec == "mp3/mpegaudio/mpa1l3/mpeg-1audiolayer3" or acodec == "mp3":
        acodec = "MP3"
    elif acodec == "dts/dts/dts" or acodec == "dca":
        acodec = "DTS"
    elif acodec == "aac" or acodec == "aac/a_aac/mpeg4/lc/aaclc":
        acodec = "AAC"
    elif acodec == "vorbis":
        acodec = "Vorbis"
    return acodec


# open the parsefile
f = open(options.parsefile, "r")
fc = f.read()

#get all movies
movies = getElems(fc, "movie")

# open the output file
o = open(options.output, 'w')
#print csv header
o.writelines('"Title","Year","Filesize","Bytes","Width","Height","Videocodec","Audiocodec","IMDB","Filename","Fullpath"')

#loop through each movie
for movie in movies:
    path = getElem(movie, "filenameandpath")
    #o.writelines(path + '\r\n')
    filesize = ""
    bytez = ""
    if options.nofilesize is False:
        #smb path must use xbmc web interface to get filesize
        if 'smb://' in path:
            url_path = urllib.quote_plus(path)
            xbmc_command = 'http://%s:%s@%s/xbmcCmds/xbmcHttp?command=FileSize(%s)' % \
                (username, password, baseurl, url_path)
            filesize_smb_f = urllib.urlopen(xbmc_command)
            bytez = filesize_smb_f.read()
            bytez = re.sub("\D", "", bytez)
            #bytez = bytesstrip()
            if not bytez > 0:
                continue #file not found, skip it
            filesize = convert_bytes(bytez)
        #get path via os
        elif os.path.exists(path) :
            bytez = os.path.getsize(path)
            filesize = convert_bytes(bytez)
        #can't find file, skip to next movie
        else :
            continue
    #get xml elements
    title = getElem(movie, "title").replace("\"", "'")
    year = getElem(movie, "year")
    width = getElem(movie, "width")
    height = getElem(movie, "height")
    codecs = getElems(movie, "codec")

    #not elegent way to get codecs
    if codecs:
        acodec = codecs.pop()
        acodec = acodec.replace(" ", "")
    if codecs:
        vcodec = codecs.pop()
        vcodec = vcodec.replace(" ", "")
    imdb = getElem(movie, "id")
    fullpath = correctPath(getElem(movie, "filenameandpath"))
    filename = path.replace(getElem(movie, "basepath"), "")
    #print csv line
    # "Title","Year","Filesize","Bytes","Width","Height","Videocodec","Audiocodec","IMDB","Filename","Fullpath"
    o.writelines('"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % \
        (title, year, filesize, bytez, width, height, vcodec, acodec, imdb, filename, fullpath))
