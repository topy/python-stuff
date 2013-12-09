# -*- coding: utf-8 -*-
from module.plugins.Hook import Hook
import urllib2
#import urllib
from BeautifulSoup import BeautifulSoup
import re
import tmdb
import feedparser
import simplejson as json

def parseFeeds(self):
	movieList = []
	
	#apple feed
	if self.getConfig('rssapple'):
		feed = feedparser.parse('http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/topMovies/xml')
		for item in feed.entries:
			movieList.append(replaceUmlauts( item.title[0:item.title.find('-')]))
	#rottentomatoes feed
	if self.getConfig('rssrottentomato'):
		feed = feedparser.parse('http://www.rottentomatoes.com/syndication/rss/top_movies.xml')
		for item in feed.entries:
			movieList.append(replaceUmlauts( item.title[4:] ))
			
	#kino.de charts
	if self.getConfig('rsskinode'):
		feed = feedparser.parse('http://www.kino.de/rss/charts/')
		for item in feed.entries:
			movieList.append(replaceUmlauts(item.title))
			
	#remove duplicates from movieList
	list(set(movieList))
	
	return movieList
def replaceUmlauts(title):
	title = title.replace(unichr(228),'ae')
	title = title.replace(unichr(252),'ue')
	title = title.replace(unichr(246),'oe')
	title = title.replace(unichr(196),'Ae')
	title = title.replace(unichr(220),'Ue')
	title = title.replace(unichr(214),'Oe')
	
	return title

def tmdbLookup(self,movieList):
	movieListTrans = []
	if self.getConfig('tmdbapikey') == "":
		self.core.log.error('No TMDB API Key given!')
	else:
		
		tmdb.configure(self.getConfig('tmdbapikey'),self.getConfig('tmdblang'))
		for title in movieList:
			title = title.strip()
			newtitle = re.sub("\(\d{4}\)$",'',title)
			if newtitle != '':
				title = newtitle
			
			self.core.log.debug('----------------------- try search ----> "' + title + '"')
			movies = tmdb.Movies(title)
			
			#handling more results maybe later
			for movie in movies.iter_results():
				self.core.log.debug(movie['title'])
				
				movieListTrans.append(movie)
				# maybe more later
				break
	return movieListTrans

def fetchTraktTvList(self,movieList):
	if self.getConfig("usetrakttv"):
		apikey = self.getConfig("traktvapikey")
		username = self.getConfig("traktvusername")
		pw = self.getConfig("traktvpwhash")
		listname = self.getConfig("traktvlist")
		url = "http://api.trakt.tv/user/list.json/" + apikey + "/" +username + "/" + listname
		request = urllib2.Request(url,json.dumps({"username" : username,"password" : pw}))
		request.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0')
		request.add_header('Accept','	text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
		request.add_header('Host',"api.trakt.tv") # important!!
		opener = urllib2.build_opener()
		result = opener.open(request).read()
		
		list = json.loads(result)
		for item in list["items"]:
			if item["type"] == "movie":
				movieList.append(item["movie"]["title"])
			
	return movieList
	
	
def openUrl(url,host):
	request = urllib2.Request(url)
	request.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0')
	request.add_header('Accept','	text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
	request.add_header('Host',host)
	opener = urllib2.build_opener()
	return opener.open(request).read()
##################################################
###################### HD-AREA	
def hdareaSearch(self,movieListTrans,packages):
	#search on hd-area
	for movie in movieListTrans:
		title = movie['title']
		otitle = title
		# prepare title
		title = title.lower()
		title = replaceUmlauts(title)
		title = title.replace(':','')
		title = title.replace('.','')
		title = title.replace('-','')
		title = title.replace('  ',' ')
			
		searchLink = 'http://www.hd-area.org/?s=search&q=' + urllib2.quote(title)
		self.core.log.debug('search with '+searchLink)
		page = urllib2.urlopen(searchLink).read()
		soup = BeautifulSoup(page)
		releases = []
		for content in soup.findAll("div",{"class":"whitecontent contentheight"}):
			searchLinks = content.findAll('a')
			
			# if no results - search again with shorter title? maybe cut one,two,three words for better results?
			# example Chroniken der Unterwelt - City of Bones -> no results
			#         Chroniken der Unterwelt has results!
			
			for link in searchLinks:
				href = link['href']
				releaseName = link.getText()
				
				if self.getConfig('quality') in releaseName:
					if checkReleaseName(self,releaseName,title):
						release = {}
						release['text'] = releaseName
						release['link'] = href
						release['title'] = otitle
						release['id'] = movie['id']
						releases.append(release)
			
		for release in releases:
			# parse search result
			self.core.log.debug("parse movie page " + release["link"])
			page = urllib2.urlopen(release['link']).read()
			soup = BeautifulSoup(page)
			acceptedLinks = []
			for download in soup.findAll("div",{"class":"download"}):
				for descr in download.findAll("div",{"class":"beschreibung"}):
					links = descr.findAll('span',{"style":"display:inline;"})
					for link in links:
						url = link.a["href"]
						hoster = link.text
						for prefhoster in self.getConfig('hoster').split(";"):
							if prefhoster.lower() in hoster.lower():
								# accepted release link
								acceptedLinks.append(url)
								# TODO: save alternative release link.
			# build package for release
			if len(acceptedLinks) > 0:
				release['acceptedLinks'] = acceptedLinks
				packages.append(release)

##################################################
###################### HD-WORLD
def hdworldSearch(self,movieListTrans,packages):
	#search on hd-area
	for movie in movieListTrans:
		title = movie['title']
		otitle = title
		# prepare title
		title = title.lower()
		title = replaceUmlauts(title)
		title = title.replace(':','')
		title = title.replace('.','')
		title = title.replace('-','')
		title = title.replace('  ',' ')
		
		searchLink = 'http://hd-world.org/index.php?s=' + urllib2.quote(title)
		self.core.log.debug('search with '+searchLink)
		page = openUrl(searchLink,"hd-world.org")
		
		soup = BeautifulSoup(page)
		releases = []
		for content in soup.findAll("div",{"class":"post"}):
			for heading in content.findAll("h1"):
				searchLinks = heading.findAll('a')
				
				# if no results - search again with shorter title? maybe cut one,two,three words for better results?
				# example Chroniken der Unterwelt - City of Bones -> no results
				#         Chroniken der Unterwelt has results!
				
				for link in searchLinks:
					href = link['href']
					releaseName = link.getText()
					
					if "anmeldung" not in href and self.getConfig('quality') in releaseName:
						if checkReleaseName(self,releaseName,title):
							release = {}
							release['text'] = releaseName
							release['link'] = href
							release['title'] = otitle
							release['id'] = movie['id']
							releases.append(release)
			
		for release in releases:
			# parse search result
			self.core.log.debug("parse movie page " + release["link"])
			#page = urllib2.urlopen(release['link']).read()
			page = openUrl(release['link'],"hd-world.org")
			soup = BeautifulSoup(page)
			acceptedLinks = []
			for download in soup.findAll("div",{"class":"entry"}):
				for link in download.findAll("a"):
					url = link["href"]
					hoster = link.text					
					try:
						psText = link.previousSibling.text.lower()
						if "download" in psText or "mirror" in psText:				
							for prefhoster in self.getConfig('hoster').split(";"):
								if prefhoster.lower() in hoster.lower():
									# accepted release link
									self.core.log.debug("Accepted # "+url)
									acceptedLinks.append(url)
									# TODO: save alternative release link.
					except Exception: 
						pass
			# build package for release
			if len(acceptedLinks) > 0:
				release['acceptedLinks'] = acceptedLinks
				packages.append(release)
		break

def checkReleaseName(self,releaseName,title):
	releaseName = releaseName.lower()
	reqtext = self.getConfig('reqtext').lower()
	nottext = self.getConfig('nottext').lower()
	
	# contains required text / not contains bad words
	if (reqtext == '' or reqtext in releaseName) and (nottext == '' or nottext not in releaseName):
		# does release name begins with first word of title; replace . with blanks in release name
		if releaseName.replace('.',' ').startswith(title.split(' ')[0]+" "):
			return True
	
	return False
		
def checkFetched(self,movieListTrans):
	s = open("topmoviefetches.txt").read()
	movieListTransReduced = movieListTrans[:]
	for movie in movieListTrans:
		if str(movie['id']) in s:
			self.core.log.info("TopMovieFetcher: "+movie['title']+" was already fetched. Skip search")
			movieListTransReduced.remove(movie)
	return movieListTransReduced
				
class TopMovieFetcher(Hook):
    __name__ = "TopMovieFetcher"
    __version__ = "0.5"
    __description__ = "Checks HD-AREA.org for new Movies. "
    __config__ = [	
					("activated", "bool", "Activated", "False"),
					("queue", "bool", "move Movies directly to Queue", "False"),
					
					("rssapple","bool","Use Apple's Top Movies RSS","True"),
					("rssrottentomato","bool","Use Rottentomatoes Top Movies RSS","True"),
					("rsskinode","bool","Use German Top Movies Charts from Kino.de RSS","True"),
					
					("usehdworld","bool","Search on hd-world.org","True"),
					("usehdarea","bool","Search on hd-area.org","True"),
					
					("interval", "int", "Check interval in minutes", "60"),
					("quality", "str", "Quality (720p or 1080p)", "720p"),
					("hoster", "str", "Preferred Hoster (seperated by ;)","uploaded"),
					("reqtext","str","Required text in release name","x264"),
					("nottext","str","Text not in release name",".3D"),
					
					("tmdbapikey","str","themoviedb.org API-Key",""),
					("tmdblang","str","Language (en or de)","de"),
					
					("usetrakttv","bool","Fetch from trakt.tv-list","False"),
					("traktvapikey","str","trakt.tv API-Key",""),
					("traktvusername","str","trakt.tv Username",""),
					("traktvpwhash","str","trakt.tv Password (SHA1-Hash!)",""),
					("traktvlist","str","trakt.tv List which should be fetched","")]
    __author_name__ = ("Studententyp")
    __author_mail__ = ("")
	
	

    def setup(self):
		self.interval = self.getConfig("interval") * 60 

    def periodical(self):
		self.core.log.info('Period of TopMovieFetcher started')
		
		# create file
		open("topmoviefetches.txt", "a").close()

		#get feeds
		movieList = parseFeeds(self)
		
		#use third party services
		movieList = fetchTraktTvList(self,movieList)
		
		#check movies in tmdb
		movieListTrans = tmdbLookup(self,movieList)
		
		packages = []
		
		# check for already fetched ones
		movieListTrans = checkFetched(self,movieListTrans)
		
		## search on hd-area.org
		if self.getConfig('usehdarea'):
			hdareaSearch(self,movieListTrans,packages)
		
		## search on hd-world.org
		if self.getConfig('usehdworld'):
			hdworldSearch(self,movieListTrans,packages)
		
		## final preparation
		finalMovieList = []
		finalPackages = []
		for r in packages:
			# 'remove' duplicates
			if not r['title'] in finalMovieList:
				finalMovieList.append(r['title'])
				
				finalPackages.append(r)
				
		for r in finalPackages:
			self.core.api.addPackage(r['text'].encode("utf-8"), r["acceptedLinks"][0].split('"'), 1 if self.getConfig("queue") else 0)
			f = open("topmoviefetches.txt", "a")
			f.write(str(r['id'])+";") 
			f.close()
		
		self.core.log.info('Period of TopMovieFetcher ended')
