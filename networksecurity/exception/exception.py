
"""Custom exception utilities for the project."""

import sys
import traceback


class CustomException(Exception):
	"""A small wrapper exception that captures file name and line number.

	The class accepts an `error_message` and optional `file_name` and
	`lineno`. If the location is not provided it will attempt to infer it
	from the current exception traceback.
	"""

	def __init__(self, error_message: Exception, file_name: str = None, lineno: int = None):
		super().__init__(error_message)
		self.error_message = error_message

		if file_name is None or lineno is None:
			tb = sys.exc_info()[2]
			if tb:
				last = traceback.extract_tb(tb)[-1]
				file_name = file_name or last.filename
				lineno = lineno or last.lineno

		self.file_name = file_name or "<unknown>"
		self.lineno = lineno or 0

	def __str__(self):
			return "Error occured in python script name [{0}] line number [{1}] error message [{2}]".format(
			self.file_name, self.lineno, str(self.error_message))

