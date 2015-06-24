# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import xbmc
from Utils import *
from TheMovieDB import *
from YouTube import *
from ImageTools import *
from BaseClasses import DialogBaseInfo
from WindowManager import wm


class DialogEpisodeInfo(DialogBaseInfo):

    @busy_dialog
    def __init__(self, *args, **kwargs):
        super(DialogEpisodeInfo, self).__init__(*args, **kwargs)
        self.tmdb_id = kwargs.get('show_id')
        self.season = kwargs.get('season')
        self.show_name = kwargs.get('tvshow')
        self.episode_number = kwargs.get('episode')
        data = extended_episode_info(tvshow_id=self.tmdb_id,
                                     season=self.season,
                                     episode=self.episode_number)
        if data:
            self.info, self.data = data
        else:
            notify(ADDON.getLocalizedString(32143))
            return None
        search_str = "%s tv" % (self.info['title'])
        youtube_thread = GetYoutubeVidsThread(search_str, "", "relevance", 15)
        youtube_thread.start()  # TODO: rem threading here
        filter_thread = FilterImageThread(self.info["thumb"], 25)
        filter_thread.start()
        youtube_thread.join()
        filter_thread.join()
        self.info['ImageFilter'] = filter_thread.image
        self.info['ImageColor'] = filter_thread.imagecolor
        self.listitems = [(1000, create_listitems(self.data["actors"] + self.data["guest_stars"], 0)),
                          (750, create_listitems(self.data["crew"], 0)),
                          (1150, create_listitems(self.data["videos"], 0)),
                          (1350, create_listitems(self.data["images"], 0)),
                          (350, create_listitems(youtube_thread.listitems, 0))]

    def onInit(self):
        super(DialogEpisodeInfo, self).onInit()
        HOME.setProperty("movie.ImageColor", self.info["ImageColor"])
        self.window.setProperty("type", "Episode")
        pass_dict_to_skin(self.info, "movie.", False, False, self.window_id)
        self.fill_lists()

    def onClick(self, control_id):
        HOME.setProperty("WindowColor", xbmc.getInfoLabel("Window(home).Property(movie.ImageColor)"))
        if control_id in [1000, 750]:
            actor_id = self.getControl(control_id).getSelectedItem().getProperty("id")
            wm.open_actor_info(prev_window=self,
                               actor_id=actor_id)
        elif control_id in [350, 1150]:
            listitem = self.getControl(control_id).getSelectedItem()
            PLAYER.play_youtube_video(youtube_id=listitem.getProperty("youtube_id"),
                                      listitem=listitem,
                                      window=self)
        elif control_id in [1250, 1350]:
            wm.open_slideshow(image=self.getControl(control_id).getSelectedItem().getProperty("original"))
        elif control_id == 132:
            wm.open_textviewer(header=xbmc.getLocalizedString(32037),
                               text=self.info["Plot"],
                               color=self.info['ImageColor'])
        elif control_id == 6001:
            rating = get_rating_from_user()
            if not rating:
                return None
            identifier = [self.tmdb_id, self.season, self.info["episode"]]
            send_rating_for_media_item(media_type="episode",
                                       media_id=identifier,
                                       rating=rating)
            self.update_states()
        elif control_id == 6006:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            listitems = get_rated_media_items("tv/episodes")
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            wm.open_video_list(prev_window=self,
                               listitems=listitems)

    def update_states(self, forceupdate=True):
        if forceupdate:
            xbmc.sleep(2000)  # delay because MovieDB takes some time to update
            self.update = extended_episode_info(tvshow_id=self.tmdb_id,
                                                season=self.season,
                                                episode=self.episode_number,
                                                cache_time=0)
            self.data["account_states"] = self.update["account_states"]
        if self.data["account_states"]:
            # if self.data["account_states"]["favorite"]:
            #     self.window.setProperty("FavButton_Label", "UnStar episode")
            #     self.window.setProperty("movie.favorite", "True")
            # else:
            #     self.window.setProperty("FavButton_Label", "Star episode")
            #     self.window.setProperty("movie.favorite", "")
            if self.data["account_states"]["rated"]:
                self.window.setProperty("movie.rated", str(self.data["account_states"]["rated"]["value"]))
            else:
                self.window.setProperty("movie.rated", "")
            # self.window.setProperty("movie.watchlist", str(self.data["account_states"]["watchlist"]))
            # notify(str(self.data["account_states"]["rated"]["value"]))
