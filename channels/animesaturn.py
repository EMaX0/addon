# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# Thanks to 4l3x87
# ----------------------------------------------------------

from core import support

# __channel__ = "animesaturn"
# host = support.config.get_setting("channel_host", __channel__)
host = support.config.get_channel_url()
headers={'X-Requested-With': 'XMLHttpRequest'}


list_servers = ['directo', 'fembed', 'animeworld']
list_quality = ['default', '480p', '720p', '1080p']

@support.menu
def mainlist(item):

    anime = ['/animelist?load_all=1',
             ('Più Votati',['/toplist','menu', 'top']),
             ('In Corso',['/animeincorso','peliculas','incorso']),
             ('Ultimi Episodi',['/fetch_pages.php?request=episodes','peliculas','updated'])]

    return locals()


@support.scrape
def search(item, texto):
    search = texto
    item.contentType = 'tvshow'
    anime = True
    patron = r'href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>[^<|(]+)(?:(?P<lang>\(([^\)]+)\)))?<|\)'
    action = 'check'
    def itemHook(item):
        item.url = item.url.replace('www.','')
        return item
    return locals()


def newest(categoria):
    support.log()
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host + '/fetch_pages.php?request=episodes'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def menu(item):
    patronMenu = r'u>(?P<title>[^<]+)<u>(?P<url>.*?)</div> </div>'
    action = 'peliculas'
    def itemHook(item):
        item.url = item.url.replace('www.','')
        return item
    return locals()


@support.scrape
def peliculas(item):
    anime = True
    deflang= 'Sub-ITA'
    if item.args == 'updated':
        post = "page=" + str(item.page if item.page else 1) if item.page > 1 else None
        page= support.match(item, patron=r'data-page="(\d+)" title="Next">', post=post, headers=headers).match
        patron = r'<img alt="[^"]+" src="(?P<thumb>[^"]+)" [^>]+></div></a>\s*<a href="(?P<url>[^"]+)"><div class="testo">(?P<title>[^\(<]+)(?:(?P<lang>\(([^\)]+)\)))?</div></a>\s*<a href="[^"]+"><div class="testo2">[^\d]+(?P<episode>\d+)</div></a>'
        if page: nextpage = page
        item.contentType='episode'
        action = 'findvideos'
    elif item.args == 'top':
        data = item.url
        patron = r'<a href="(?P<url>[^"]+)">[^>]+>(?P<title>[^<\(]+)(?:\((?P<year>[0-9]+)\))?(?:\((?P<lang>[A-Za-z]+)\))?</div></a><div class="numero">(?P<title2>[^<]+)</div>.*?src="(?P<thumb>[^"]+)"'
        action = 'check'
    else:
        pagination = ''
        if item.args == 'incorso': patron = r'"slider_title"\s*href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)"[^>]+>(?P<title>[^\(<]+)(?:\((?P<year>\d+)\))?</a>'
        else: patron = r'href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>.+?)(?:\((?P<lang>ITA)\))?(?:(?P<year>\((\d+)\)))?</span>'
        action = 'check'
    def itemHook(item):
        item.url = item.url.replace('www.','')
        return item
    return locals()


def check(item):
    movie = support.match(item, patron=r'Episodi:</b> (\d*) Movie')
    anime_id = support.match(movie.data, patron=r'anime_id=(\d+)').match
    item.url = host + "/loading_anime?anime_id=" + anime_id
    if movie.match:
        item.contentType = 'movie'
        episodes = episodios(item)
        if len(episodes) > 0: item.url = episodes[0].url
        return findvideos(item)
    else:
        item.contentType = 'tvshow'
        return episodios(item)


@support.scrape
def episodios(item):
    if item.contentType != 'movie': anime = True
    patron = r'<strong" style="[^"]+">(?P<title>[^<]+)</b></strong></td>\s*<td style="[^"]+"><a href="(?P<url>[^"]+)"'
    def itemHook(item):
        item.url = item.url.replace('www.','')
        return item
    return locals()


def findvideos(item):
    support.log()
    itemlist = []
    # support.dbg()
    urls = support.match(item, patron=r'<a href="([^"]+)"><div class="downloadestreaming">', headers=headers, debug=False).matches
    if urls:
        links = support.match(urls[0].replace('www.',''), patron=r'(?:<source type="[^"]+"\s*src=|file:\s*)"([^"]+)"', headers=headers, debug=False)
        for link in links.matches:
            itemlist.append(
                support.Item(channel=item.channel,
                            action="play",
                            title='Diretto',
                            quality='',
                            url=link,
                            server='directo',
                            fulltitle=item.fulltitle,
                            show=item.show,
                            contentType=item.contentType,
                            folder=False))
    return support.server(item, links, itemlist=itemlist)









