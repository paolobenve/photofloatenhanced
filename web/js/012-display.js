$(document).ready(function() {
	
	/* 
	 * The display is not yet object oriented. It's procedural code
	 * broken off into functions. It makes use of libphotofloat's
	 * PhotoFloat class for the network and management logic.
	 * 
	 * All of this could potentially be object oriented, but presently
	 * it should be pretty readable and sufficient. The only thing to
	 * perhaps change in the future would be to consolidate calls to
	 * jQuery selectors. And perhaps it'd be nice to move variable
	 * declarations to the top, to stress that JavaScript scope is
	 * for an entire function and always hoisted.
	 * 
	 * None of the globals here polutes the global scope, as everything
	 * is enclosed in an anonymous function.
	 * 
	 */
	
	/* Globals */
	
	var currentAlbum = null;
	var currentPhoto = null;
	var currentPhotoIndex = -1;
	var previousAlbum = null;
	var previousPhoto = null;
	var originalTitle = document.title;
	var photoFloat = new PhotoFloat();
	var maxSize = 1600;
	bydateString = "_by_date";
	bydateStringWithTrailingDash = bydateString + "-";
	foldersString = "_folders";
	foldersStringWithTrailingDash = foldersString + "-";
	bydateEnglishString = "images by date";
	foldersEnglishString = "folders";
	
	
	/* Displays */
	
	function setTitle() {
		var title = "", documentTitle = "", last = "", components, i;
		if (!currentAlbum.path.length)
			components = [originalTitle];
		else {
			components = currentAlbum.path.split("/");
			components.unshift(originalTitle);
		}
		if (currentPhoto !== null)
			documentTitle += photoFloat.trimExtension(currentPhoto.name);
		for (i = 0; i < components.length; ++i) {
			if (i || currentPhoto !== null)
				documentTitle += " \u00ab ";
			if (i)
				last += "/" + components[i];
			if (i < components.length - 1 || currentPhoto !== null)
				title += "<a href=\"#!/" + (i ? photoFloat.cachePath(last.substring(1)) : "") + "\">";
			var titleAdd = components[i];
			if (typeof bydateTranslation !== 'undefined')
				titleAdd = titleAdd.replace(bydateString, bydateTranslation);
			else
				titleAdd = titleAdd.replace(bydateString, bydateEnglishString);
			if (typeof foldersTranslation !== 'undefined')
				titleAdd = titleAdd.replace(foldersString, foldersTranslation);
			else
				titleAdd = titleAdd.replace(foldersString, foldersEnglishString);
			title += titleAdd;
			var documentTitleAdd = components[components.length - 1 - i];
			if (typeof bydateTranslation !== 'undefined')
				documentTitleAdd = documentTitleAdd.replace(bydateString, bydateTranslation);
			else
				documentTitleAdd = documentTitleAdd.replace(bydateString, bydateEnglishString);
			if (typeof foldersTranslation !== 'undefined')
				documentTitleAdd = documentTitleAdd.replace(foldersString, foldersTranslation);
			else
				documentTitleAdd = documentTitleAdd.replace(foldersString, foldersEnglishString);
			documentTitle += documentTitleAdd;
			if (i < components.length - 1 || currentPhoto !== null) {
				title += "</a>";
			}
			//~ if (i < components.length - 1) {
				title += " &raquo; ";
			//~ }
		}
		if (currentPhoto !== null)
			title += "<span id=\"photo-name\">" + photoFloat.trimExtension(currentPhoto.name) + "</div>";
		
		$("#title").html(title);
		document.title = documentTitle;
	}
	function scrollToThumb() {
		var photo, thumb;
		photo = currentPhoto;
		if (photo === null) {
			photo = previousPhoto;
			if (photo === null)
				return;
		}
		$("#thumbs img").each(function() {
			if (this.title === photo.name) {
				thumb = $(this);
				return false;
			}
		});
		if (typeof thumb === "undefined")
			return;
		if (currentPhoto !== null) {
			var scroller = $("#album-view");
			
			scroller.stop().animate({ scrollLeft: thumb.parent().position().left + scroller.scrollLeft() - scroller.width() / 2 + thumb.width() / 2 }, "slow");
		} else
			$("html, body").stop().animate({ scrollTop: thumb.offset().top - $(window).height() / 2 + thumb.height() }, "slow");
		
		if (currentPhoto !== null) {
			$("#thumbs img").removeClass("current-thumb");
			thumb.addClass("current-thumb");
		}
	}
	function showAlbum(populate) {
		var i, link, image, photos, thumbsElement, subalbums, subalbumsElement, hash, thumbHash;
		if (currentPhoto === null && previousPhoto === null)
			$("html, body").stop().animate({ scrollTop: 0 }, "slow");
		if (populate) {
			photos = [];
			for (i = 0; i < currentAlbum.photos.length; ++i) {
				hash = photoFloat.photoHash(currentAlbum, currentAlbum.photos[i]);
				thumbHash = photoFloat.photoPath(currentAlbum, currentAlbum.photos[i], 150, true);
				if (thumbHash.indexOf(bydateStringWithTrailingDash) === 0) {
					thumbHash =
						PhotoFloat.cachePath(currentAlbum.photos[i].completeName.substring(0, currentAlbum.photos[i].completeName.length - currentAlbum.photos[i].name.length - 1)) +
						"/" +
						PhotoFloat.cachePath(currentAlbum.photos[i].name);
				}
				//link = $("<a href=\"#!/" + photoFloat.photoHash(currentAlbum, currentAlbum.photos[i]) + "\"></a>");
				link = $("<a href=\"#!/" + hash + "\"></a>");
				//image = $("<img title=\"" + photoFloat.trimExtension(currentAlbum.photos[i].name) +
				//		"\" alt=\"" + photoFloat.trimExtension(currentAlbum.photos[i].name) +
				//		"\" src=\"" + photoFloat.photoPath(currentAlbum, currentAlbum.photos[i], 150, true) +
				//		"\" height=\"150\" width=\"150\" />");
				image = $("<div class=\"thumb-container\">" +
							"<img title=\"" + currentAlbum.photos[i].name +
							"\" alt=\"" + photoFloat.trimExtension(currentAlbum.photos[i].name) +
							"\" src=\"" + thumbHash +
							"\" height=\"150\" width=\"150\" />" +
							"<div class=\"thumb-caption\">" +
							currentAlbum.photos[i].name.replace(/ /g, "</span> <span style=\"white-space: nowrap;\">") +
							"</div>" +
							"</div>");
				if (currentAlbum.photos[i].mediaType == "video")
					image.css("background-image", "url(" + image.attr("src") + ")").attr("src", "img/video-icon.png");

				image.get(0).photo = currentAlbum.photos[i];
				link.append(image);
				photos.push(link);
				(function(theLink, theImage, theAlbum) {
					theImage.error(function() {
						photos.splice(photos.indexOf(theLink), 1);
						theLink.remove();
						theAlbum.photos.splice(theAlbum.photos.indexOf(theImage.get(0).photo), 1);
					});
				})(link, image, currentAlbum);
			}
			thumbsElement = $("#thumbs");
			thumbsElement.empty();
			thumbsElement.append.apply(thumbsElement, photos);
			
			if (currentPhoto === null) {
				subalbums = [];
				for (i = 0; i < currentAlbum.albums.length; ++i) {
					link = $("<a href=\"#!/" + photoFloat.albumHash(currentAlbum.albums[i]) + "\"></a>");
					var imageTextAdd = currentAlbum.albums[i].path;
					if (typeof bydateTranslation !== 'undefined')
						imageTextAdd = imageTextAdd.replace(bydateString, bydateTranslation);
					else
						imageTextAdd = imageTextAdd.replace(bydateString, bydateEnglishString);
					if (typeof foldersTranslation !== 'undefined')
						imageTextAdd = imageTextAdd.replace(foldersString, foldersTranslation);
					else
						imageTextAdd = imageTextAdd.replace(foldersString, foldersEnglishString);
					image = $("<div title=\"" + currentAlbum.albums[i].date + "\" class=\"album-button\">" +
								imageTextAdd +
								"</div>");
					link.append(image);
					subalbums.push(link);
					(function(theContainer, theAlbum, theImage, theLink) {
						photoFloat.albumPhoto(theAlbum, function(album, photo) {
							theImage.css("background-image", "url(" + photoFloat.photoPath(album, photo, 150, true) + ")");
						}, function error() {
							theContainer.albums.splice(currentAlbum.albums.indexOf(theAlbum), 1);
							theLink.remove();
							subalbums.splice(subalbums.indexOf(theLink), 1);

						});
					})(currentAlbum, currentAlbum.albums[i], image, link);
				}
				subalbumsElement = $("#subalbums");
				subalbumsElement.empty();
				subalbumsElement.append.apply(subalbumsElement, subalbums);
				subalbumsElement.insertBefore(thumbsElement);
			}
		}
		
		if (currentPhoto === null) {
			$("#thumbs img").removeClass("current-thumb");
			$("#album-view").removeClass("photo-view-container");
			$("#subalbums").show();
			$("#photo-view").hide();
			$("#video-box-inner").empty();
			$("#video-box").hide();
		}
		setTimeout(scrollToThumb, 1);
	}
	function getDecimal(fraction) {
		if (fraction[0] < fraction[1])
			return fraction[0] + "/" + fraction[1];
		return (fraction[0] / fraction[1]).toString();
	}
	function scaleImage() {
		var image, container;
		image = $("#photo");
		if (image.get(0) === this)
			$(window).bind("resize", scaleImage);
		container = $("#photo-view");
		if (image.css("width") !== "100%" && container.height() * image.attr("ratio") > container.width())
			image.css("width", "100%").css("height", "auto").css("position", "absolute").css("bottom", 0);
		else if (image.css("height") !== "100%")
			image.css("height", "100%").css("width", "auto").css("position", "").css("bottom", "");
	}
	function scaleVideo() {
		var video, container;
		video = $("#video");
		if (video.get(0) === this)
			$(window).bind("resize", scaleVideo);
		container = $("#photo-view");
		if (video.attr("width") > container.width() && container.height() * video.attr("ratio") > container.width())
			video.css("width", container.width()).css("height", container.width() / video.attr("ratio")).parent().css("height", container.width() / video.attr("ratio")).css("margin-top", - container.width() / video.attr("ratio") / 2).css("top", "50%");
		else if (video.attr("height") > container.height() && container.height() * video.attr("ratio") < container.width())
			video.css("height", container.height()).css("width", container.height() * video.attr("ratio")).parent().css("height", "100%").css("margin-top", "0").css("top", "0");
		else
			video.css("height", "").css("width", "").parent().css("height", video.attr("height")).css("margin-top", - video.attr("height") / 2).css("top", "50%");
	}
	function showPhoto() {
		var width, height, photoSrc, videoSrc, previousPhoto, nextPhoto, nextLink, text;
		width = currentPhoto.size[0];
		height = currentPhoto.size[1];

		if (currentPhoto.mediaType == "video") {
			$("#video-box-inner").empty();
			if (! Modernizr.video) {
				$('<div id="video-unsupported"><p>Sorry, your browser doesn\'t support the HTML5 &lt;video&gt; element!</p><p>Here\'s a <a href="http://caniuse.com/video">list of which browsers do</a>.</p></div>').appendTo('#video-box-inner');
			}
			else if (! Modernizr.video.h264) {
				$('<div id="video-unsupported"><p>Sorry, your browser doesn\'t support the H.264 video format!</p></div>').appendTo('#video-box-inner');
			} else {
				$(window).unbind("resize", scaleVideo);
				$(window).unbind("resize", scaleImage);
				videoSrc = photoFloat.videoPath(currentAlbum, currentPhoto);
				//console.log(videoSrc);
				$('<video/>', { id: 'video', controls: true }).appendTo('#video-box-inner')
					.attr("width", width).attr("height", height).attr("ratio", currentPhoto.size[0] / currentPhoto.size[1])
					.attr("src", videoSrc)
					.attr("alt", currentPhoto.name)
					.on('loadstart', scaleVideo);
			}
			$("head").append("<link rel=\"video_src\" href=\"" + videoSrc + "\" />");
			$("#video-box-inner").css('height', height + 'px').css('margin-top', - height / 2);
			$("#photo-box").hide();
			$("#video-box").show();
		} else {
			width = currentPhoto.size[0];
			height = currentPhoto.size[1];
			if (width > height) {
				height = height / width * maxSize;
				width = maxSize;
			} else {
				width = width / height * maxSize;
				height = maxSize;
			}
			$(window).unbind("resize", scaleVideo);
			$(window).unbind("resize", scaleImage);
			photoSrc = photoFloat.photoPath(currentAlbum, currentPhoto, maxSize, false);
			$("#photo")
				.attr("width", width).attr("height", height).attr("ratio", currentPhoto.size[0] / currentPhoto.size[1])
				.attr("src", photoSrc)
				.attr("alt", currentPhoto.name)
				.attr("title", currentPhoto.date)
				.load(scaleImage);
			$("head").append("<link rel=\"image_src\" href=\"" + photoSrc + "\" />");
			$("#video-box-inner").empty();
			$("#video-box").hide();
			$("#photo-box").show();
		}
		$(window).unbind("resize", scaleImage);
		photoSrc = photoFloat.photoPath(currentAlbum, currentPhoto, maxSize, false);
		$("#photo")
			.attr("width", width).attr("height", height).attr("ratio", currentPhoto.size[0] / currentPhoto.size[1])
			.attr("src", photoSrc)
			.attr("alt", currentPhoto.name)
			.attr("title", currentPhoto.date)
			.load(scaleImage);
		$("head").append("<link rel=\"image_src\" href=\"" + photoSrc + "\" />");
		previousPhoto = currentAlbum.photos[
			(currentPhotoIndex - 1 < 0) ? (currentAlbum.photos.length - 1) : (currentPhotoIndex - 1)
		];
		nextPhoto = currentAlbum.photos[
			(currentPhotoIndex + 1 >= currentAlbum.photos.length) ? 0 : (currentPhotoIndex + 1)
		];
		$.preloadImages(photoFloat.photoPath(currentAlbum, nextPhoto, maxSize, false),
						photoFloat.photoPath(currentAlbum, previousPhoto, maxSize, false));
		
		if (currentAlbum.path == photoFloat.photoFoldersAlbum(currentPhoto)) {
			$("#folders-view-container").hide();
			$("#day-view-container").hide();
			$("#month-view-container").show();
			$("#year-view-container").show();
		}
		else if (currentAlbum.path == photoFloat.photoMonthAlbum(currentPhoto)) {
			$("#folders-view-container").hide();
			$("#day-view-container").show();
			$("#month-view-container").hide();
			$("#year-view-container").show();
		}
		else if (currentAlbum.path == photoFloat.photoDayAlbum(currentPhoto)) {
			$("#folders-view-container").show();
			$("#day-view-container").hide();
			$("#month-view-container").hide();
			$("#year-view-container").show();
		}
		
		if (currentAlbum.path == photoFloat.photoYearAlbum(currentPhoto)) {
			//~ $("#folders-view-container").show();
			//~ $("#day-view-container").hide();
			//~ $("#month-view-container").hide();
			$("#year-view-container").hide();
		}
		
		nextLink = "#!/" + photoFloat.photoHash(currentAlbum, nextPhoto);
		$("#next-photo").attr("href", nextLink);
		$("#next").attr("href", nextLink);
		$("#back").attr("href", "#!/" + photoFloat.photoHash(currentAlbum, previousPhoto));
		$("#original-link").attr("target", "_blank").attr("href", photoFloat.originalPhotoPath(currentPhoto));
		$("#folders-view").attr("href", "#!/" + PhotoFloat.cachePath(currentPhoto.foldersAlbum) + "/" + PhotoFloat.cachePath(currentPhoto.name));
		$("#day-view").attr("href", "#!/" + PhotoFloat.cachePath(currentPhoto.dayAlbum) + "/" + PhotoFloat.cachePath(currentPhoto.name));
		$("#month-view").attr("href", "#!/" + PhotoFloat.cachePath(currentPhoto.monthAlbum) + "/" + PhotoFloat.cachePath(currentPhoto.name));
		$("#year-view").attr("href", "#!/" + PhotoFloat.cachePath(currentPhoto.yearAlbum) + "/" + PhotoFloat.cachePath(currentPhoto.name));
		
		text = "<table>";
		if (typeof currentPhoto.make !== "undefined") text += "<tr><td>Camera Maker</td><td>" + currentPhoto.make + "</td></tr>";
		if (typeof currentPhoto.model !== "undefined") text += "<tr><td>Camera Model</td><td>" + currentPhoto.model + "</td></tr>";
		if (typeof currentPhoto.date !== "undefined") text += "<tr><td>Time Taken</td><td>" + currentPhoto.date + "</td></tr>";
		if (typeof currentPhoto.size !== "undefined") text += "<tr><td>Resolution</td><td>" + currentPhoto.size[0] + " x " + currentPhoto.size[1] + "</td></tr>";
		if (typeof currentPhoto.aperture !== "undefined") text += "<tr><td>Aperture</td><td> f/" + getDecimal(currentPhoto.aperture) + "</td></tr>";
		if (typeof currentPhoto.focalLength !== "undefined") text += "<tr><td>Focal Length</td><td>" + getDecimal(currentPhoto.focalLength) + " mm</td></tr>";
		if (typeof currentPhoto.subjectDistanceRange !== "undefined") text += "<tr><td>Subject Distance Range</td><td>" + currentPhoto.subjectDistanceRange + "</td></tr>";
		if (typeof currentPhoto.iso !== "undefined") text += "<tr><td>ISO</td><td>" + currentPhoto.iso + "</td></tr>";
		if (typeof currentPhoto.sceneCaptureType !== "undefined") text += "<tr><td>Scene Capture Type</td><td>" + currentPhoto.sceneCaptureType + "</td></tr>";
		if (typeof currentPhoto.exposureTime !== "undefined") text += "<tr><td>Exposure Time</td><td>" + getDecimal(currentPhoto.exposureTime) + " sec</td></tr>";
		if (typeof currentPhoto.exposureProgram !== "undefined") text += "<tr><td>Exposure Program</td><td>" + currentPhoto.exposureProgram + "</td></tr>";
		if (typeof currentPhoto.exposureCompensation !== "undefined") text += "<tr><td>Exposure Compensation</td><td>" + getDecimal(currentPhoto.exposureCompensation) + "</td></tr>";
		if (typeof currentPhoto.spectralSensitivity !== "undefined") text += "<tr><td>Spectral Sensitivity</td><td>" + currentPhoto.spectralSensitivity + "</td></tr>";
		if (typeof currentPhoto.sensingMethod !== "undefined") text += "<tr><td>Sensing Method</td><td>" + currentPhoto.sensingMethod + "</td></tr>";
		if (typeof currentPhoto.lightSource !== "undefined") text += "<tr><td>Light Source</td><td>" + currentPhoto.lightSource + "</td></tr>";
		if (typeof currentPhoto.flash !== "undefined") text += "<tr><td>Flash</td><td>" + currentPhoto.flash + "</td></tr>";
		if (typeof currentPhoto.orientation !== "undefined") text += "<tr><td>Orientation</td><td>" + currentPhoto.orientation + "</td></tr>";
		text += "</table>";
		$("#metadata").html(text);
		
		$("#album-view").addClass("photo-view-container");
		$("#subalbums").hide();
		$("#photo-view").show();
		
		if (typeof showMetadataTranslation !== 'undefined')
			$("#metadata-link").html(showMetadataTranslation);
		if (typeof foldersViewTranslation !== 'undefined')
			$("#folders-view").html(foldersViewTranslation);
		if (typeof byDayTranslation !== 'undefined')
			$("#day-view").html(byDayTranslation);
		if (typeof byMonthTranslation !== 'undefined')
			$("#month-view").html(byMonthTranslation);
		if (typeof byYearTranslation !== 'undefined')
			$("#year-view").html(byYearTranslation);
		if (typeof donwloadOriginalTranslation !== 'undefined')
			$("#original-link").html(donwloadOriginalTranslation);
		if (typeof fullscreenTranslation !== 'undefined')
			$("#fullscreen").html(fullscreenTranslation);
	}
	
	
	/* Error displays */
	
	function die(error) {
		if (error == 403) {
			$("#auth-text").fadeIn(1000);
			$("#password").focus();
		} else
			$("#error-text").fadeIn(2500);
		$("#error-overlay").fadeTo(500, 0.8);
		$("body, html").css("overflow", "hidden");
	}
	function undie() {
		$("#error-text, #error-overlay, #auth-text").fadeOut(500);
		$("body, html").css("overflow", "auto");
	}
		
		
	
	/* Entry point for most events */
	
	function hashParsed(album, photo, photoIndex) {
		undie();
		$("#loading").hide();
		if (album === currentAlbum && photo === currentPhoto)
			return;
		if (album != currentAlbum)
			currentAlbum = null;
		if (currentAlbum && currentAlbum.path.indexOf(bydateString) === 0 && photo !== null) {
			previousAlbum = currentAlbum;
			album = currentAlbum;
			previousPhoto = photo;
			currentPhoto = photo;
			currentPhotoIndex = photoIndex;
		}
		else {
			previousAlbum = currentAlbum;
			previousPhoto = currentPhoto;
			currentAlbum = album;
			currentPhoto = photo;
			currentPhotoIndex = photoIndex;
		}
		setTitle();
		var populateAlbum = previousAlbum !== currentAlbum || previousPhoto !== currentPhoto;
		showAlbum(populateAlbum);
		if (photo !== null) {
			showPhoto();
		}
		if (typeof poweredByTranslation !== 'undefined')
			$("#powered-by-string").html(poweredByTranslation);
		if (typeof loadingTranslation !== 'undefined')
			$("#loading").html(loadingTranslation);
		if (typeof errorTextTranslation !== 'undefined')
			$("#error-text").html(errorTextTranslation);
	}
	
	/* Event listeners */
	
	$(window).hashchange(function() {
		$("#loading").show();
		$("link[rel=image_src]").remove();
		$("link[rel=video_src]").remove();
		photoFloat.parseHash(location.hash, hashParsed, die);
	});
	$(window).hashchange();
	$(document).keydown(function(e){
		if (currentPhoto === null)
			return true;
		if (e.keyCode === 39) {
			window.location.href = $("#next").attr("href");
			return false;
		} else if (e.keyCode === 37) {
			window.location.href = $("#back").attr("href");
			return false;
		}
		return true;
	});
	$(document).mousewheel(function(event, delta) {
		if (currentPhoto === null)
			return true;
		if (delta < 0) {
			window.location.href = $("#next").attr("href");
			return false;
		} else if (delta > 0) {
			window.location.href = $("#back").attr("href");
			return false;
		}
		return true;
	});
	$("#photo-box").mouseenter(function() {
		$("#photo-links").stop().fadeTo("slow", 0.50).css("display", "inline");
	});
	$("#photo-box").mouseleave(function() {
		$("#photo-links").stop().fadeOut("slow");
	});
	$("#next, #back").mouseenter(function() {
		$(this).stop().fadeTo("slow", 1);
	});
	$("#next, #back").mouseleave(function() {
		$(this).stop().fadeTo("slow", 0.35);
	});
	if ($.support.fullscreen) {
		$("#fullscreen-divider").show();
		$("#fullscreen").show().click(function() {
			$("#photo").fullScreen({callback: function(isFullscreen) {
				maxSize = isFullscreen ? 1600 : 1600;
				showPhoto();
			}});
		});
	}
	$("#metadata-link").click(function() {
		if (!$("#metadata").is(":visible"))
			$("#metadata").stop()
				.css("height", 0)
				.css("padding-top", 0)
				.css("padding-bottom", 0)
				.show()
				.animate({ height: $("#metadata > table").height(), paddingTop: 3, paddingBottom: 3 }, "slow", function() {
					$(this).css("height", "auto");
					$("#metadata-link").text($("#metadata-link").text().replace("show", "hide"));
				});
		else
			$("#metadata").stop().animate({ height: 0, paddingTop: 0, paddingBottom: 0 }, "slow", function() {
				$(this).hide();
				$("#metadata-link").text($("#metadata-link").text().replace("hide", "show"));
			});
	});
	$("#auth-form").submit(function() {
		var password = $("#password");
		password.css("background-color", "rgb(128, 128, 200)");
		photoFloat.authenticate(password.val(), function(success) {
			password.val("");
			if (success) {
				password.css("background-color", "rgb(200, 200, 200)");
				$(window).hashchange();
			} else
				password.css("background-color", "rgb(255, 64, 64)");
		});
		return false;
	});
});
