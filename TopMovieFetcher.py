# -*- coding: utf-8 -*-
from module.plugins.Hook import Hook
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import tmdb
import feedparser

class TopMovieFetcher(Hook):
    __name__ = "TopMovieFetcher"
    __version__ = "0.1"
    __description__ = "Checks HD-AREA.org for new Movies. "
    __config__ = [	("activated", "bool", "Activated", "False"),
					("interval", "int", "Check interval in minutes", "60"),
					("queue", "bool", "move Movies directly to Queue", "False"),
					("quality", "str", "720p or 1080p", "720p"),
					("rating","float","min. IMDB rating","6.1"),
					("rssapple","bool","Use Apple's Top Movies RSS","True"),
					("rssrottentomato","bool","Use Rottentomatoes Top Movies RSS","True"),
					("usehdarea","bool","Search on hd-area.org","True"),
					("usehdworld","bool","Search on hd-world.org","True"),
					("tmdbapikey","str","themoviedb.org API-Key",""),
					("tmdblang","str","Language en or de","de")]
    __author_name__ = ("Studententyp")
    __author_mail__ = ("")

    def setup(self):
        self.interval = self.getConfig("interval") * 60 
    def periodical(self):
		self.core.log.debug('Period of TopMovieFetcher')
		movieList = []
		movieListTrans = []
		
		#get feeds
		
		#apple feed
		if self.getConfig('rssapple'):
			feed = feedparser.parse('http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/topMovies/xml')
			for item in feed.entries:
				movieList.append(item.title[0:item.title.find('-')])
		#rottentomatoes feed
		if self.getConfig('rssrottentomato'):
			feed = feedparser.parse('http://www.rottentomatoes.com/syndication/rss/top_movies.xml')
			for item in feed.entries:
				movieList.append(item.title[4:])
		
		self.core.log.debug('check for movies')
		#check movies in tmdb
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
					movieListTrans.append(movie['title'])
					# maybe more later
					break
					
		movieList = [] 
		
		#search on hd-area
		if self.getConfig('usehdarea'):
			for title in movieListTrans:
				# prepare title
				title = title.lower()
				title = title.replace('ä','ae')
				title = title.replace('ü','ue')
				title = title.replace('ö','oe')
				
				searchLink = 'http://www.hd-area.org/?s=search&q='+title
				page = urllib2.urlopen(searchLink).read()
				soup = BeautifulSoup(page)
				for searchDiv in soup.findAll("div", {"class" : "whitecontent"}):
					for mLink in searchDiv.findAll("a"):
						if self.getConfig('quality') in mLink.get('text'):
							self.core.log.debug(mLink.get('text')+ ' is ja nice result')
					
