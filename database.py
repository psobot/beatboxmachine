from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *
from config import database_connect_string
import datetime

Base = declarative_base()

class Track( Base ):
    __tablename__ = 'tracks'
    id = Column( Integer, primary_key=True )
    uid = Column( CHAR( length=32 ) )
    time = Column( DateTime )
    hash = Column( CHAR( length=32 ) )
    size = Column( Integer )
    
    # Tag Attributes
    length = Column( Integer )
    samplerate = Column( Integer )
    channels = Column( Integer )
    extension = Column( String )
    bitrate = Column( Integer )

    title = Column( String )
    artist = Column( String )
    album = Column( String )
    
    art = Column( String )
    thumbnail = Column( String )
    
    events = relationship( "Event" )

    def __init__( self, uid, hash = None, size = None, length = None, samplerate = None, channels = None, extension = None, bitrate = None, title = None, artist = None, album = None, art = None, thumbnail = None ):
        self.uid = uid
        self.time = datetime.datetime.now()
        
        self.hash = hash
        self.size = size

        self.length = length
        self.samplerate = samplerate
        self.channels = channels
        self.extension = extension
        self.bitrate = bitrate

        self.title = title
        self.artist = artist
        self.album = album

        self.art = art
        self.thumbnail = thumbnail

class Event( Base ):
    __tablename__ = 'events'
    id = Column( Integer, primary_key=True )
    uid = Column( CHAR( length=32 ) , ForeignKey('tracks.uid') )
    action = Column( String )
    start = Column( DateTime )
    end = Column( DateTime )
    success = Column( Boolean )
    ip = Column( String )
    detail = Column( Text )
    track = relationship( "Track" )

    def __init__( self, uid, action, success = None, ip = None, detail = None ):
        self.uid = uid
        self.start = datetime.datetime.now()
        if success is not None:
            self.end = datetime.datetime.now()
        self.action = action
        self.success = success 
        self.ip = ip
        self.detail = detail

    def time( self ):
        try:
            return self.end - self.start
        except:
            return datetime.timedelta( 0 )

def getdb():
    try:
        return db
    except:
        engine = create_engine( database_connect_string, echo=False )
        db = sessionmaker( bind = engine, autocommit=True, autoflush=True )()
        db.Track = Track
        db.Event = Event
        return db

