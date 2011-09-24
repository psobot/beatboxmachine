"""
    The Wub Machine
    Python web interface
    August 5-25, 2011 by Peter Sobot (petersobot.com)
"""

__author__ = "Peter Sobot"
__copyright__ = "Copyright (C) 2011 Peter Sobot"
__version__ = "2.1"

import json, time, locale, traceback, gc, logging, os, database, urllib
import tornado.ioloop, tornado.web, tornado.template, tornado.httpclient, tornado.escape, tornado.websocket
import tornadio, tornadio.server
import config
from datetime import datetime, timedelta
from hashlib import md5

# Wubmachine-specific libraries
from remixers.beatbox import Beatbox
from helpers.remixqueue import RemixQueue
from helpers.soundcloud import SoundCloud
from helpers.cleanup import Cleanup
from helpers.daemon import Daemon
from helpers.web import *
         
# Instead of using xheaders, which doesn't work under Tornadio, we do this:
if config.nginx:
    class RequestHandler(tornado.web.RequestHandler):
        """
            Patched Tornado RequestHandler to take care of Nginx ip proxying
        """
        def __init__(self, application, request, **kwargs):
            if 'X-Real-Ip' in request.headers:
                request.remote_ip = request.headers['X-Real-Ip']
            tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
else:
    RequestHandler = tornado.web.RequestHandler

# Handlers

class MainHandler(RequestHandler):
    def get(self):
        js = ("window.wubconfig = %s;" % json.dumps(config.javascript)) + '\n'.join(javascripts)
        kwargs = {
            "isOpen": r.isAccepting(),
            "track": sc.frontPageTrack(),
            "isErroring": r.errorRateExceeded(),
            'count': locale.format("%d", trackCount, grouping=True),
            'cleanup_timeout': time_in_words(config.cleanup_timeout),
            'javascript': js,
            'connectform': connectform
        }
        self.write(templates.load('index.html').generate(**kwargs)) 
    def head(self):
        self.finish()

class ProgressSocket(tornadio.SocketConnection):
    listeners = {}

    @classmethod
    def update(self, uid, data):
        try:  
            self.listeners[uid].send(data)
        except:
            pass

    def on_open(self, *args, **kwargs):
        try:
            self.uid = kwargs['extra']
            if self.uid in self.listeners:
                raise Exception("Progress socket already open!")
            if self.uid in r.finished:
                raise Exception("Remix complete, socket should be closed!")
            self.listeners[self.uid] = self
            if r.isAvailable():
                r.start(self.uid)
            log.info("Opened progress socket for %s" % self.uid)
        except:
            raise
            log.warning("Failed to open progress socket for %s because: %s" % (self.uid, traceback.format_exc()) )

    def on_close(self):
        try:
            del self.listeners[self.uid]
            r.stop(self.uid)
            log.info("Closed progress socket for %s" % self.uid)
        except:
            log.warning("Failed to close progress socket for %s" % self.uid)

    def on_message(self, message):
        pass

class MonitorSocket(tornadio.SocketConnection):
    monitors = set()

    @classmethod
    def update(self, uid):
        data = MonitorHandler.track(uid)
        for m in self.monitors:
            m.send(data)

    def on_open(self, *args, **kwargs):
        log.info("Opened monitor socket.")
        self.monitors.add(self)

    def on_close(self):
        log.info("Closed monitor socket.")
        self.monitors.remove(self)

    def on_message(self, message):
        pass

class MonitorHandler(RequestHandler):
    keys = ['upload', 'download', 'remixTrue', 'remixFalse', 'shareTrue', 'shareFalse']

    @tornado.web.asynchronous
    def get(self, sub=None, uid=None):
        if sub:
            sections = {
                'graph': self.graph,
                'overview': self.overview,
                'latest': self.latest,
                'remixqueue': self.remixqueue,
            }
            if sub in sections:
                self.write(sections[sub]())
                self.finish()
            else:
                raise tornado.web.HTTPError(404)
        else:
            kwargs = {
                'overview': self.overview(),
                'latest': self.latest(),
                'config': "window.wubconfig = %s;" % json.dumps(config.javascript)
            }
            self.write(templates.load('monitor.html').generate(**kwargs))
            self.finish()

    def clearqueue(self):
        del self.watchqueue[:]

    def histogram(self, interval=None):
        if interval:
            limit = datetime.now() - timedelta(**{ interval: 1 })
            d = db.query(db.Event).add_columns('count(*)', db.Event.action, db.Event.success).group_by('action', 'success').filter(db.Event.start > limit).all()
        else:
            d = db.query(db.Event).add_columns('count(*)', db.Event.action, db.Event.success).group_by('action', 'success').all()
        n = {}
        for k in self.keys:
            n[k] = 0
        for a in d:
            if a.action == 'upload' or a.action == 'download':
                n[a.action] = int(a.__dict__['count(*)'])
            elif a.action == 'remix' or a.action == 'share':
                n["%s%s" % (a.action, a.success)] = int(a.__dict__['count(*)'])
        return n

    def remixqueue(self):
        self.set_header("Content-Type", 'text/plain')
        return str("Remixers: %s\nFinished: %s\nQueue:    %s\nRunning:  %s" % (r.remixers, r.finished, r.queue, r.running))

    def overview(self):
        kwargs = {
            'ct': str(datetime.now()),
            'inqueue': len(r.queue),
            'processing': len(r.remixers),
            'maximum': r.maximum,
            'maximumexceeded': len(r.remixers) > r.maximum,
            'hourly': r.hourly,
            'hourlyexceeded': r.countInHour() > r.hourly,
            'errorInterval': 2,
            'errorRate': r.errorRate(),
            'errorRateExceeded': r.errorRateExceeded(),
            'isOpen': r.isAvailable(),
            'hour': self.histogram('hours'),
            'day': self.histogram('days'),
            'ever': self.histogram(),
        }
        return templates.load('overview.html').generate(**kwargs)

    def current(self):
        running = [v for k, v in r.remixers.iteritems() if k in r.running]
        return templates.load('current.html').generate(c=running)

    def shared(self):
        d = db.query(db.Event).filter_by(action = "sharing", success = True).group_by(db.Event.uid).order_by(db.Event.id.desc()).limit(6)
        return templates.load('shared.html').generate(tracks=d.all())

    @classmethod
    def track(self, track):
        db = database.getdb()
        if not isinstance(track, db.Track):
            if not track:
                raise tornado.web.HTTPError(400)
            if isinstance(track, dict) and 'uid' in track:
                track = track['uid']
            elif not isinstance(track, str) and not len(track) == 32:
                return '' # This object isn't a track
            tracks =  db.query(db.Track).filter(db.Track.uid == track).all()
            if not tracks:
                raise tornado.web.HTTPError(404)
            else:
                track = tracks[0]

        for stat in ['upload', 'remix', 'share', 'download']:
            track.__setattr__(stat, None)
        
        events = {}
        for event in track.events:
            events[event.action] = event
        track.upload = events.get('upload')
        track.remix = events.get('remix')
        track.share = events.get('share')
        track.download = events.get('download')
        track.running = track.uid in r.running or (track.share and track.share.start and not track.share.end and track.share.success is None)
        track.failed = (track.remix and track.remix.success == False) or (track.share and track.share.success == False)
        if track.failed:
            track.failure = track.remix.detail if track.remix.success is False else track.share.detail
        try:
            track.progress = r.remixers[track.uid].last['progress']
            track.text = r.remixers[track.uid].last['text']
        except:
            track.progress = None
            track.text = None

        kwargs = {
            'track': track,
            'exists': os.path.exists,
            'time_ago_in_words': time_ago_in_words,
            'seconds_to_time': seconds_to_time,
            'convert_bytes': convert_bytes
        }
        return templates.load('track.html').generate(**kwargs)

    def latest(self):
        tracks = db.query(db.Track).order_by(db.Track.id.desc()).limit(config.monitor_limit).all()
        return ''.join([self.track(track) for track in tracks])

    def graph(self):
        history = {}
        for i in xrange(0, 24*2): # last 3 days
            low = datetime.now() - timedelta(hours = i)
            high = low + timedelta(hours = 1)
            timestamp = 1000 * time.mktime(high.timetuple())
            dayr = db.query(db.Event).add_columns('count(*)', db.Event.action, db.Event.success).group_by('action', 'success').filter(db.Event.start.between(low, high)).all()
            n = {}
            for daya in dayr:
                if daya.action == 'download':
                    n[daya.action] = [timestamp , int(daya.__dict__['count(*)'])]
                elif daya.action == 'remix' or daya.action == 'share':
                    n["%s%s" % (daya.action, daya.success)] = [timestamp, int(daya.__dict__['count(*)'])]

            for k in self.keys:
                if not k in history:
                    history[k] = []
                if k in n:
                    history[k].append(n[k])
                else:
                    history[k].append([timestamp, int(0)])
        return history 

class ShareHandler(RequestHandler):
    @tornado.web.asynchronous
    def get(self, uid):
        self.uid = uid
        try:
            token = str(self.get_argument('token'))
            timeout = config.soundcloud_timeout

            if not uid in r.finished:
                raise tornado.web.HTTPError(404)

            t = r.finished[uid]['tag']

            description = config.soundcloud_description
            if 'artist' in t and 'album' in t:
                description = ("Original song by %s, from the album \"%s\".<br />" % (t['artist'], t['album'])) + description
            elif 'artist' in t:
                description = ("Original song by %s.<br />" % t['artist']) + description

            form = MultiPartForm()
            form.add_field('oauth_token', token)
            form.add_field('track[title]', t['new_title'].encode('utf-8'))
            form.add_field('track[genre]', "Beat")
            form.add_field('track[license]', "no-rights-reserved")
            form.add_field('track[tag_list]', ' '.join(['"%s"' % tag for tag in config.soundcloud_tag_list]))
            form.add_field('track[bpm]', '140')
            form.add_field('track[description]', description.encode('utf-8'))
            form.add_field('track[track_type]', 'remix')
            form.add_field('track[downloadable]', 'true')
            form.add_field('track[sharing_note]', config.soundcloud_sharing_note)
            form.add_file('track[asset_data]', '%s.mp3' % uid, open(t['remixed']))
            if 'art' in t:
                form.add_file('track[artwork_data]', '%s.png' % uid, open(t['art']))
            if 'key' in t:
                form.add_field('track[key_signature]', t['key'])

            self.event = db.Event(uid, "share", ip = self.request.remote_ip)
            db.add(self.event)
            db.flush()
            MonitorSocket.update(self.uid)

            self.ht = tornado.httpclient.AsyncHTTPClient()
            self.ht.fetch(
                "https://api.soundcloud.com/tracks.json",
                self._get,
                method = 'POST',
                headers = {"Content-Type": form.get_content_type()},
                body = str(form),
                request_timeout = timeout,
                connect_timeout = timeout
            )
        except:
            self.write({ 'error': traceback.format_exc().splitlines()[-1] })
            self.event.success = False
            self.event.end = datetime.now()
            self.event.detail = traceback.format_exc().splitlines()[-1]
            db.flush()
            self.finish()
            MonitorSocket.update(self.uid)
    
    def _get(self, response):
        self.write(response.body)
        self.finish()
        r = json.loads(response.body)
        self.event.success = True
        self.event.end = datetime.now()
        self.event.detail = r['permalink_url'].encode('ascii', 'ignore')
        db.flush()
        MonitorSocket.update(self.uid)
        sc.fetchTracks()

class DownloadHandler(RequestHandler):
    def get(self, uid):
        if not uid in r.finished or not os.path.isfile('static/songs/%s.mp3' % uid):
            tornado.web.HTTPError(404)
        else:
            filename = "%s.mp3" % (r.finished[uid]['tag']['new_title'] if 'new_title' in r.finished[uid]['tag'] else uid)
            self.set_header('Content-disposition', 'attachment; filename="%s"' % filename)
            self.set_header('Content-type', 'audio/mpeg')
            self.set_header('Content-Length', os.stat('static/songs/%s.mp3' % uid)[6])
            self.write(open('static/songs/%s.mp3' % uid).read())
            self.finish()
            db.add(db.Event(uid, "download", success = True, ip = self.request.remote_ip))
            db.flush()
            MonitorSocket.update(uid)

class UploadHandler(RequestHandler):
    def trackDone(self, final):
        global trackCount
        trackCount += 1

    def post(self):
        self.uid = config.uid()
        self.track = db.Track(self.uid)
        self.event = db.Event(self.uid, "upload", None, self.request.remote_ip, urllib.unquote_plus(self.get_argument('qqfile').encode('ascii', 'ignore')))
        db.add(self.track)
        db.add(self.event)

        try:
            extension = os.path.splitext(self.get_argument('qqfile'))[1]
        except:
            extension = '.mp3'
        self.track.extension = extension
        targetPath = os.path.join('uploads/', '%s%s' % (self.uid, extension))

        if extension not in config.allowed_file_extensions:
            self.write({ 'error': "Sorry, but %s only works with %s." % (config.app_name, list_in_words([e[1:] for e in config.allowed_file_extensions])) })
            return

        try:
            f = open(targetPath, 'w')
            data = self.request.body if not self.request.files else self.request.files['upload'][0]['body'] 
            f.write(data)
            f.close()

            self.track.hash = md5(data).hexdigest()
            self.track.size = len(data)
            del data

            if not self.request.files:
                del self.request.body
            else:
                del self.request.files['upload'][0]['body']

            r.add(self.uid, extension, Beatbox, ProgressSocket.update, self.trackDone)
            self.event.success = True
            response = r.waitingResponse(self.uid)
            response['success'] = True
            self.write(response)
        except Exception as e:
            log.error("Error when trying to handle upload: %s" % traceback.format_exc())
            self.write({ "error" : "Could not save file." })
            self.event.success = False
        self.event.end = datetime.now()
        db.flush()
        gc.collect()

application = tornado.web.Application([
    (r"/(favicon.ico)", tornado.web.StaticFileHandler, {"path": "static/img/"}),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static/"}),
    (r"/monitor[/]?([^/]+)?[/]?(.*)", MonitorHandler), #Fix this
    (r"/upload", UploadHandler),
    (r"/share/(%s)" % config.uid_re, ShareHandler),
    (r"/download/(%s)" % config.uid_re, DownloadHandler),
    (r"/", MainHandler),
    tornadio.get_router(
        MonitorSocket,
        resource = config.monitor_resource
    ).route(),
    tornadio.get_router(
        ProgressSocket,
        resource = config.progress_resource,
        extra_re = config.uid_re,
        extra_sep = config.socket_extra_sep
    ).route()],
    socket_io_port = config.socket_io_port,
    enabled_protocols = ['websocket', 'xhr-multipart', 'xhr-polling', 'jsonp-polling'],
    )


if __name__ == "__main__":
    Daemon()

    log = logging.getLogger()
    log.name = config.log_name
    handler = logging.FileHandler(config.log_file)
    handler.setFormatter(logging.Formatter(config.log_format)) 
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)

    try:
        log.info("Starting %s..." % config.app_name)
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        except:
            locale.setlocale(locale.LC_ALL, 'en_US')
        
        log.info("\tConnecting to MySQL...")
        db = database.getdb()
        if not db:
            log.critical("Can't connect to DB!")
            exit(1)

        log.info("\tGrabbing track count from DB...")
        trackCount = db.query(db.Event).filter_by(action='remix', success = True).count()

        log.info("\tClearing temp directories...")
        cleanup = Cleanup(log, db, None)
        cleanup.all()

        log.info("\tStarting RemixQueue...")
        r = RemixQueue(db, MonitorSocket)
        cleanup.remixQueue = r

        log.info("\tInstantiating SoundCloud object...")
        sc = SoundCloud(log)

        log.info("\tLoading templates...")
        templates = tornado.template.Loader("templates/")
        templates.autoescape = None

        log.info("\tStarting cleanup timer...")
        cleanupTimer = tornado.ioloop.PeriodicCallback(cleanup.active, 1000*config.cleanup_timeout)
        cleanupTimer.start()

        log.info("\tCaching javascripts...")
        javascripts = [
            open('./static/js/jquery.fileupload.js').read(),
            open('./static/js/front.js').read(),
            open('./static/js/player.js').read(),
        ]
        connectform = open('./static/js/connectform.js').read()

        log.info("\tStarting Tornado...")
        application.listen(config.port)
        log.info("...started!")
        tornadio.server.SocketServer(application, xheaders=config.nginx)
    except:
        raise
    finally:
        log.critical("Error: %s" % traceback.format_exc())
        log.critical("IOLoop instance stopped. About to shutdown...")
        try:
            cleanup.all()
        except:
            pass
        log.critical("Shutting down!")
        if os.path.exists('wubmachine.pid'):
            os.remove('wubmachine.pid')
        exit(0)

