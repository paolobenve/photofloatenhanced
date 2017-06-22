import sys

usrOptions = {}
OptionsForJs = []
def SetOptions(config_file = ""):
	global usrOptions, OptionsForJs
	from CachePath import message, next_level, back_level
	
	DefaultOptions = {
		'max_verbose'                      : 0, # verbosity level, python only
		'indexHtmlPath'                    : "", # absolute path of the folder where index.html resides, by default albumPath is "albums" inside it and cachePath is cache inside it
		'albumPath'                        : "", # absolute path, for use in python
		'serverAlbumPath'                  : "albums", # relative path, for use in js, no trailing slash
		'cachePath'                        : "", # absolute path, for use in python 
		'serverCachePath'                  : "cache", # relative path, for use in js, no trailing slash
		'thumbSizes'                       : [ (1600, False), (1200, False), (800, False), (150, True) ],
		'language'                         : "", # overrides browser language
		'thumbSpacing'                     : "3px", # string!
		'videoTranscodeBitrate'            : "4M",
		'foldersString'                    : "_folders",
		'byDateString'                     : "_by_date",
		'cacheFolderSeparator'             : "-",
		'pageTitle'                        : "My photos",
		'differentAlbumThumbnails'         : False,
		'thumbnailsGenerationMode'         : "cascade", # permitted values: "cascade", "parallel", "mixed"
		'showMediaNamesBelowInAlbums'      : True,
		'titleFontSize'                    : "medium",	# other values: large, small, or a px/em size
		'titleColor'                       : "white",
		'titleColorHover'                  : "yellow",
		'titleImageNameColor'              : "green",
		'jpegQuality'                      : 95,	# an integer number 1 -100
		'backgroundColor'                  : "#222222",	# ~ gray
		'switchButtonBackgroundColor'      : "black",
		'switchButtonBackgroundColorHover' : "white",
		'switchButtonColor'                : "white",
		'switchButtonColorHover'           : "black"
	}
	
	if config_file:
		execfile(config_file)
	OptionsForJs = [
		'serverAlbumPath',
		'serverCachePath',
		'cachePath',
		'language',	# DONE
		'thumbSpacing',	# DONE
		'foldersString',	# DONE
		'byDateString',	# DONE
		'cacheFolderSeparator',	# DONE
		'pageTitle',	# DONE
		'differentAlbumThumbnails',	# DONE
		'showMediaNamesBelowInAlbums',	# DONE
		'titleFontSize',	# DONE
		'titleColor',	# DONE
		'titleColorHover',	# DONE
		'titleImageNameColor',	# DONE
		'backgroundColor',	# DONE
		'switchButtonBackgroundColor',	# DONE
		'switchButtonBackgroundColorHover',	# DONE
		'switchButtonColor',	# DONE
		'switchButtonColorHover',	# DONE
		'thumbSizes'	# DONE
	]
	for key in DefaultOptions :
		try:
			usrOptions[key]
		except KeyError:
			usrOptions[key] = DefaultOptions[key]
	if len(sys.argv) == 3:
		usrOptions['albumPath'] = sys.argv[1]
		usrOptions['cachePath'] = sys.argv[2]
	if not usrOptions['indexHtmlPath'] and not usrOptions['albumPath'] and not usrOptions['cachePath']:
		message("options", "at least indexHtmlPath or both albumPath and cachePath must be given, quitting")
		sys.exit(-97)
	elif usrOptions['indexHtmlPath'] and not usrOptions['albumPath'] and not usrOptions['cachePath']:
		message("options", "on indexHtmlPath is given, using its subfolder 'albums' for albumPath and 'cache' for cachePath")
		usrOptions['albumPath'] = os.path.join(usrOptions['indexHtmlPath'], "albums")
		usrOptions['cachePath'] = os.path.join(usrOptions['indexHtmlPath'], "cache")
	elif (not usrOptions['indexHtmlPath'] and
			usrOptions['albumPath'] and
			usrOptions['cachePath'] and
			usrOptions['albumPath'][:usrOptions['albumPath'].rfind("/")] == usrOptions['cachePath'][:usrOptions['albumPath'].rfind("/")]):
		usrOptions['indexHtmlPath'] = usrOptions['albumPath'][:usrOptions['albumPath'].rfind("/")]
	message("Options", "asterisk denotes options changed by config file")
	next_level()
	
	for key in usrOptions:
		if DefaultOptions[key] == usrOptions[key]:
			option = "  "
		else:
			option = "* "
		option += str(usrOptions[key])
		message(key, option)
	back_level()