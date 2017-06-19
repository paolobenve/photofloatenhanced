import os.path
from datetime import datetime
from Options import Options

max_verbose = 0
def message(category, text, verbose = 0):
	if (verbose <= max_verbose):
		if message.level <= 0:
			sep = "  "
		else:
			sep = "--"
		print "%s %s%s[%s]%s%s" % (datetime.now().isoformat(), max(0, message.level) * "  |", sep, str(category), max(1, (20 - len(str(category)))) * " ", str(text))
message.level = -1
def next_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level += 1
def back_level(verbose = 0):
	if (verbose <= max_verbose):
		message.level -= 1
def set_cache_path_base(base):
	trim_base.base = base
def untrim_base(path):
	return os.path.join(trim_base.base, path)
def trim_base_custom(path, base):
	if path.startswith(base):
		path = path[len(base):]
	if path.startswith('/'):
		path = path[1:]
	return path
def trim_base(path):
	return trim_base_custom(path, trim_base.base)
def cache_base(path, filepath=False):
	if len(path) == 0:
		path = "root"
	else:
		#~ elif filepath and len(path.split(os.sep)) < 2:
			#~ path = "root-" + path
		path = trim_base(path).replace('/', Options.Options['cacheFolderSeparator']).replace(' ', '_').replace('(', '').replace('&', '').replace(',', '').replace(')', '').replace('#', '').replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace('_-_', '-').lower()
		while path.find("--") != -1:
			path = path.replace("--", "-")
		while path.find("__") != -1:
			path = path.replace("__", "_")
	return path
def json_name(path):
	return cache_base(path) + ".json"
def image_cache(path, size, square=False):
	if square:
		suffix = str(size) + "s"
	else:
		suffix = str(size)
	return cache_base(path, True) + "_" + suffix + ".jpg"
def video_cache(path):
	return cache_base(path, True) + ".mp4"
def file_mtime(path):
	return datetime.fromtimestamp(int(os.path.getmtime(path)))
