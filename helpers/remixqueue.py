import config, os, time, database
from helpers.web import ordinal
from datetime import datetime, timedelta

class RemixQueue():
    maximum  = config.maximum_concurrent_remixes
    hourly   = config.hourly_remix_limit
    db = None

    def __init__(self, db, monitor):
        self.db = db
        self.monitor_callback = monitor.update

        self.remixers = {}
        self.finished = {}
        self.cleanups = {}
        self.events = {}

        self.watching = {}

        self.queue    = []
        self.running  = []

    def add(self, uid, ext, remixer, _user_callback, done_callback):
        if uid in self.remixers:
            raise Exception("Song already receieved!")

        infile = os.path.join("uploads/", "%s%s" % (uid, ext))
        outfile = os.path.join("static/songs/", "%s.mp3" % uid)

        user_callback = lambda data: _user_callback(uid, data)
        self.remixers[uid] = remixer(self, str(infile), str(outfile), [self.monitor_callback, user_callback])
        self.watching[uid] = user_callback
        self.cleanups[uid] = done_callback
        self.queue.append(uid)

    def updateTrack(self, uid, tag):
        # This may be called from another thread: let's use a unique DB connection.
        db = database.getdb()
        track = db.query(db.Track).filter_by(uid = uid).first()
        keep = ['length', 'samplerate', 'channels', 'bitrate', 'title', 'artist', 'album', 'art', 'thumbnail']
        for a in tag:
            if a in keep:
                try:
                    track.__setattr__(a, tag[a])
                except:
                    pass
        db.flush()
        db.close()
        del db

    def finish(self, uid, final=None):
        del self.remixers[uid]
        self.running.remove(uid)
        self.finished[uid] = final
        if self.cleanups[uid]:
            self.cleanups[uid](final)
            del self.cleanups[uid]
        
        # DB stuff
        self.events[uid].end = datetime.now()
        if final['status'] is -1:
            self.events[uid].success = False
            self.events[uid].detail = final.get('debug')
        else:
            self.events[uid].success = True
        self.db.flush()
        del self.events[uid]
        self.notifyWatchers()
        self.monitor_callback(uid)
        self.next()

    def start(self, uid):
        if not uid in self.queue:
            raise Exception("Cannot start, remixer not waiting: %s" % uid)
        self.running.append(uid)
        self.queue.remove(uid)
        del self.watching[uid]
        self.remixers[uid].start()
        self.events[uid] = self.db.Event(uid, "remix")
        self.db.add(self.events[uid])
        self.monitor_callback(uid)
        self.db.flush()

    def stop(self, uid):
        if uid in self.running:
            self.remixers[uid].stop()

    def notifyWatchers(self):
        for uid, callback in self.watching.iteritems():
            callback(self.waitingResponse(uid))

    def waitingResponse(self, uid):
        if uid in self.queue:
            position = self.queue.index(uid)
            if position is 0 and not len(self.running):
                text = "Starting..."
            elif position is 0:
                text = "Waiting... (next in line)"
            else:
                text = "Waiting in line... (%s)" % ordinal(position)
        else:
            text = "Starting..."
        return { 'status': 0, 'text': text, 'progress': 0, 'uid': uid, 'time': time.time() }

    def next(self):
        if len(self.queue):
            self.start(self.queue[0])

    def cleanup(self):
        for uid in self.running:
            if not self.remixers[uid].isAlive():
                self.running.remove(uid)
                del self.remixers[uid]

    def isAvailable(self):
        return len(self.running) < config.maximum_concurrent_remixes and self.countInHour() < config.hourly_remix_limit

    def isAccepting(self):
        return len(self.running) < config.maximum_waiting_remixes and self.countInHour() < config.hourly_remix_limit

    def countInHour(self):
        return self.db.query(self.db.Event).filter_by(action='upload').filter(self.db.Event.start > datetime.now() - timedelta(hours = 1)).count()

    def errorRate(self, hours = 2):
        failed = self.db.query(self.db.Event).filter_by(action="remix", success=False).filter(self.db.Event.start > datetime.now() - timedelta(hours = hours)).count()
        total  = self.db.query(self.db.Event).filter_by(action="remix").filter(self.db.Event.start > datetime.now() - timedelta(hours = hours)).count()
        try:
            return failed / total
        except:
            return 0

    def errorRateExceeded(self, hours = 2):
        return self.errorRate(hours) > 0.5

