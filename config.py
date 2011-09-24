# Check required version numbers
import tornado
import tornadio
assert tornado.version_info >= (2, 0, 0), "Tornado v2 or greater is required!"
assert tornadio.__version__ >= (0, 0, 4), "Tornadio v0.0.4 or greater is required!"

# Frontend settings
app_name = "the Beatbox Machine"

# Remixer settings
maximum_concurrent_remixes = 1
maximum_waiting_remixes = 4
hourly_remix_limit = 30
cleanup_timeout = 60*30 #in minutes

thumbnail_size = (128, 128)

# Number of recent remixes to display on the monitor page
monitor_limit = 20

# Server settings
nginx = True
database_connect_string = 'mysql+mysqldb://root:@localhost/beatboxmachine'

# Backend log-to-file
log_file = 'log.txt'
log_name = "web"
log_format = '%(asctime)s (%(levelname)s) %(module)s:%(lineno)d: %(message)s'

# Allowed mimetypes and file extensions
allowed_file_extensions = ['.mp3', '.m4a', '.mp4', '.wav']

# Format of track identifiers (currently UUIDs)
import uuid
uid = lambda: str( uuid.uuid4() ).replace( '-', '' )
uid_re = r'[a-f0-9]{32}'

# Socket.IO variables, needed in JS and backend
port = 8889 # put behind Nginx or something
socket_io_port = 8002
socket_extra_sep = '/'
monitor_resource = 'watch'
progress_resource = 'progress'

# Soundcloud settings and strings
soundcloud_consumer = "6325e96fcef18547e6552c23b4c0788c"  #dev: "a777862d216790ce1b8668899cd058fd"
soundcloud_secret = "2bc846e4b317357494138ca34e3e92ec"    #dev: "42220de44734f274f6aad4bdb2797c84"
soundcloud_redirect = 'http://beatbox.wubmachine.com/static/sc.html'
soundcloud_app_id = 28788

soundcloud_timeout = 300.0
soundcloud_description = "Created with <a href='http://beatbox.wubmachine.com'>the Beatbox Machine</a>, the automagic beatbox drum machine."
soundcloud_tag_list = ["beatboxmachine", "Auto-Beatbox"]
soundcloud_sharing_note = 'Check out my new beat!'

# Variables to be passed through to javascript.
javascript = {
    'socket_io_port': socket_io_port,
    'remember_transport': False,
    'monitor_resource': monitor_resource,
    'progress_resource': progress_resource,
    'socket_extra_sep': socket_extra_sep,
    'allowed_file_extensions': [x[1:] for x in allowed_file_extensions],
    'drop_text': 'Drop a beatbox track here to remix!',
    'upload_text': 'Click here to remix your beatbox track.',
    'soundcloud_consumer': soundcloud_consumer,
    'soundcloud_redirect': soundcloud_redirect,
}
