# Hello.
# You can change the default settings by putting them in a
# file called "settings_local.py" instead of modifying this.

import os

# TODO: try loading this from ~/.i8bp_settings.py and also /etc/i8bpsettings.py too

### Saving server side ###

# directory containing level update save files
HISTORYDIR = "server/history"
# directory where all client data is saved
CLIENTDATADIR = "server/clientdata"
# how often to check for new saves
SAVEINTERVAL = 2
# save after there have been no edits for this long
SAVEAFTER = 30

# whether or not the server should send email when it encounters an exception
SERVER_EMAIL_EXCEPTIONS = False
# the address where the email should be sent
ADMIN_EMAIL = 'chrism@infiniteplatformer.com'
# the address where the email should come from
FROM_EMAIL = 'infinite@dor.cx'
# email server configuration options
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_SSL = False
EMAIL_USERNAME = ''
EMAIL_PASSWORD = ''

# the key of the admin user
ADMIN_KEY = "xxxxx-xxxx-xxxx-xxxx"

# server host
SERVER_HOST = "i8bp.infiniteplatformer.com"

### Items ###

# how long items should disappear for
ITEMHIDETIME = 30

if os.path.isfile(os.path.join(".", "settings_local.py")):
	from settings_local import *

