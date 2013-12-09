python-stuff
============

pyload-hook: TopMovieFetcher
----------------------------

see http://forum.pyload.org/viewtopic.php?f=9&t=3153

- fetches movies from rss feeds (see list below)
- multilingual support
- quality selection / bad word filter (eg 3D)
- saves already fetched movies (in a txt file)

Supported Feeds
- Top Movies from apple http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/topMovies/xml
- Top Movies from rottentomatoes http://www.rottentomatoes.com/syndication/rss/top_movies.xml
- Top Movies from kino.de http://www.kino.de/rss/charts/

Supported Third-Party Apps
- trakt.tv private lists

Planned:
- add more search-sites (eg hd-world)
- save alternative links if a package is partly offline
- better search variations and verification 
- include more/custom rss feeds
- hoster prio
- saving already fetched files in sqlite db
- much more
- looking forward to feature requests

Requires (add to your /usr/share/pyload/module/lib folder)
- https://github.com/doganaydin/themoviedb/blob/master/tmdb.py
- http://www.python-requests.org/en/latest/user/install/#install


Credits:
Gutz-Pilz


