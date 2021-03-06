# -*- coding: utf-8 -*-

# @python2
from __future__ import unicode_literals

import os
import os.path
import sys
import json
import re
import time
import random
import math

from datetime import datetime

from PIL import Image

from CachePath import remove_album_path, file_mtime, last_modification_time, trim_base_custom, remove_folders_marker
from Utilities import message, next_level, back_level, report_times
from PhotoAlbum import Media, Album, PhotoAlbumEncoder
from Geonames import Geonames
import Options
from CachePath import convert_to_ascii_only, remove_accents, remove_non_alphabetic_characters, remove_digits, switch_to_lowercase, phrase_to_words

class TreeWalker:
	def __init__(self):
		# # check whether the albums or the cache has been modified after the last run, actually comparing with options file modification time
		# # use the same method as in file_mtime:
		# # datetime.fromtimestamp(int(os.path.getmtime(path)))
		# message("getting albums last mtime...", "be patient, x time is needed!", 4)
		# last_album_modification_time = last_modification_time(Options.config['album_path'])
		# next_level()
		# message("albums last mtime got", str(last_album_modification_time), 4)
		# back_level()

		# message("getting cache last mtime...", "be even more patient, 12x time could be needed!", 4)
		# last_cache_modification_time = last_modification_time(Options.config['cache_path'])
		# next_level()
		# message("cache last mtime got", str(last_cache_modification_time), 4)
		# json_options_file_modification_time = file_mtime(os.path.join(Options.config['cache_path'], "options.json"))
		# message("json options file mtime is", str(json_options_file_modification_time), 4)
		# if len(sys.argv) == 2:
		# 	options_file_modification_time = file_mtime(sys.argv[1])
		# 	message("options file mtime is", str(options_file_modification_time), 4)
		# back_level()

		if (Options.config['use_stop_words']):
			self.get_lowercase_stopwords()

		# # If nor the albums nor the cache have been modified after the last run,
		# # and if sensitive options haven't changed,
		# # we can avoid browsing the albums
		# if (
		# 	# the cache must be newer than albums
		# 	last_album_modification_time < json_options_file_modification_time and
		# 	# the json options file must be newer than albums
		# 	last_album_modification_time < last_cache_modification_time and
		# 	# the cache must be newer than the supplied options file too: physical paths could have been changed
		# 	(len(sys.argv) == 2 and options_file_modification_time < last_cache_modification_time) and
		# 	not Options.config['recreate_json_files'] and
		# 	not Options.config['recreate_reduced_photos'] and
		# 	not Options.config['recreate_thumbnails']
		# ):
		# 	message("no albums modification, no refresh needed", "We can safely end here", 4)
		# else:
		message("Browsing", "start!", 3)

		random.seed()
		self.all_json_files = ["options.json"]
		self.all_json_files_by_subdir = {}

		# be sure reduced_sizes array is correctly sorted
		Options.config['reduced_sizes'].sort(reverse=True)

		geonames = Geonames()
		self.all_albums = list()
		self.tree_by_date = {}
		self.tree_by_geonames = {}
		self.tree_by_search = {}
		self.media_with_geonames_list = list()
		self.all_media = list()
		self.all_album_composite_images = list()
		self.album_cache_path = os.path.join(Options.config['cache_path'], Options.config['cache_album_subdir'])
		if os.path.exists(self.album_cache_path):
			if not os.access(self.album_cache_path, os.W_OK):
				message("FATAL ERROR", self.album_cache_path + " not writable, quitting")
				sys.exit(-97)
		else:
			message("creating still unexistent album cache subdir", self.album_cache_path, 4)
			os.makedirs(self.album_cache_path)
			next_level()
			message("still unexistent subdir created", "", 5)
			back_level()

		self.origin_album = Album(Options.config['album_path'])
		# self.origin_album.read_album_ini() # origin_album is not a physical one, it's the parent of the root physical tree and of the virtual albums
		self.origin_album.cache_base = "root"
		next_level()
		[folders_album, num, _] = self.walk(Options.config['album_path'], Options.config['folders_string'], self.origin_album)
		back_level()
		if folders_album is None:
			message("WARNING", "ALBUMS ROOT EXCLUDED BY MARKER FILE", 2)
		else:
			message("saving all media json file...", "", 4)
			next_level()
			self.save_all_media_json()
			back_level()
			next_level()
			message("all media json file saved", "", 5)
			back_level()

			self.all_json_files.append("all_media.json")

			folders_album.num_media_in_sub_tree = num
			self.origin_album.add_album(folders_album)
			self.all_json_files.append(Options.config['folders_string'] + ".json")

			message("generating by date albums...", "", 4)
			by_date_album = self.generate_date_albums(self.origin_album)
			next_level()
			message("by date albums generated", "", 5)
			back_level()
			if by_date_album is not None and not by_date_album.empty:
				self.all_json_files.append(Options.config['by_date_string'] + ".json")
				self.origin_album.add_album(by_date_album)

			if self.tree_by_geonames:
				message("generating by geonames albums...", "", 4)
				by_geonames_album = self.generate_geonames_albums(self.origin_album)
				next_level()
				message("by geonames albums generated", "", 5)
				back_level()
				if by_geonames_album is not None and not by_geonames_album.empty:
					self.all_json_files.append(Options.config['by_gps_string'] + ".json")
					self.origin_album.add_album(by_geonames_album)

			message("generating by search albums...", "", 4)
			by_search_album = self.generate_by_search_albums(self.origin_album)
			next_level()
			message("by search albums generated", "", 5)
			back_level()
			if by_search_album is not None and not by_search_album.empty:
				self.all_json_files.append(Options.config['by_search_string'] + ".json")
				self.origin_album.add_album(by_search_album)

			message("saving all albums to json files...", "", 4)
			next_level()
			try:
				self.all_albums_to_json_file(folders_album, True, True)
			except UnboundLocalError:
				pass

			try:
				self.all_albums_to_json_file(by_date_album, True, True)
			except UnboundLocalError:
				pass
			try:
				self.all_albums_to_json_file(by_geonames_album, True, True)
			except UnboundLocalError:
				pass

			# search albums in by_search_album has the normal albums as subalbums,
			# and they are saved when folders_album is saved, avoid saving them multiple times
			try:
				self.all_albums_to_json_file(by_search_album, True, False)
			except UnboundLocalError:
				pass

			message("all albums saved to json files", "", 5)
			back_level()

			# options must be saved when json files have been saved, otherwise in case of error they may not reflect the json files situation
			self._save_json_options()
			self.remove_stale()
			message("completed", "", 4)

	def all_albums_to_json_file(self, album, save_subalbums, save_subsubalbums):
		if save_subalbums:
			for sub_album in album.subalbums_list:
				self.all_albums_to_json_file(sub_album, save_subsubalbums, True)
		album.to_json_file()

	def generate_date_albums(self, origin_album):
		next_level()
		# convert the temporary structure where media are organized by year, month, date to a set of albums

		by_date_path = os.path.join(Options.config['album_path'], Options.config['by_date_string'])
		by_date_album = Album(by_date_path)
		by_date_album.parent = origin_album
		by_date_album.cache_base = Options.config['by_date_string']
		by_date_max_file_date = None
		for year, _ in self.tree_by_date.items():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			year_album.parent = by_date_album
			year_album.cache_base = by_date_album.cache_base + Options.config['cache_folder_separator'] + year
			year_max_file_date = None
			by_date_album.add_album(year_album)
			for month, _ in self.tree_by_date[year].items():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				month_album.parent = year_album
				month_album.cache_base = year_album.cache_base + Options.config['cache_folder_separator'] + month
				month_max_file_date = None
				year_album.add_album(month_album)
				for day, media in self.tree_by_date[year][month].items():
					message("working with day album...", "", 5)
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					day_album.parent = month_album
					day_album.cache_base = month_album.cache_base + Options.config['cache_folder_separator'] + day
					day_max_file_date = None
					month_album.add_album(day_album)
					for single_media in media:
						single_media.day_album_cache_base = day_album.cache_base
						day_album.add_media(single_media)
						day_album.num_media_in_sub_tree += 1
						day_album.num_media_in_album += 1
						month_album.add_media(single_media)
						month_album.num_media_in_sub_tree += 1
						year_album.add_media(single_media)
						year_album.num_media_in_sub_tree += 1
						by_date_album.add_media(single_media)
						by_date_album.num_media_in_sub_tree += 1
						single_media_date = max(single_media.datetime_file, single_media.datetime_dir)
						if day_max_file_date:
							day_max_file_date = max(day_max_file_date, single_media_date)
						else:
							day_max_file_date = single_media_date
						if month_max_file_date:
							month_max_file_date = max(month_max_file_date, single_media_date)
						else:
							month_max_file_date = single_media_date
						if year_max_file_date:
							year_max_file_date = max(year_max_file_date, single_media_date)
						else:
							year_max_file_date = single_media_date
						if by_date_max_file_date:
							by_date_max_file_date = max(by_date_max_file_date, single_media_date)
						else:
							by_date_max_file_date = single_media_date
					self.all_albums.append(day_album)
					self.generate_composite_image(day_album, day_max_file_date)
					next_level()
					message("day album worked out", media[0].year + "-" + media[0].month + "-" + media[0].day, 4)
					back_level()
				self.all_albums.append(month_album)
				self.generate_composite_image(month_album, month_max_file_date)
			self.all_albums.append(year_album)
			self.generate_composite_image(year_album, year_max_file_date)
		self.all_albums.append(by_date_album)
		if by_date_album.num_media_in_sub_tree > 0:
			self.generate_composite_image(by_date_album, by_date_max_file_date)
		back_level()
		return by_date_album

	def generate_by_search_albums(self, origin_album):
		next_level()
		# convert the temporary structure where media are organized by words to a set of albums

		by_search_path = os.path.join(Options.config['album_path'], Options.config['by_search_string'])
		by_search_album = Album(by_search_path)
		by_search_album.parent = origin_album
		by_search_album.cache_base = Options.config['by_search_string']
		by_search_max_file_date = None
		message("working with word albums...", "", 5)
		for word, media_and_album_words in self.tree_by_search.items():
			next_level()
			message("working with word album...", "", 5)
			word_path = os.path.join(by_search_path, str(word))
			word_album = Album(word_path)
			word_album.parent = by_search_album
			word_album.cache_base = by_search_album.generate_cache_base(os.path.join(by_search_album.path, word))
			word_max_file_date = None
			by_search_album.add_album(word_album)
			for single_media in media_and_album_words["media_words"]:
				word_album.add_media(single_media)
				word_album.num_media_in_sub_tree += 1
				word_album.num_media_in_album += 1
				by_search_album.num_media_in_sub_tree += 1
				single_media_date = max(single_media.datetime_file, single_media.datetime_dir)
				if word_max_file_date:
					word_max_file_date = max(word_max_file_date, single_media_date)
				else:
					word_max_file_date = single_media_date
				if by_search_max_file_date:
					by_search_max_file_date = max(by_search_max_file_date, single_media_date)
				else:
					by_search_max_file_date = single_media_date
			for single_album in media_and_album_words["album_words"]:
				word_album.add_album(single_album)
				word_album.num_media_in_sub_tree += single_album.num_media_in_sub_tree
				word_album.num_media_in_album += 1
				by_search_album.num_media_in_sub_tree += single_album.num_media_in_sub_tree
				if word_max_file_date:
					word_max_file_date = max(word_max_file_date, single_album.date)
				else:
					word_max_file_date = single_album.date
				if by_search_max_file_date:
					by_search_max_file_date = max(by_search_max_file_date, single_album.date)
				else:
					by_search_max_file_date = single_album.date
			word_album.unicode_words = media_and_album_words["unicode_words"]
			self.all_albums.append(word_album)
			# self.generate_composite_image(word_album, word_max_file_date)
			next_level()
			message("word album worked out", word, 4)
			back_level()
			back_level()
		self.all_albums.append(by_search_album)
		back_level()
		return by_search_album


	def generate_geonames_albums(self, origin_album):
		next_level()
		# convert the temporary structure where media are organized by country_code, region_code, place_code to a set of albums

		by_geonames_path = os.path.join(Options.config['album_path'], Options.config['by_gps_string'])
		by_geonames_album = Album(by_geonames_path)
		by_geonames_album.parent = origin_album
		by_geonames_album.cache_base = Options.config['by_gps_string']
		by_geonames_max_file_date = None
		for country_code, _ in self.tree_by_geonames.items():
			country_path = os.path.join(by_geonames_path, str(country_code))
			country_album = Album(country_path)
			country_album.center = {}
			country_album.parent = by_geonames_album
			country_album.cache_base = by_geonames_album.generate_cache_base(os.path.join(by_geonames_album.path, country_code))
			country_max_file_date = None
			by_geonames_album.add_album(country_album)
			for region_code, _ in self.tree_by_geonames[country_code].items():
				region_path = os.path.join(country_path, str(region_code))
				region_album = Album(region_path)
				region_album.center = {}
				region_album.parent = country_album
				region_album.cache_base = country_album.generate_cache_base(os.path.join(country_album.path, region_code))
				region_max_file_date = None
				country_album.add_album(region_album)
				for place_code, media_list in self.tree_by_geonames[country_code][region_code].items():
					place_code = str(place_code)
					place_name = media_list[0].place_name
					message("working with place album...", media_list[0].country_name + "-" + media_list[0].region_name + "-" + place_name, 4)
					next_level()
					message("sorting media...", "", 5)
					media_list.sort(key=lambda m: m.latitude)
					next_level()
					message("media sorted", "", 5)
					back_level()
					# check if there are too many media in album
					# in case, "place" album will be split in "place (subalbum 1)", "place (subalbum 2)",...
					# clustering is made with the kmeans algorithm
					# transform media_list in an element in a list, probably most times, we'll work with it
					message("checking if it's a big list...", "", 5)
					if len(media_list) > Options.config['big_virtual_folders_threshold']:
						next_level()
						K = 2
						clustering_failed = False
						# this array is used in order to detect when there is no convertion
						max_cluster_length_list = [0, 0, 0]
						message("big list found", str(len(media_list)) + " photos", 5)
						next_level()
						while True:
							message("clustering with k-means algorithm...", "K = " + str(K), 5)
							cluster_list = Geonames.find_centers(media_list, K)
							max_cluster_length = max([len(cluster) for cluster in cluster_list])
							if max_cluster_length <= Options.config['big_virtual_folders_threshold']:
								next_level()
								message("clustered with k-means algorithm", "OK!", 5)
								back_level()
								break
							# detect no convergence
							max_cluster_length_list.append(max_cluster_length)
							max_cluster_length_list.pop(0)
							if max(max_cluster_length_list) > 0 and max(max_cluster_length_list) == min(max_cluster_length_list):
								# three times the same value: no convergence
								next_level()
								message("clustering with k-means algorithm failed", "max cluster length doesn't converge, it's stuck at " + str(max_cluster_length), 5)
								back_level()
								clustering_failed = True
								break

							if K > len(media_list):
								next_level()
								message("clustering with k-means algorithm failed", "clusters remain too big even with k > len(media_list)", 5)
								back_level()
								clustering_failed = true
								break
							next_level()
							message("clustering with k-means algorithm not ok", "biggest cluster has " + str(max_cluster_length) + " photos", 5)
							back_level()
							K = K * 2
						next_level()
						if clustering_failed:
							# we must split the big clusters into smaller ones
							# but firts sort media in cluster by date, so that we get more homogeneus clusters
							message("splitting big clusters into smaller ones...", "", 5)
							cluster_list_new = list()
							n = 0
							for cluster in cluster_list:
								n += 1
								next_level()
								message("working with cluster...", "n." + str(n), 5)

								integer_ratio = len(cluster) // Options.config['big_virtual_folders_threshold']
								if integer_ratio >= 1:
									# big cluster

									# sort the cluster by date
									next_level()
									message("sorting cluster by date...", "", 5)
									cluster.sort()
									next_level()
									message("cluster sorted by date", "", 5)
									back_level()

									message("splitting cluster...", "", 5)
									new_length = len(cluster) // (integer_ratio + 1)
									for index in range(integer_ratio):
										start = index * new_length
										end = (index + 1) * new_length
										cluster_list_new.append(cluster[start:end])
									# the remaining is still to be appended
									cluster_list_new.append(cluster[end:])
									next_level()
									message("cluster splitted", "", 5)
									back_level()
									back_level()
								else:
									next_level()
									message("cluster is OK", "", 5)
									back_level()
									cluster_list_new.append(cluster)
								back_level()
							cluster_list = cluster_list_new[:]
							max_cluster_length = max([len(cluster) for cluster in cluster_list])
							next_level()
							message("big clusters splitted into smaller ones", "biggest cluster lenght is now " + str(max_cluster_length), 5)
							back_level()

						message("clustering terminated", "there are " + str(len(cluster_list)) + " clusters", 5)
						back_level()
						back_level()
						back_level()

					else:
						next_level()
						message("it's not a big list", "", 5)
						back_level()
						cluster_list = [media_list]

					# iterate on cluster_list
					num_digits = len(str(len(cluster_list)))
					alt_place_code = place_code
					alt_place_name = place_name
					set_alt_place = len(cluster_list) > 1
					for i, cluster in enumerate(cluster_list):
						if set_alt_place:
							next_level()
							message("working with clusters", str(i) + "-th cluster", 5)
							alt_place_code = place_code + "_" + str(i + 1).zfill(num_digits)
							alt_place_name = place_name + "_" + str(i + 1).zfill(num_digits)

						place_path = os.path.join(region_path, str(alt_place_code))
						place_album = Album(place_path)
						place_album.center = {}
						place_album.parent = region_album
						place_album.cache_base = region_album.generate_cache_base(os.path.join(region_album.path, place_code))
						place_max_file_date = None
						region_album.add_album(place_album)
						for j, single_media in enumerate(cluster):
							single_media.gps_album_cache_base = place_album.cache_base
							cluster[j].gps_path = remove_album_path(place_path)
							cluster[j].place_name = place_name
							cluster[j].alt_place_name = alt_place_name
							place_album.add_media(single_media)
							place_album.num_media_in_sub_tree += 1
							place_album.num_media_in_album += 1
							region_album.add_media(single_media)
							region_album.num_media_in_sub_tree += 1
							country_album.add_media(single_media)
							country_album.num_media_in_sub_tree += 1
							by_geonames_album.add_media(single_media)
							by_geonames_album.num_media_in_sub_tree += 1

							if place_album.center == {}:
								place_album.center['latitude'] = single_media.latitude
								place_album.center['longitude'] = single_media.longitude
								place_album._name = place_name
								place_album.alt_name = alt_place_name
							else:
								place_album.center['latitude'] = Geonames.recalculate_mean(place_album.center['latitude'], len(place_album.media_list), single_media.latitude)
								place_album.center['longitude'] = Geonames.recalculate_mean(place_album.center['longitude'], len(place_album.media_list), single_media.longitude)

							if region_album.center == {}:
								region_album.center['latitude'] = single_media.latitude
								region_album.center['longitude'] = single_media.longitude
								region_album._name = single_media.region_name
							else:
								region_album.center['latitude'] = Geonames.recalculate_mean(region_album.center['latitude'], len(region_album.media_list), single_media.latitude)
								region_album.center['longitude'] = Geonames.recalculate_mean(region_album.center['longitude'], len(region_album.media_list), single_media.longitude)

							if country_album.center == {}:
								country_album.center['latitude'] = single_media.latitude
								country_album.center['longitude'] = single_media.longitude
								country_album._name = single_media.country_name
							else:
								country_album.center['latitude'] = Geonames.recalculate_mean(country_album.center['latitude'], len(country_album.media_list), single_media.latitude)
								country_album.center['longitude'] = Geonames.recalculate_mean(country_album.center['longitude'], len(country_album.media_list), single_media.longitude)

							single_media_date = max(single_media.datetime_file, single_media.datetime_dir)
							if place_max_file_date:
								place_max_file_date = max(place_max_file_date, single_media_date)
							else:
								place_max_file_date = single_media_date
							if region_max_file_date:
								region_max_file_date = max(region_max_file_date, single_media_date)
							else:
								region_max_file_date = single_media_date
							if country_max_file_date:
								country_max_file_date = max(country_max_file_date, single_media_date)
							else:
								country_max_file_date = single_media_date
							if by_geonames_max_file_date:
								by_geonames_max_file_date = max(by_geonames_max_file_date, single_media_date)
							else:
								by_geonames_max_file_date = single_media_date
						self.all_albums.append(place_album)
						self.generate_composite_image(place_album, place_max_file_date)
						if set_alt_place:
							next_level()
							message("cluster worked out", str(i) + "-th cluster: " + cluster[0].country_code + "-" + cluster[0].region_code + "-" + alt_place_name, 4)
							back_level()
							back_level()
						else:
							# next_level()
							message("place album worked out", cluster[0].country_code + "-" + cluster[0].region_code + "-" + alt_place_name, 4)
							# back_level()
					if set_alt_place and len(cluster_list[0]) >= 1:
						# next_level()
						message("place album worked out", cluster_list[0][0].country_code + "-" + cluster_list[0][0].region_code + "-" + place_name, 4)
						# back_level()
					back_level()
				self.all_albums.append(region_album)
				self.generate_composite_image(region_album, region_max_file_date)
			self.all_albums.append(country_album)
			self.generate_composite_image(country_album, country_max_file_date)
		self.all_albums.append(by_geonames_album)
		if by_geonames_album.num_media_in_sub_tree > 0:
			self.generate_composite_image(by_geonames_album, by_geonames_max_file_date)
		back_level()
		return by_geonames_album

	def add_media_to_tree_by_date(self, media):
		# add the given media to a temporary structure where media are organized by year, month, date

		if media.year not in list(self.tree_by_date.keys()):
			self.tree_by_date[media.year] = {}
		if media.month not in list(self.tree_by_date[media.year].keys()):
			self.tree_by_date[media.year][media.month] = {}
		if media.day not in list(self.tree_by_date[media.year][media.month].keys()):
			self.tree_by_date[media.year][media.month][media.day] = list()
		if not any(media.media_file_name == _media.media_file_name for _media in self.tree_by_date[media.year][media.month][media.day]):
		#~ if not media in self.tree_by_date[media.year][media.month][media.day]:
			self.tree_by_date[media.year][media.month][media.day].append(media)

	def remove_stopwords(self, alphabetic_words, search_normalized_words, ascii_words):
		# remove the stopwords found in alphabetic_words, from search_normalized_words and ascii_words
		purged_alphabetic_words = set(alphabetic_words) - TreeWalker.lowercase_stopwords
		purged_search_normalized_words = []
		purged_ascii_words = []
		alphabetic_words = list(alphabetic_words)
		search_normalized_words = list(search_normalized_words)
		ascii_words = list(ascii_words)
		for word_index in range(len(alphabetic_words)):
			if alphabetic_words[word_index] in purged_alphabetic_words:
				purged_search_normalized_words.append(search_normalized_words[word_index])
				purged_ascii_words.append(ascii_words[word_index])

		return purged_alphabetic_words, purged_search_normalized_words, purged_ascii_words

	# The dictionaries of stopwords for the user language
	lowercase_stopwords = {}

	@staticmethod
	def load_stopwords():
		"""
		Load the list of stopwords for the user language into the set `lowercase_stopwords`
		The list of stopwords comes from https://github.com/stopwords-iso/stopwords-iso
		"""
		language = Options.config['language'] if Options.config['language'] != '' else os.getenv('LANG')[:2]
		message("working with stopwords", "Using language " + language, 4)

		stopwords = []
		stopwords_file = os.path.join(os.path.dirname(__file__), "resources/stopwords-iso.json")
		next_level()
		message("loading stopwords...", stopwords_file, 4)
		with open(stopwords_file, "r") as stopwords_p:
			stopwords = json.load(stopwords_p)

		next_level()
		if language in stopwords:
			phrase = " ".join(stopwords[language])
			TreeWalker.lowercase_stopwords = frozenset(switch_to_lowercase(phrase).split())
			message("stopwords loaded", "", 4)
		else:
			message("stopwords: no stopwords for language", language, 4)
		back_level()
		back_level()
		return

	@staticmethod
	def get_lowercase_stopwords():
		"""
		Get the set of lowercase stopwords used when searching albums.
		Loads the stopwords from resource file if necessary.
		"""
		if TreeWalker.lowercase_stopwords == {}:
			TreeWalker.load_stopwords()

	def add_media_to_tree_by_search(self, media):
		words_for_word_list, unicode_words, words_for_search_album_name = self.prepare_for_tree_by_search(media)
		media.words = words_for_word_list
		for word_index in range(len(words_for_search_album_name)):
			word = words_for_search_album_name[word_index]
			unicode_word = unicode_words[word_index]
			if word:
				if word not in list(self.tree_by_search.keys()):
					self.tree_by_search[word] = {"media_words": [], "album_words": [], "unicode_words": []}
				if media not in self.tree_by_search[word]["media_words"]:
					self.tree_by_search[word]["media_words"].append(media)
				if unicode_word not in self.tree_by_search[word]["unicode_words"]:
					self.tree_by_search[word]["unicode_words"].append(unicode_word)

	def add_album_to_tree_by_search(self, album):
		words_for_word_list, unicode_words, words_for_search_album_name = self.prepare_for_tree_by_search(album)
		album.words = words_for_word_list
		for word_index in range(len(words_for_search_album_name)):
			word = words_for_search_album_name[word_index]
			unicode_word = unicode_words[word_index]
			if word:
				if word not in list(self.tree_by_search.keys()):
					self.tree_by_search[word] = {"media_words": [], "album_words": [], "unicode_words": []}
				if album not in self.tree_by_search[word]["album_words"]:
					self.tree_by_search[word]["album_words"].append(album)
					if unicode_word not in self.tree_by_search[word]["unicode_words"]:
						self.tree_by_search[word]["unicode_words"].append(unicode_word)


	def prepare_for_tree_by_search(self, media_or_album):
		# add the given media or album to a temporary structure where media or albums are organized by search terms
		# works on the words in the file/directory name and in album.ini's description, title, tags

		# media_or_album.name must be the last item because the normalization will remove the file extension
		media_or_album_name = media_or_album.name
		if isinstance(media_or_album, Media):
			# remove the extension
			media_or_album_name = os.path.splitext(media_or_album_name)[0]
		elements = [media_or_album.title, media_or_album.description, " ".join(media_or_album.tags), media_or_album_name]
		phrase = ' '.join(filter(None, elements))

		alphabetic_phrase = remove_non_alphabetic_characters(remove_digits(phrase))
		lowercase_phrase = switch_to_lowercase(alphabetic_phrase)
		search_normalized_phrase = remove_accents(lowercase_phrase)
		ascii_phrase = convert_to_ascii_only(search_normalized_phrase)

		alphabetic_words = phrase_to_words(alphabetic_phrase)
		lowercase_words = phrase_to_words(lowercase_phrase)
		search_normalized_words = phrase_to_words(search_normalized_phrase)
		ascii_words = phrase_to_words(ascii_phrase)

		if (Options.config['use_stop_words']):
			# remove stop words: do it according to the words in lower case, different words could be removed if performing remotion from every list
			alphabetic_words, search_normalized_words, ascii_words = self.remove_stopwords(alphabetic_words, search_normalized_words, ascii_words)
			alphabetic_words = list(alphabetic_words)

		return alphabetic_words, search_normalized_words, ascii_words


	def add_media_to_tree_by_geonames(self, media):
		# add the given media to a temporary structure where media are organized by country, region/state, place

		if media.country_code not in list(self.tree_by_geonames.keys()):
			self.tree_by_geonames[media.country_code] = {}
		if media.region_code not in list(self.tree_by_geonames[media.country_code].keys()):
			self.tree_by_geonames[media.country_code][media.region_code] = {}
		if media.place_code not in list(self.tree_by_geonames[media.country_code][media.region_code].keys()):
			self.tree_by_geonames[media.country_code][media.region_code][media.place_code] = list()
		if not any(media.media_file_name == _media.media_file_name for _media in self.tree_by_geonames[media.country_code][media.region_code][media.place_code]):
			self.tree_by_geonames[media.country_code][media.region_code][media.place_code].append(media)


	@staticmethod
	def _listdir_sorted_by_time(path):
		# this function returns the directory listing sorted by mtime
		# it takes into account the fact that the file is a symlink to an unexistent file
		mtime = lambda f: os.path.exists(os.path.join(path, f)) and os.stat(os.path.join(path, f)).st_mtime or time.mktime(datetime.now().timetuple())
		return list(sorted(os.listdir(path), key=mtime))


	def walk(self, absolute_path, album_cache_base, parent_album=None):
		#~ trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
		#~ absolute_path_with_marker = os.path.join(Options.config['album_path'], Options.config['folders_string'])
		#~ if trimmed_path:
			#~ absolute_path_with_marker = os.path.join(absolute_path_with_marker, trimmed_path)
		max_file_date = file_mtime(absolute_path)
		message("Walking                                 ", os.path.basename(absolute_path), 3)
		next_level()
		message("cache base", album_cache_base, 4)
		if not os.access(absolute_path, os.R_OK | os.X_OK):
			message("access denied to directory", os.path.basename(absolute_path), 1)
			back_level()
			return [None, 0, None]
		listdir = os.listdir(absolute_path)
		if Options.config['exclude_tree_marker'] in listdir:
			next_level()
			message("excluded with subfolders by marker file", Options.config['exclude_tree_marker'], 4)
			back_level()
			back_level()
			return [None, 0, None]
		skip_files = False
		if Options.config['exclude_files_marker'] in listdir:
			next_level()
			message("files excluded by marker file", Options.config['exclude_files_marker'], 4)
			skip_files = True
			back_level()
		json_file = os.path.join(Options.config['cache_path'], album_cache_base) + ".json"
		json_file_exists = os.path.exists(json_file)
		json_file_mtime = None
		if json_file_exists:
			json_file_mtime = file_mtime(json_file)
		json_file_OK = False
		album_ini_file = os.path.join(absolute_path, Options.config['metadata_filename'])
		can_use_existing_json_file = True
		album_ini_good = False
		must_process_album_ini = False
		if os.path.exists(album_ini_file):
			if not os.access(album_ini_file, os.R_OK):
				message("album.ini file unreadable", "", 2)
			elif os.path.getsize(album_ini_file) == 0:
				message("album.ini file has zero lenght", "", 2)
			else:
				album_ini_good = True

		cached_album = None
		json_message = json_file
		if Options.config['recreate_json_files']:
			message("forced json file recreation", "some sensible option has changed", 3)
		else:
			try:
				if json_file_exists:
					if not os.access(json_file, os.R_OK):
						message("json file unreadable", json_file, 1)
					elif not os.access(json_file, os.W_OK):
						message("json file unwritable", json_file, 1)
					else:
						if album_ini_good and file_mtime(album_ini_file) > json_file_mtime:
							# a check on album_ini_file content would have been good:
							# execution comes here even if album.ini hasn't anything significant
							message("album.ini newer than json file", "recreating json file taking into account album.ini", 4)
							can_use_existing_json_file = False
							must_process_album_ini = True
						if can_use_existing_json_file:
							message("reading json file to import album...", json_file, 5)
							# the following is the instruction which could raise the error
							cached_album = Album.from_cache(json_file, album_cache_base)
							next_level()
							message("json file read", "", 5)
							back_level()
							if (
								file_mtime(absolute_path) <= json_file_mtime and
								cached_album is not None and
								hasattr(cached_album, "absolute_path") and
								cached_album.absolute_path == absolute_path and
								Options.json_version != 0 and hasattr(cached_album, "json_version") and cached_album.json_version == Options.json_version
							):
								next_level()
								message("json file is OK", "", 4)
								back_level()
								json_file_OK = True
								album = cached_album
								message("adding media in album to big lists...", "", 5)
								for media in album.media:
									if not any(media.media_file_name == _media.media_file_name for _media in self.all_media):
										self.add_media_to_tree_by_date(media)
										if media.has_gps_data:
											self.add_media_to_tree_by_geonames(media)
										self.add_media_to_tree_by_search(media)

										self.all_media.append(media)
								next_level()
								message("added media to big lists", "", 5)
								back_level()
							else:
								next_level()
								message("json file invalid (old or invalid path)", "", 4)
								back_level()
								cached_album = None
				else:
					must_process_album_ini = True
			except KeyboardInterrupt:
				raise
			except IOError:
				# will execution never come here?
				next_level()
				message("json file unexistent", json_message, 4)
				back_level()
				json_file_OK = False
			except (ValueError, AttributeError, KeyError):
				next_level()
				message("json file invalid", json_message, 4)
				back_level()
				json_file_OK = False
				cached_album = None

		if not json_file_OK:
			message("generating void album...", "", 5)
			album = Album(absolute_path)
			next_level()
			message("void album generated", "", 5)
			back_level()

		if album_ini_good:
			if not must_process_album_ini:
				message("album.ini values already in json file", "", 2)
			else:
				album.read_album_ini(album_ini_file)

		if parent_album is not None:
			album.parent = parent_album
		album.cache_base = album_cache_base

		message("subdir for cache files", " " + album.subdir, 3)

		#~ for entry in sorted(os.listdir(absolute_path)):
		message("reading directory", absolute_path, 5)
		num_photo_in_dir = 0
		photos_without_geotag_in_dir = []
		photos_without_exif_date_in_dir = []
		for entry in self._listdir_sorted_by_time(absolute_path):
			try:
				# @python2
				if sys.version_info < (3, ):
					entry = entry.decode(sys.getfilesystemencoding())
				else:
					entry = os.fsdecode(entry)
			except KeyboardInterrupt:
				raise
			except:
				next_level()
				message("unicode error", entry, 1)
				back_level()
				continue

			if entry[0] == '.' or entry == Options.config['metadata_filename']:
				# skip hidden files and directories, or user's metadata file 'album.ini'
				continue

			entry_with_path = os.path.join(absolute_path, entry)
			if not os.path.exists(entry_with_path):
				next_level()
				message("unexistent file, perhaps a symlink, skipping", entry_with_path, 2)
				back_level()
			elif not os.access(entry_with_path, os.R_OK):
				next_level()
				message("unreadable file", entry_with_path, 2)
				back_level()
			elif os.path.islink(entry_with_path) and not Options.config['follow_symlinks']:
				# this way file symlink are skipped too: may be symlinks can be checked only for directories?
				next_level()
				message("symlink, skipping as set in options", entry_with_path, 3)
				back_level()
			elif os.path.isdir(entry_with_path):
				trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
				entry_for_cache_base = os.path.join(Options.config['folders_string'], trimmed_path, entry)
				next_level()
				message("determining cache base...", "", 5)
				next_album_cache_base = album.generate_cache_base(entry_for_cache_base)
				next_level()
				message("cache base determined", "", 5)
				back_level()
				back_level()
				[next_walked_album, num, sub_max_file_date] = self.walk(entry_with_path, next_album_cache_base, album)
				if next_walked_album is not None:
					max_file_date = max(max_file_date, sub_max_file_date)
					album.num_media_in_sub_tree += num
					album.add_album(next_walked_album)
					self.add_album_to_tree_by_search(next_walked_album)
			elif os.path.isfile(entry_with_path):
				if skip_files:
					continue
				next_level()
				cache_hit = False
				mtime = file_mtime(entry_with_path)
				max_file_date = max(max_file_date, mtime)
				media = None
				cached_media = None
				if cached_album:
					message("reading cache media from cached album...", "", 5)
					cached_media = cached_album.media_from_path(entry_with_path)
					next_level()
					message("cache media read", "", 5)
					back_level()
					if cached_media and	mtime <= cached_media.datetime_file:
						cache_files = cached_media.image_caches
						# check if the cache files actually exist and are not old
						cache_hit = True
						for cache_file in cache_files:
							absolute_cache_file = os.path.join(Options.config['cache_path'], cache_file)
							absolute_cache_file_exists = os.path.exists(absolute_cache_file)
							if (
								Options.config['recreate_fixed_height_thumbnails'] and
								absolute_cache_file_exists and file_mtime(absolute_cache_file) < json_file_mtime
							):
								# remove wide images, in order not to have blurred thumbnails
								fixed_height_thumbnail_re = "_" + str(Options.config['media_thumb_size']) + r"tf\.jpg$"
								match = re.search(fixed_height_thumbnail_re, cache_file)
								if match and cached_media.size[0] > cached_media.size[1]:
									try:
										os.unlink(os.path.join(Options.config['cache_path'], cache_file))
										message("deleted, re-creating fixed height thumbnail", os.path.join(Options.config['cache_path'], cache_file), 3)
									except OSError:
										message("error deleting fixed height thumbnail", os.path.join(Options.config['cache_path'], cache_file), 1)

							if (
								not absolute_cache_file_exists or
								json_file_OK and (
									file_mtime(absolute_cache_file) < cached_media.datetime_file or
									file_mtime(absolute_cache_file) > json_file_mtime
								) or
								(Options.config['recreate_reduced_photos'] or Options.config['recreate_thumbnails'])
							):
								cache_hit = False
								break
						if cache_hit:
							media = cached_media
							if media.is_video:
								message("reduced size transcoded video and thumbnails OK", os.path.basename(entry_with_path), 4)
							else:
								message("reduced size images and thumbnails OK", os.path.basename(entry_with_path), 4)
						#~ else:
							#~ absolute_cache_file = ""
				if not cache_hit:
					message("not a cache hit", entry_with_path, 4)
					next_level()
					if not json_file_OK:
						message("reason: json file not OK", "  " + json_message, 4)
					else:
						if cached_media is None:
							message("reason: media not cached", "", 4)
						# TODO: We can't execute the code below as cache_hit = False...
						elif cache_hit:
							if not absolute_cache_file_exists:
								message("reason: unexistent reduction/thumbnail", "", 4)
							else:
								if file_mtime(absolute_cache_file) < cached_media.datetime_file:
									message("reason: reduct/thumbn older than cached media", "", 4)
								elif file_mtime(absolute_cache_file) > json_file_mtime:
									message("reason: reduct/thumbn newer than json file", "", 4)

					if Options.config['recreate_reduced_photos']:
						message("reduced photo recreation requested", "", 4)
					if Options.config['recreate_thumbnails']:
						message("thumbnail recreation requested", "", 4)
					back_level()
					message("processing media from file", entry_with_path, 5)
					media = Media(album, entry_with_path, Options.config['cache_path'])

				if media.is_valid:
					album.num_media_in_sub_tree += 1
					album.num_media_in_album += 1
					if media.is_video:
						Options.num_video += 1
						if not cache_hit:
							Options.num_video_processed += 1
					else:
						Options.num_photo += 1
						num_photo_in_dir += 1
						if not cache_hit:
							Options.num_photo_processed += 1
						if media.has_exif_date:
							Options.num_photo_with_exif_date += 1
						else:
							photos_without_exif_date_in_dir.append(entry_with_path)
						if media.has_gps_data:
							Options.num_photo_geotagged += 1
						else:
							photos_without_geotag_in_dir.append(entry_with_path)

					next_level()
					message("adding media to by date tree...", "", 5)
					# the following function has a check on media already present
					self.add_media_to_tree_by_date(media)
					next_level()
					message("media added to by date tree", "", 5)
					back_level()

					if media.has_gps_data:
						message("adding media to by geonames tree...", "", 5)
						# the following function has a check on media already present
						self.add_media_to_tree_by_geonames(media)
						next_level()
						message("media added to by geonames tree", "", 5)
						back_level()

					message("adding media to search tree...", "", 5)
					# the following function has a check on media already present
					self.add_media_to_tree_by_search(media)
					next_level()
					message("media added to search tree", "", 5)
					back_level()

					message("adding media to album...", "", 5)
					album.add_media(media)
					next_level()
					message("media added to album", "", 5)
					back_level()

					message("adding media to big list...", "", 5)
					if not any(media.media_file_name == _media.media_file_name for _media in self.all_media):
						self.all_media.append(media)
					next_level()
					message("media added to big list", "", 5)
					back_level()

					back_level()

				elif not media.is_valid:
					next_level()
					message("not image nor video", "", 1)
					back_level()
				back_level()
		if num_photo_in_dir:
			if num_photo_in_dir == len(photos_without_geotag_in_dir):
				Options.photos_without_geotag.append(absolute_path + " (" + str(num_photo_in_dir) + " photos)")
			else:
				Options.photos_without_geotag.extend(photos_without_geotag_in_dir)
			if num_photo_in_dir == len(photos_without_exif_date_in_dir):
				Options.photos_without_exif_date.append(absolute_path + " (" + str(num_photo_in_dir) + " photos)")
			else:
				Options.photos_without_exif_date.extend(photos_without_exif_date_in_dir)
		if not album.empty:
			next_level()
			message("adding album to big list...", "", 5)
			self.all_albums.append(album)
			next_level()
			message("added album to big list", "", 4)
			back_level()
			back_level()
		else:
			message("VOID: no media in this directory", os.path.basename(absolute_path), 4)

		if album.num_media_in_sub_tree:
			# generate the album composite image for sharing
			self.generate_composite_image(album, max_file_date)
		back_level()

		report_times(False)

		return [album, album.num_media_in_sub_tree, max_file_date]


	@staticmethod
	def _index_to_coords(index, tile_width, px_between_tiles, side_off_set, linear_number_of_tiles):
		x = side_off_set + (index % linear_number_of_tiles) * (tile_width + px_between_tiles)
		y = side_off_set + int(index / linear_number_of_tiles) * (tile_width + px_between_tiles)
		return [x, y]


	def pick_random_image(self, album, random_number):
		if random_number < len(album.media_list):
			return [album.media_list[random_number], random_number]
		else:
			random_number -= len(album.media_list)
			for subalbum in album.subalbums_list:
				if random_number < subalbum.num_media_in_sub_tree:
					[picked_image, random_number] = self.pick_random_image(subalbum, random_number)
					if picked_image:
						return [picked_image, random_number]
				random_number -= subalbum.num_media_in_sub_tree
		return [None, random_number]

	def generate_composite_image(self, album, max_file_date):
		next_level()
		composite_image_name = album.cache_base + ".jpg"
		self.all_album_composite_images.append(composite_image_name)
		composite_image_path = os.path.join(self.album_cache_path, composite_image_name)
		json_file_with_path = os.path.join(Options.config['cache_path'], album.json_file)
		if (os.path.exists(composite_image_path) and
			file_mtime(composite_image_path) > max_file_date and
			os.path.exists(json_file_with_path) and
			file_mtime(json_file_with_path) < file_mtime(composite_image_path)
		):
			message("composite image OK", "", 5)
			with open(composite_image_path, 'a'):
				os.utime(composite_image_path, None)
			next_level()
			message("composite image OK, touched", composite_image_path, 4)
			back_level()
			back_level()
			return

		message("generating composite image...", composite_image_path, 5)

		# pick a maximum of Options.max_album_share_thumbnails_number random images in album and subalbums
		# and generate a square composite image

		# determine the number of images to use
		if album.num_media_in_sub_tree == 1 or Options.config['max_album_share_thumbnails_number'] == 1:
			max_thumbnail_number = 1
		elif album.num_media_in_sub_tree < 9 or Options.config['max_album_share_thumbnails_number'] == 4:
			max_thumbnail_number = 4
		elif album.num_media_in_sub_tree < 16 or Options.config['max_album_share_thumbnails_number'] == 9:
			max_thumbnail_number = 9
		elif album.num_media_in_sub_tree < 25 or Options.config['max_album_share_thumbnails_number'] == 16:
			max_thumbnail_number = 16
		elif album.num_media_in_sub_tree < 36 or Options.config['max_album_share_thumbnails_number'] == 25:
			max_thumbnail_number = 25
		else:
			max_thumbnail_number = Options.config['max_album_share_thumbnails_number']

		# pick max_thumbnail_number random square album thumbnails
		random_thumbnails = list()
		random_list = list()
		bad_list = list()
		num_random_thumbnails = min(max_thumbnail_number, album.num_media_in_sub_tree)
		i = 0
		good_media_number = album.num_media_in_sub_tree
		while True:
			if i >= good_media_number:
				break
			if len(album.media) and num_random_thumbnails == 1:
				random_media = album.media[0]
			else:
				while True:
					random_number = random.randint(0, album.num_media_in_sub_tree - 1)
					if random_number not in random_list and random_number not in bad_list:
						break
				random_list.append(random_number)
				[random_media, random_number] = self.pick_random_image(album, random_number)
			folder_prefix = remove_folders_marker(random_media.album.cache_base)
			if folder_prefix:
				folder_prefix += Options.config['cache_folder_separator']
			thumbnail = os.path.join(
					Options.config['cache_path'],
					random_media.album.subdir,
					folder_prefix + random_media.cache_base
				) + Options.config['cache_folder_separator'] + str(Options.config['album_thumb_size']) + "as.jpg"
			if os.path.exists(thumbnail):
				random_thumbnails.append(thumbnail)
				i += 1
				if i == num_random_thumbnails:
					break
			else:
				message("unexistent thumbnail", thumbnail + " - i=" + str(i) + ", good=" + str(good_media_number), 5)
				bad_list.append(thumbnail)
				good_media_number -= 1

		if len(random_thumbnails) < max_thumbnail_number:
			# add the missing images: repeat the present ones
			for i in range(max_thumbnail_number - len(random_thumbnails)):
				random_thumbnails.append(random_thumbnails[i])

		# generate the composite image
		# following code inspired from
		# https://stackoverflow.com/questions/30429383/combine-16-images-into-1-big-image-with-php#30429557
		# thanks to Adarsh Vardhan who wrote it!

		tile_width = Options.config['album_thumb_size']

		# INIT BASE IMAGE FILLED WITH BACKGROUND COLOR
		linear_number_of_tiles = int(math.sqrt(max_thumbnail_number))
		px_between_tiles = 1
		side_off_set = 1

		map_width = side_off_set + (tile_width + px_between_tiles) * linear_number_of_tiles - px_between_tiles + side_off_set
		map_height = side_off_set + (tile_width + px_between_tiles) * linear_number_of_tiles - px_between_tiles + side_off_set
		img = Image.new('RGB', (map_width, map_height), "white")

		# PUT SRC IMAGES ON BASE IMAGE
		index = -1
		for thumbnail in random_thumbnails:
			index += 1
			tile = Image.open(thumbnail)
			tile_img_width = tile.size[0]
			tile_img_height = tile.size[1]
			[x, y] = self._index_to_coords(index, tile_width, px_between_tiles, side_off_set, linear_number_of_tiles)
			if tile_img_width < tile_width:
				x += int(float(tile_width - tile_img_width) / 2)
			if tile_img_height < tile_width:
				y += int(float(tile_width - tile_img_height) / 2)
			img.paste(tile, (x, y))

		# save the composite image
		img.save(composite_image_path, "JPEG", quality=Options.config['jpeg_quality'])
		next_level()
		message("composite image generated", "", 5)
		back_level()
		back_level()


	def save_all_media_json(self):
		media_list = []
		message("sorting all media list...", "", 5)
		self.all_media.sort()
		next_level()
		message("all media list sorted", "", 5)
		back_level()
		message("building media path list...", "", 5)
		for media in self.all_media:
			media_list.append(media.path)
		next_level()
		message("media path list built", "", 5)
		back_level()
		message("caching all media path list...", "", 4)
		with open(os.path.join(Options.config['cache_path'], "all_media.json"), 'w') as all_media_file:
			json.dump(media_list, all_media_file, cls=PhotoAlbumEncoder)
		next_level()
		message("all media path list cached", "", 5)
		back_level()


	@staticmethod
	def _save_json_options():
		json_options_file = os.path.join(Options.config['cache_path'], 'options.json')
		message("saving json options file...", json_options_file, 4)
		# some option must not be saved
		options_to_save = {}
		for key, value in list(Options.config.items()):
			if key not in Options.options_not_to_be_saved:
				options_to_save[key] = value

		with open(json_options_file, 'w') as options_file:
			json.dump(options_to_save, options_file)
		next_level()
		message("saved json options file", "", 5)
		back_level()


	def remove_stale(self, subdir=""):
		if not subdir:
			message("cleaning up, be patient...", "", 3)
			next_level()
			message("building stale list...", "", 4)
			for album in self.all_albums:
				self.all_json_files.append(album.json_file)
			for media in self.all_media:
				album_subdir = media.album.subdir
				for entry in media.image_caches:
					entry_without_subdir = entry[len(album_subdir) + 1:]
					try:
						self.all_json_files_by_subdir[album_subdir].append(entry_without_subdir)
					except KeyError:
						self.all_json_files_by_subdir[album_subdir] = list()
						self.all_json_files_by_subdir[album_subdir].append(entry_without_subdir)
			next_level()
			message("stale list built", "", 5)
			back_level()
			info = "in cache path"
			deletable_files_suffixes_re = r"\.json$"
		else:
			info = "in subdir " + subdir
			# reduced sizes, thumbnails, old style thumbnails
			if subdir == Options.config['cache_album_subdir']:
				self.all_json_files_by_subdir[subdir] = list()
				for path in self.all_album_composite_images:
					self.all_json_files_by_subdir[subdir].append(path)
				deletable_files_suffixes_re = r"\.jpg$"
			else:
				deletable_files_suffixes_re = r"(" + Options.config['cache_folder_separator'] + r"|_)transcoded(_([1-9][0-9]{0,3}[kKmM]|[1-9][0-9]{3,10})(_[1-5]?[0-9])?)?\.mp4$"
				deletable_files_suffixes_re += r"|(" + Options.config['cache_folder_separator'] + r"|_)[1-9][0-9]{1,4}(a|t|s|[at][sf])?\.jpg$"
		message("searching for stale cache files", info, 4)

		for cache_file in sorted(os.listdir(os.path.join(Options.config['cache_path'], subdir))):
			if os.path.isdir(os.path.join(Options.config['cache_path'], cache_file)):
				next_level()
				self.remove_stale(cache_file)
				if not os.listdir(os.path.join(Options.config['cache_path'], cache_file)):
					next_level()
					message("empty subdir, deleting...", "", 4)
					file_to_delete = os.path.join(Options.config['cache_path'], cache_file)
					next_level()
					os.rmdir(os.path.join(Options.config['cache_path'], file_to_delete))
					message("empty subdir, deleted", "", 5)
					back_level()
					back_level()
				back_level()
			else:
				# only delete json's, transcoded videos, reduced images and thumbnails
				next_level()
				message("deciding whether to keep a cache file...", "", 7)
				match = re.search(deletable_files_suffixes_re, cache_file)
				next_level()
				message("decided whether to keep a cache file", cache_file, 6)
				back_level()
				if match:
					try:
						# @python2
						if sys.version_info < (3, ):
							cache_file = cache_file.decode(sys.getfilesystemencoding())
						else:
							cache_file = os.fsdecode(cache_file)
					except KeyboardInterrupt:
						raise
					#~ except:
						#~ pass
					if subdir:
						if subdir in self.all_json_files_by_subdir:
							cache_list = self.all_json_files_by_subdir[subdir]
						else:
							cache_list = list()
					else:
						cache_list = self.all_json_files
					if cache_file not in cache_list:
						message("removing stale cache file...", cache_file, 3)
						file_to_delete = os.path.join(Options.config['cache_path'], subdir, cache_file)
						os.unlink(file_to_delete)
						next_level()
						message("stale cache file removed", "", 5)
						back_level()
				else:
					next_level()
					message("not a stale cache file, keeping it", cache_file, 2)
					back_level()
					back_level()
					continue
				back_level()
		if not subdir:
			message("cleaned", "", 5)
			back_level()
			back_level()
