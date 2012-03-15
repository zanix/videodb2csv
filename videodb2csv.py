#!/bin/python
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

# If you have smb:// paths you will have to enable xbmc web interface so we can get the filesize
# You will have to configure these too
username = 'xbmc'
password = 'xbmcpass'
baseurl = '192.168.1.1:8080' # Don't forget the port if it is not 80


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


# CSV header
def printHeader():
    print '"Title","Year","Filesize","Bytes","Width","Height","Videocodec","Audiocodec","IMDB","Filename","Fullpath"'


# Fix path issues
def correctPath(path):
    if path.find("stack://") >- 1:
        path = path.replace("stack://", "")
        path = path.replace(" , ", "*")
        path = path.replace(",,", ",")
    return path


# convert filesize bytes to human readable format
def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size


# Usage instructions
if len(sys.argv) !=2 :
    sys.stderr.write("usage: "+sys.argv[0]+" path/to/videodb.xml [> output.csv]\r\n")
    sys.exit(1)

#print csv header
printHeader()

# open the file
f = open(sys.argv[1], "r")
fc = f.read()

#get all movies
movies = getElems(fc, "movie")

#loop through each movie
for movie in movies:
    path = getElem(movie, "filenameandpath")
    #smb path must use xbmc web interface to get filesize
    if 'smb://' in path:
        url_path = urllib.quote_plus(path)
        xbmc_command = 'http://%s:%s@%s/xbmcCmds/xbmcHttp?command=FileSize(%s)' % \
            (username, password, baseurl, url_path)
        filesize_smb_f = urllib.urlopen(xbmc_command)
        bytez = filesize_smb_f.read()
        bytez = re.sub("\D", "", bytez)
        #bytez = bytesstrip() 
        if not bytez > 0: continue #file not found, skip it
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
    print '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % \
        (title, year, filesize, bytez, width, height, vcodec, acodec, imdb, filename, fullpath)