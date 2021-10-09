#!/usr/bin/env python
# -*- coding: utf-8 -*-
# some_file.py


import os
import sys
import argparse
from pprint import pprint
import json
from pythonintext import PIH

parser = argparse.ArgumentParser(description='Creates output (reports) out of a json database and PIH report templates')

parser.add_argument("-i", "--input", dest="input_filename",
				  help="read json input from INPUT", metavar="INPUT", required=True)

parser.add_argument("-d", "--directory", dest="input_paths", action='append',
				  help="search for report templates in DIR , can be file or directory", metavar="DIR", required=True)

args = parser.parse_args()

walk_dir = []


# If your current working directory may change during script execution, it's recommended to
# immediately convert program arguments to an absolute path. Then the variable root below will
# be an absolute path as well. Example:

for path in args.input_paths:
	try:
		walk_dir.append(os.path.abspath(path.strip()))
	except:
		print(f'Error: {path} is no valid directory or file')

input_file_path=os.path.abspath(args.input_filename.strip())

class Reporter:

	def __init__(self,input_file_path):
		self.objs={}
		with open(input_file_path) as json_file:
			try:
				self.objs = json.load(json_file)
			except Exception as ex:
				print(f'ERROR: No valid json in {input_file_path}, program terminating',str(ex))
		


	def import_file(self, file_path):
		this_options=[]
		with open(file_path, 'r') as fin:
			line=fin.readline()
			read_header=True
			while line != None and read_header:
				print(file_path, line)
				line=fin.readline().strip()
				if line:
					try:
						key,value=line.split(':',2)
						this_options[key]=value
					except:
						pass
				else:
					read_header=False
			remaining_content=fin.read()
			print(remaining_content)
			py_code_output_stream=sys.stdout
			pih=PIH(remaining_content)
			pythonCode=pih.pythonCode()
			print(pythonCode)
			try:
				exec (pythonCode)
			except Exception as ex:
				print('Exception:',str(ex))


	def save(self, file_path):
		try:
			with open(file_path, 'w') as fout:
				json.dump(self.objs, fout)
		except Exception as ex:
			print(f'Error: Couldn\' save result to {file_path} : {str(ex)}')


	def scan_for_reports(self, dirs):
		if isinstance(dirs, str):
			walk_dirs = [dirs]
		else:
			walk_dirs = dirs
		md_objects = {}
		for walk_dir in walk_dirs:
			if os.path.isfile(walk_dir):
				md_objects[walk_dir] = self.import_file(walk_dir)
			for root, subdirs, files in os.walk(walk_dir):
				for subdir in subdirs:
					pass
				for filename in files:
					if not filename[-6:] == '.mdrep':
						continue
					file_path = os.path.join(root, filename)
					md_objects[file_path] = self.import_file(file_path)

		return md_objects


if __name__ == '__main__':
	reporter = Reporter(input_file_path)
	if not reporter.objs:
		parser.error()
	md_objects = reporter.scan_for_reports(walk_dir)

	# print(md_objects)
	#pprint(reporter.objs)

