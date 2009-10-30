#!/usr/bin/env python
# encoding: utf-8
"""
imagepartitioner.py

Created by Ryan Matthew Balfanz on 2009-07-18.
Copyright (c) 2009 Ryan Matthew Balfanz. All rights reserved.
"""


import logging
import os
import optparse
import sys

import Image


class ImagePartitioner(object):
	"""A class used to partition images into rectangular regions, optionally overlapping.
	
	Partitions are defined by a 4-tuple, where coordinates are (left, upper, right, lower).
	Overlaps are defined by a 2-tuple, where coordinates are (width, height).
	"""
	
	def __init__(self, partSize, overlapSize=None, log=None):
		super(ImagePartitioner, self).__init__()
		self.partSize = partSize
		
		if not overlapSize:
			overlapSize = (0, 0)
		self.overlapSize = overlapSize
		
		self.log = log
		if log:
			self._init_logging()
			
	def _init_logging(self):
		"""docstring for init_logging"""
		# Set the message format.
		format = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")

		# Create the message handler.
		stderr_hand = logging.StreamHandler(sys.stderr)
		stderr_hand.setLevel(logging.INFO)
		stderr_hand.setFormatter(format)

		# Create a handler for routing to a file.
		logfile_hand = logging.FileHandler(self.log + '.log')
		logfile_hand.setLevel(logging.DEBUG)
		logfile_hand.setFormatter(format)

		# Create a top-level logger.
		self.log = logging.getLogger(self.log)
		self.log.setLevel(logging.DEBUG)
		self.log.addHandler(logfile_hand)
		self.log.addHandler(stderr_hand)
		
		self.log.debug('Initializing logger')
		
	@property
	def size(self):
		"""Return the size of the partitions."""
		return self.partSize
		
	@property
	def overlap(self):
		"""Return the size of the overlaps."""
		return self.overlapSize
		
	@property
	def logname(self):
		"""Return the log identifier."""
		return self.log.name
		
	def validate_box_size_against_image_size(self, imgSize):
		"""Verify the box size relative to the image size."""
		if self.log: self.log.debug('Validating box size against image size')
		
		if self.partSize[0] > imgSize[0]:
			errorMessage = "Image width (%d) must exceed box width (%d)" % (imgSize[0], self.partSize[0])
			if self.log: self.log.error(errorMessage)
			raise ValueError, errorMessage
		if self.partSize[1] > imgSize[0]:
			errorMessage = "Image height (%d) must exceed box height (%d)" % (imgSize[1], self.partSize[1])
			if self.log: self.log.error(errorMessage)
			raise ValueError, errorMessage
			
	def validate_overlap_size_against_box_size(self, boxSize):
		"""Verify the overlap size relative to box size."""
		if self.log: self.log.debug('Validating overlap size against box size')
		
		if self.overlapSize[0] >= boxSize[0]:
			errorMessage = "Overlap width (%d) must exceed box width (%d)" % (self.overlapSize[0], boxSize[0])
			if self.log: self.log.error(errorMessage)
			raise ValueError, errorMessage
		if self.overlapSize[1] >= boxSize[1]:
			errorMessage = "Overlap height (%d) must not exceed overlap height (%d)" % (self.overlapSize[1], boxSize[1])
			if self.log: self.log.error(errorMessage)
			raise ValueError, errorMessage
		
	def get_boxes(self, imgSize, boxSize, overlap, overhang):
		"""Return the box of each partition."""
		if self.log: self.log.debug('Generating boxes')
		
		if overhang: raise NotImplementedError
		
		imageWidth, imageHeight = imgSize[0], imgSize[1]
		boxWidth, boxHeight = boxSize[0], boxSize[1]
		overlapWidth, overlapHeight = overlap[0], overlap[1]
		
		# Validate conditions.
		self.validate_box_size_against_image_size(imgSize)
		self.validate_overlap_size_against_box_size(boxSize)
		
		# Setup the first box.
		row, col = 0, 0
		left, upper = 0, 0
		right, lower = boxSize[0], boxSize[1]
		box = (left, upper, right, lower)

		# Calculate the box translation offsets.
		widthOffset = boxWidth - overlapWidth
		heightOffset = boxHeight - overlapHeight
		
		# Generate the boxes.
		while upper < imageHeight:
			while left < imageWidth:
				# Trim the box if it exceeds the image size.
				if right > imageWidth:
					if self.log: self.log.debug("box (r%dc%d) exceeds image width, trimming" % (row, col))
					right = imageWidth
				if lower > imageHeight:
					if self.log: self.log.debug("box (r%dc%d) exceeds image height, trimming" % (row, col))
					lower = imageHeight
				# Do a few sanity checks.
				# TODO: Should these be if statements? To not raise an exception?
				assert 0 <= left
				assert 0 <= upper
				assert left < right
				assert upper < lower
				if self.log: self.log.debug("Box at row %d column %d is %s" % (row, col, (left, upper, right, lower)))
				yield  (left, upper, right, lower), row, col
				left = left + widthOffset
				right = right + widthOffset
				col = col + 1
			left, right = 0, boxSize[0]
			row, col = row + 1, 0
			upper, lower = upper + heightOffset, lower + heightOffset
		
	def get_partitions(self, source, overhang):
		"""Generate the image partitions."""
		if self.log: self.log.info("Partitioning '%s'" % (source))

		im = None
		if isinstance(source, Image.Image):
			im = source
		else:
			try:
				im = Image.open(source, 'r')
			except IOError, e:
				# TODO: e may include a ':', which is the delimiter of the log files!
				if self.log: self.log.error('Could not open %s %s' % (filename, e))

		if im:
			for i, (box, row, col) in enumerate(self.get_boxes(im.size, self.partSize, self.overlapSize, overhang)):
				if self.log: self.log.debug('Cropping row %d col %d' % (row, col))
				yield im.crop(box), row, col
		else:
			raise StopIteration
		
		if self.log: self.log.info("Sliced and diced '%s' into %d partitions" % (source, i+1))
		
	
if __name__ == '__main__':
	parser = optparse.OptionParser()
	parser.set_defaults(overwidth=0)
	parser.set_defaults(overheight=0)
	parser.add_option("--width", type="int", dest="width")
	parser.add_option("--height", type="int", dest="height")
	parser.add_option("--owidth", type="int", dest="overwidth")
	parser.add_option("--oheight", type="int", dest="overheight")

	(options, args) = parser.parse_args()
	#(options, args) = parser.parse_args("--width 256 --height 256 rb.jpg .".split())

	pSize = (options.width, options.height)
	oSize = (options.overwidth, options.overheight)
	ip = ImagePartitioner(partSize=pSize, overlapSize=oSize)
	
	outDir = os.path.abspath(args[-1])
	for inpFile in args[:-1]:
		img = Image.open(inpFile)
		for i, (part, r, c) in enumerate(ip.get_partitions(source=img, overhang=None)):
			root, ext = os.path.splitext(inpFile)
			outParams = {"basename": root, 
				"row": r, "col": c, 
				"extension": ext}
			outFile = '%(basename)s_r%(row)dc%(col)d%(extension)s' % outParams
			outFilePath = os.path.join(outDir, outFile)
			part.save(outFilePath)
			