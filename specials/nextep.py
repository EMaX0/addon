# -*- coding: utf-8 -*-
import xbmc, xbmcgui, os
from platformcode import config, platformtools, logger
from time import time, sleep
from core import scrapertools
from core import jsontools, filetools
from lib.concurrent import futures

PLAYER_STOP = 13
ND = 'NextDialogCompact.xml' if config.get_setting('next_ep_type') else 'NextDialog.xml'

def check(item):
    return True if config.get_setting('next_ep') > 0 and item.contentType != 'movie' else False


def return_item(item):
    logger.info()
    with futures.ThreadPoolExecutor() as executor:
        future = executor.submit(next_ep, item)
        item = future.result()
    return item

def run(item):
    logger.info()
    with futures.ThreadPoolExecutor() as executor:
        future = executor.submit(next_ep, item)
        item = future.result()
    if item.next_ep:
        from platformcode.launcher import play_from_library
        return play_from_library(item)


def videolibrary(item):
    from threading import Thread
    item.videolibrary = True
    Thread(target=next_ep, args=[item]).start()


def next_ep(item):
    logger.info()
    condition = config.get_setting('next_ep')
    item.next_ep = False
    item.show_server = True

    VL = True if item.videolibrary else False

    time_over = False
    time_limit = time() + 30
    time_steps = [20,30,40,50,60]
    TimeFromEnd = time_steps[config.get_setting('next_ep_seconds')]

    # wait until the video plays
    while not platformtools.is_playing() and time() < time_limit:
        sleep(1)

    while platformtools.is_playing() and time_over == False:
        try:
            Total = xbmc.Player().getTotalTime()
            Actual = xbmc.Player().getTime()
            Difference = Total - Actual
            if Total > TimeFromEnd >= Difference:
                time_over = True
        except:
            break

    if time_over:
        if condition == 1: # hide server afther x second
            item.show_server = False
        elif condition == 2: # play next fileif exist

            # check i next file exist
            current_filename = os.path.basename(item.strm_path)
            base_path = os.path.basename(os.path.normpath(os.path.dirname(item.strm_path)))
            path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"),base_path)
            fileList = []
            for file in os.listdir(path):
                if file.endswith('.strm'):
                    fileList.append(file)

            fileList.sort()

            nextIndex = fileList.index(current_filename) + 1
            if nextIndex == 0 or nextIndex == len(fileList):
                next_file = None
            else:
                next_file = fileList[nextIndex]

            # start next episode window afther x time
            if next_file:
                from core.item import Item
                season_ep = next_file.split('.')[0]
                season = season_ep.split('x')[0]
                episode = season_ep.split('x')[1]
                next_ep = '%sx%s' % (season, episode)
                item = Item(
                    action= 'play_from_library',
                    channel= 'videolibrary',
                    contentEpisodeNumber= episode,
                    contentSeason= season,
                    contentTitle= next_ep,
                    contentType= 'tvshow',
                    infoLabels= {'episode': episode, 'mediatype': 'tvshow', 'season': season, 'title': next_ep},
                    strm_path= filetools.join(base_path, next_file))

                global ITEM
                ITEM = item

                nextDialog = NextDialog(ND, config.get_runtime_path())
                nextDialog.show()
                while platformtools.is_playing() and not nextDialog.is_still_watching():
                    xbmc.sleep(100)
                    pass

                nextDialog.close()
                logger.info('Next Episode: ' +str(nextDialog.stillwatching))

                if nextDialog.stillwatching or nextDialog.continuewatching:
                    item.next_ep = True
                    xbmc.Player().stop()
                    if VL:
                        sleep(1)
                        xbmc.executebuiltin('Action(Back)')
                        sleep(0.5)
                        from platformcode.launcher import play_from_library
                        return play_from_library(item)
                else:
                    item.show_server = False
                    if VL:
                        sleep(1)
                        xbmc.executebuiltin('Action(Back)')
                        sleep(0.5)
                        return None

    return item


class NextDialog(xbmcgui.WindowXMLDialog):
    item = None
    cancel = False
    stillwatching = False
    continuewatching = True

    def __init__(self, *args, **kwargs):
        logger.info()
        self.action_exitkeys_id = [10, 13]
        self.progress_control = None
        self.item = ITEM

    def set_still_watching(self, stillwatching):
        self.stillwatching = stillwatching

    def set_continue_watching(self, continuewatching):
        self.continuewatching = continuewatching

    def is_still_watching(self):
        return self.stillwatching

    def onFocus(self, controlId):
        pass

    def doAction(self):
        pass

    def closeDialog(self):
        self.close()

    def onClick(self, controlId):
        if controlId == 3012:  # Still watching
            self.set_still_watching(True)
            self.set_continue_watching(False)
            self.close()
        elif controlId == 3013:  # Cancel
            self.set_continue_watching(False)
            self.close()

    def onAction(self, action):
        logger.info()
        if action == PLAYER_STOP:
            self.set_continue_watching(False)
            self.close()
