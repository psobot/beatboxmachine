import config, os

class Cleanup():
    directories = ['tmp', 'uploads', 'static/songs']
    keep = ['thumb', 'empty']
    artdir = "static/songs"
    log = None
    db = None
    remixQueue = None

    def __init__(self, log, db, remixQueue):
        self.log = log
        self.db = db
        self.remixQueue = remixQueue

    def all(self):
        for d in self.directories:
            if not os.path.exists(d):
                self.log.info("\t\Creating directory %s..." % d)
                os.mkdir(d)
            else:
                self.log.info("\t\tPurging directory %s..." % d)
                for f in os.listdir(d):
                    if not any([k in f for k in self.keep]):
                        p = os.path.join(d, f)
                        self.log.info("\t\t\tRemoving %s..." % p)
                        os.remove(p)
        self.thumbnails()

    def active(self):
        self.log.info("Cleaning up...")
        for uid in self.remixQueue.finished.keys():
            self.log.info("\tClearing: %s" % uid)
            for d in self.directories:
                for f in os.listdir(d):
                    if uid in f and not any([k in f for k in self.keep]):
                        p = os.path.join(d, f)
                        self.log.info("\t\tRemoving %s..." % f)
                        os.remove(p)
            del self.remixQueue.finished[uid]
        self.thumbnails()

    def thumbnails(self):
        self.log.info("\tRemoving old thumbnails...")
        thumbs = [os.path.basename(thumb) for (thumb,) in self.db.query(self.db.Track.thumbnail).order_by(self.db.Track.id.desc()).limit(config.monitor_limit).all() if thumb is not None]
        for f in os.listdir(self.artdir):
            if os.path.basename(f) not in thumbs:
                p = os.path.join(self.artdir, f)
                self.log.info("\t\tRemoving %s..." % p)
                os.remove(p)

