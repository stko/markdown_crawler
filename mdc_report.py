#!/usr/bin/env python
# -*- coding: utf-8 -*-
# some_file.py


import os
import sys
import argparse
from pprint import pprint
import json
from pythonintext import PIH



class Reporter:

	def __init__(self,input_file_path,base_output_file_path=None):
		'''
		if base_output_file_path == None, then the folder of the report template is choosen as 
		'''
		self.objs={}
		if base_output_file_path:
			self.base_output_file_path=base_output_file_path
		else:
			self.base_output_file_path=os.path.dirname(input_file_path)
		self.outputpathmask=''
		self.outputvars=''
		self.output_file_handles={}
		try:
			with open(input_file_path,encoding='utf8') as json_file:
				try:
					self.objs = json.load(json_file)
				except Exception as ex:
					print(f'ERROR: No valid json in {input_file_path}, program terminating',str(ex))
		except Exception as ex:
			print(f'ERROR: json file not found: {input_file_path}, program terminating',str(ex))

	def is_safe_path(self,basedir, path, follow_symlinks=True):
		# resolves symbolic links
		if follow_symlinks:
			matchpath = os.path.realpath(path)
			basepath = os.path.realpath(basedir)
		else:
			matchpath = os.path.abspath(path)
			basepath = os.path.abspath(basedir)
		return basepath == os.path.commonpath((basepath, matchpath))


	def write(self,text, vars):
		sys.stdout.write(text)
		calculated_file_path=self.outputpathmask
		for i in range(len(vars)):
			searchfor="$"+str(int(i+1))
			calculated_file_path=calculated_file_path.replace(searchfor,vars[i])
		output_file_path=os.path.join(self.base_output_file_path,calculated_file_path)
		'''if not self.is_safe_path(self.base_output_file_path,output_file_path):
			print("Error: calculated output path {0} is OUTSIDE the base dir {1}".format(output_file_path,self.base_output_file_path))
			return'''
		if  os.path.isdir(output_file_path):
			print("Error: calculated output path {0} is an existing directory!".format(output_file_path))
			return
			
		#print('calculated path:',output_file_path)
		# do we have that file stream already?
		if output_file_path in self.output_file_handles:
			fh=self.output_file_handles[output_file_path]
		else:
			#create dir, if not
			os.makedirs(os.path.dirname(output_file_path),exist_ok=True)
			fh=open(output_file_path,'w',encoding='utf8')
			self.output_file_handles[output_file_path]=fh
		fh.write(text)

	def close_handles(self):
		for fh in self.output_file_handles:
			try:
				fh.close()
			except:
				pass
		self.output_file_handles={}
 

	def import_file(self, file_path):
		this_options={}
		with open(file_path, 'r',encoding='utf8') as fin:
			# if there is no fixed root base output directory given, then we use the folder of where the template is stored in
			if not root_dir_path:
				self.base_output_file_path=os.path.dirname(file_path)
			self.outputpathmask=''
			self.outputvars=''
			line=fin.readline().strip()
			read_header=True
			while line != None and read_header:
				print(file_path, line)
				if line:
					if  not line[:1] == '#': #ignore comments
						try:
							elements=line.split(':',2)
							key=elements[0]
							value=elements[1]
							this_options[key]=value
							if key == 'outputpathmask':
								self.outputpathmask=value
							if key == 'outputvars':
								self.outputvars=value
						except:
							pass
					line=fin.readline().strip()
				else:
					read_header=False
			
			remaining_content=fin.read()
			print(remaining_content)
			py_code_output_stream=self
			pih=PIH(remaining_content,self.outputvars)
			pythonCode=pih.pythonCode()
			source_lines=pythonCode.split('\n')
			for i in range(len(source_lines)):
				print(f'{i}:{source_lines[i]}')
			try:
				exec (pythonCode)
			except Exception as ex:
				print('Exception:',str(ex))
			self.close_handles()


	def save(self, file_path):
		try:
			with open(file_path, 'w',encoding='utf8') as fout:
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
				continue
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
	parser = argparse.ArgumentParser(description='Creates output (reports) out of a json database and PIH report templates')

	parser.add_argument("-i", "--input", dest="input_filename",
					help="read json input from INPUT", metavar="INPUT", required=True)

	parser.add_argument("-r", "--rootoutputdir", dest="root_dir", default= None,
					help="root dir ROOT where all reports should be stored below", metavar="ROOT", required=False)

	parser.add_argument("-d", "--directory", dest="input_paths", action='append',
					help="search for report templates in DIR , can be file or directory", metavar="DIR", required=True)

	args = parser.parse_args()
	walk_dir = []


	for path in args.input_paths:
		# the strip() is nessary as for what ever reasons the parameter do get a leading " " (??? :-|)
		try:
			walk_dir.append(os.path.abspath(path.strip()))
		except:
			print(f'Error: {path} is no valid directory or file')

	input_file_path=os.path.abspath(args.input_filename.strip())
	if args.root_dir:
		root_dir_path=os.path.abspath(args.root_dir.strip())
	else:
		root_dir_path=None


	reporter = Reporter(input_file_path,args.root_dir)
	if not reporter.objs:
		parser.error('No input data')
	md_objects = reporter.scan_for_reports(walk_dir)

	# print(md_objects)
	#pprint(reporter.objs)

