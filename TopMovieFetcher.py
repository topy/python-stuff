# -*- coding: utf-8 -*-
from module.plugins.Hook import Hook
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import tmdb
import feedparser

class TopMovieFetcher(Hook):
    __name__ = "TopMovieFetcher"
    __version__ = "0.3"
    __description__ = "Checks HD-AREA.org for new Movies. "
    __config__ = [	
					("activated", "bool", "Activated", "False"),
					("queue", "bool", "move Movies directly to Queue", "False"),
					("rssapple","bool","Use Apple's Top Movies RSS","True"),
					("rssrottentomato","bool","Use Rottentomatoes Top Movies RSS","True"),
					("usehdarea","bool","Search on hd-area.org","True"),
					("interval", "int", "Check interval in minutes", "60"),
					("rating","float","min. IMDB rating","6.1"),
					("quality", "str", "Quality (720p or 1080p)", "720p"),
					("hoster", "str", "Preferred Hoster (seperated by ;)","uploaded"),
					("reqtext","str","Required text in release name","x264"),
					("nottext","str","Text not in release name","3D"),
					("tmdbapikey","str","themoviedb.org API-Key",""),
					("tmdblang","str","Language (en or de)","de")]
    __author_name__ = ("Studententyp")
    __author_mail__ = ("")

    def setup(self):
        self.interval = self.getConfig("interval") * 60 
    def periodical(self):
		f = open("topmoviefetches.txt", "a")
		f.close()
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
		packages = []
		
		s = open("topmoviefetches.txt").read()  
		for title in movieListTrans:
			if title in s:
				self.core.log.info("TopMovieFetcher: "+title+" was already fetched. Skip search")
				movieListTrans.remove(title)
		
		#search on hd-area
		if self.getConfig('usehdarea'):
			for title in movieListTrans:
				otitle = title
				# prepare title
				title = title.lower()
				title = title.replace(unichr(228),'ae')
				title = title.replace(unichr(252),'ue')
				title = title.replace(unichr(246),'oe')
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
							if self.getConfig('reqtext') == '' or self.getConfig('reqtext').lower() in releaseName.lower() and (self.getConfig('nottext')=='' or self.getConfig('nottext').lower() not in releaseName.lower()):
								# does release name begins with first word of title; replace . with blanks in release name
								if releaseName.replace('.',' ').lower().startswith(title.split(' ')[0]+" "):
									release = {}
									release['text'] = releaseName
									release['link'] = href
									release['title'] = otitle
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
			f.write(r['title']+"\n") 
			f.close()
