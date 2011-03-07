import os

# TODO: try loading this from ~/.i8bp_settings.py and also /etc/i8bpsettings.py

### Saving server side ###

# directory containing level update save files
HISTORYDIR = "server/history"
# directory where all client data is saved
CLIENTDATADIR = "server/clientdata"
# how often to check for new saves
SAVEINTERVAL = 2
# save after there have been no edits for this long
SAVEAFTER = 30

### Items ###

# how long items should disappear for
ITEMHIDETIME = 30

if os.path.isfile(os.path.join(".", "settings_local.py")):
	from settings_local import *

