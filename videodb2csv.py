#!/bin/python
#This will attempt to convert your XBMC exported library XML into csv format.  It also adds filesize, which for some 
#reason was not included in xbmc.
#
#Author: Greg Bosen and an xbmc forum post
#Date: March 12 2012
#
#To Get XBMC XML Export: XBMC->Settings->Video->Export Video Library->Single File->Choose Path
#Script Usage: videodb2csv.py videodb.xml > videodb.csv

import re,sys,os,urllib
from xml.sax.saxutils import unescape

#If you have smb:// paths you will have to enable xbmc web interface so we can get the filesize
#You will have to configure these too
username='xbmc'
password='xbmcpass'
baseurl='192.168.1.1:8080' #dont forget the port if not 80

#gets XML elements
def getElems(fc,elem):
	a=re.findall("<"+elem+">(.+?)</"+elem+">",fc,re.M|re.DOTALL)
	return a

#gets single XML element
def getElem(fc,elem):
	a=getElems(fc,elem)
	if len(a)>0:
		return unescape(a[0], {"&apos;": "'", "&quot;": '"'})
	else:
		return ""
#csv header
def printHeader():
	print '"Title","Year","Filename","Filesize","Width","Height","Videocodec","Audiocodec","IMDB","Fullpath"'

#fix path issues
def correctPath(path):
	if path.find("stack://")>-1:
		path=path.replace("stack://","")
		path=path.replace(" , ","*")
		path=path.replace(",,",",")
	return path

#filesize human readable format
def convert_bytes(bytes):
		bytes=float(bytes)
		if bytes >= 1099511627776:
				terabytes=bytes / 1099511627776
				size='%.2fT' % terabytes
		elif bytes >= 1073741824:
				gigabytes=bytes / 1073741824
				size='%.2fG' % gigabytes
		elif bytes >= 1048576:
				megabytes=bytes / 1048576
				size='%.2fM' % megabytes
		elif bytes >= 1024:
				kilobytes=bytes / 1024
				size='%.2fK' % kilobytes
		else:
				size='%.2fb' % bytes
		return size

#usage instructions
if len(sys.argv) !=2 :
	sys.stderr.write("usage: "+sys.argv[0]+" path/to/videodb.xml [> output.csv]\r\n")
	sys.exit(1)

#printh csv header
printHeader()
f=open(sys.argv[1],"r")
fc=f.read()
#get all movies
movies=getElems(fc,"movie")
#loop through each movie
for movie in movies:
	path=getElem(movie,"filenameandpath")
	#smb path must use xbmc web interface to get filesize
	if 'smb://' in path :
		url_path=urllib.quote_plus(path)
		filesize_smb_f=urllib.urlopen('http://'+username+':'+password+'@'+baseurl+'/xbmcCmds/xbmcHttp?command=FileSize('+url_path+')')
		filesize=filesize_smb_f.read()
		filesize=re.sub("\D", "", filesize)
		filesize=filesize.strip()
		if not filesize > 0: continue #file not found, skip it
		filesize=convert_bytes(filesize)
	#get path via os
	elif os.path.exists(path) : 
		filesize=convert_bytes(os.path.getsize(path))
	#can't find file, skip to next movie
	else :
		continue
	#get xml elements
	title=getElem(movie,"title").replace("\"","'")
	year=getElem(movie,"year")
	width=getElem(movie,"width")
	height=getElem(movie,"height")
	codecs=getElems(movie,"codec")
	#not elegent way to get codecs
	if codecs : 
		acodec=codecs.pop()
		acodec=acodec.replace(" ","")
	if codecs : 
		vcodec=codecs.pop()
		vcodec=vcodec.replace(" ","")
	imdb=getElem(movie,"id")
	fullpath=correctPath(getElem(movie,"filenameandpath"))
	filename=path.replace(getElem(movie,"basepath"),"")
	#print csv line
	print '"'+title+'","'+year+'","'+filename+'","'+filesize+'","'+width+'","'+height+'","'+vcodec+'","'+acodec+'","'+imdb+'","'+fullpath+'"'