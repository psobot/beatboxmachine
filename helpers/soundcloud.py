import config, tornado.httpclient, json, time
from random import choice

class SoundCloud():
    tracks =            []
    trackage =          None
    log = None

    def __init__(self, log):
        self.log = log
        self.ht = tornado.httpclient.AsyncHTTPClient()
        self.fetchTracks()
    
    def fetchTracks(self):
        self.log.info("\tFetching SoundCloud tracks...")
        self.ht.fetch('https://api.soundcloud.com/tracks.json?client_id=%s&tags=beatboxmachine&order=created_at&limit=30&license=no-rights-reserved&filter=downloadable' % config.soundcloud_consumer, self._fetchTracks)

    def _fetchTracks(self, response):
        if not response.error:
            tracks = json.loads(response.body)
            self.tracks = [e for e in tracks if self.valid(e)]
            self.trackage = time.gmtime()
            self.log.info("SoundCloud tracks received!")
        else:
            self.log.error("SoundCloud fetch resulted in error: %s" % response.error)

    def frontPageTrack(self):
        if self.tracks:
            return choice(self.tracks)
        else:
            return None

    def valid(self, track):
        return (track['created_with']['id'] == config.soundcloud_app_id) and (track['title'] != "[untitled] (Beatbox Machine Remix)") and (len(track['title']) > 20) and (len(track['title']) < 60)

