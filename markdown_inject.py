#!/usr/bin/env python
# -*- coding: utf-8 -*-
# some_file.py


import os
import sys
import re
import argparse
from pprint import pprint
import json
import codecs

# insert at 1, 0 is the script path (or '' in REPL)
sys.path.append("../mistletoe")

from mistletoe import Document
from contrib.latex_block_renderer import LaTeXBlockRenderer



class Crawler:
	def __init__(self):
		self.objs = {}

	def recreate_variables(self,variables, level):
		new_line_string=''
		if isinstance(variables,list):
			for value in variables:
				new_line_string+='\n'+'  '*level+'- '+self.recreate_variables(value,level +1)		
		elif isinstance(variables,dict):
			for key, value in variables.items():
				new_line_string+='\n'+'  '*level+'- '+key + self.recreate_variables(value,level +1)
		else: # a scalar lead
			return ' : '+ variables
		return new_line_string

	def inject_Lines(self, all_lines, variables):
		i = 0
		new_lines=[]
		name=None
		this_variables=None
		list_pattern = re.compile(r"^-\s*(\w+)")
		indent_pattern = re.compile(r"^\s+")
		value_pattern = re.compile(r'^-\s*\w+\s*:(.+)(\(.*\))*$')
		while i < len(all_lines):
			line = all_lines[i].rstrip()
			match = list_pattern.match(line)
			if match:
				print("found item", match.group(1))
				key_name = match.group(1).lower()
				if key_name=='name':
					name = None
					pattern_match = value_pattern.match(line)
					if pattern_match:
						name = pattern_match.group(1).strip().lower()

					if not name or  not name in variables:
						return all_lines
					else:
						this_variables=variables[name]
						# skip this line
						i += 1
				else:
					if key_name in this_variables['obj']: # do we have some data to fill in?
						# replace the contained variable with the data out of variables
						# so first we jump over each line which has any indent
						while i < len(all_lines):
							look_ahead_line=all_lines[i]
							if indent_pattern.match(look_ahead_line): # does the line have leading blanks?
								break
							i +=1
						new_lines += self.recreate_variables(this_variables['obj'][key_name],0).split('\n')

			else: # just continue
				new_lines.append(line)
				i += 1
		return new_lines

	def import_file(self, input_file_path, variables):
		with codecs.open(input_file_path, encoding='utf-8') as fin:
			with LaTeXBlockRenderer() as renderer:
				self.renderer = renderer
				all_Lines = fin.readlines()
				new_lines=self.inject_Lines(all_Lines, variables)
				document = Document(new_lines)
				latex_text = renderer.render(document)
				self.save(latex_text, input_file_path)

	def save(self, latex_text, input_file_path):
		path_only = os.path.dirname(input_file_path)
		basename_without_ext = os.path.splitext(os.path.basename(input_file_path))[0]
		output_file_path = os.path.join(path_only, basename_without_ext + ".texincl")

		try:
			with codecs.open(output_file_path, "w", encoding='utf-8') as fout:
				fout.write(latex_text)
		except Exception as ex:
			print(f"Error: Couldn' save result to {output_file_path} : {str(ex)}")

	def inject(self, dirs, variables):
		if isinstance(dirs, str):
			walk_dirs = [dirs]
		else:
			walk_dirs = dirs
		for walk_dir in walk_dirs:
			if os.path.isfile(walk_dir):
				self.import_file(walk_dir, variables)
				continue
			for root, subdirs, file_names in os.walk(walk_dir):
				directories_to_exclude = []
				for subdir in subdirs:
					pass
					dir_name = os.path.basename(subdir)
					if dir_name.lower() in args.exclude_dirs:  # do not read that
						directories_to_exclude.append(subdir)
						continue
				for excluded_dir in directories_to_exclude:
					subdirs.remove(excluded_dir)
				for file_name in file_names:
					if not file_name[-3:] == ".md":
						continue
					input_file_path = os.path.join(root, file_name)
					self.import_file(input_file_path, variables)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Reads Markdown files, injects variable into and save the result as latex files"
	)

	parser.add_argument(
		"-i",
		"--input",
		dest="input_paths",
		action="append",
		help="read from INPUT , can be file or directory",
		metavar="INPUT",
		required=True,
	)

	parser.add_argument(
		"-x",
		"--exclude",
		dest="exclude_dirs",
		action="append",
		default=[],
		help="exclude directories",
		metavar="INPUT",
		required=False,
	)

	parser.add_argument(
		"-v",
		"--variables",
		dest="variables",
		help="json file containing the data to inject",
		metavar="VARIABLES",
		required=True,
	)

	args = parser.parse_args()

	walk_dir = []

	# If your current working directory may change during script execution, it's recommended to
	# immediately convert program arguments to an absolute path.

	for path in args.input_paths:
		try:
			walk_dir.append(os.path.abspath(path.strip()))
		except:
			print(f"Error: {path} is no valid directory or file")

	print(walk_dir)
	try:
		f = open(args.variables)
		variables = json.load(f)
	except:
		print("Error: Variables file not readable")
		sys.exit(1)

	crawler = Crawler()
	crawler.inject(walk_dir, variables)
