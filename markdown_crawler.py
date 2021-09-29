#!/usr/bin/env python
# -*- coding: utf-8 -*-
# some_file.py
import os
import sys
import copy
import collections

# insert at 1, 0 is the script path (or '' in REPL)
sys.path.append('../mistletoe')

from mistletoe import Document
from contrib.mson import MSONRenderer

import sys

#walk_dir = sys.argv[1]
walk_dir = '..'
#walk_dir = '/home/steffen/PlayGround/markdown_crawler'

exclude_dirs=['mistletoe']

# If your current working directory may change during script execution, it's recommended to
# immediately convert program arguments to an absolute path. Then the variable root below will
# be an absolute path as well. Example:
walk_dir = os.path.abspath(walk_dir)


class Crawler:

	def __init__(self):
		self.objs={}

	def remove_scrap(self, md_objects):
		for file_path,file_obj in md_objects.items():
			list_items_to_delete=[]
			if isinstance(file_obj,list): # in case of a list we search for dicts with a name property
				for inner_obj in file_obj:
					if not isinstance(inner_obj,dict): # on the root level we search only for dicts
						list_items_to_delete.append(inner_obj) # remember to delete
					if isinstance(inner_obj,dict) and  not 'name' in inner_obj:
						list_items_to_delete.append(inner_obj) # remember to delete
			for del_obj in list_items_to_delete:
				file_obj.remove(del_obj) # clean up
			if not file_obj:
				print(f'Warning: {file_path} does not contain any object data' )

	def collect_objs_by_name(self, md_objects):
		for file_path,file_obj in md_objects.items():
			if not isinstance(file_obj, list) and not 'name' in file_obj:
				continue
			for obj in file_obj:
				obj_name_lower=obj['name'].lower()
				if obj_name_lower in self.objs:
					print('Error: object {0} in {1} is also already defined in {2}'.format(obj_name_lower, file_path, self.objs[obj_name_lower]['file_path']))
					continue
				parents=[]
				if not 'parent' in obj:
					parent_solved=True
				else:
					if obj['parent'] and not isinstance(obj['parent'],bool) :
						parent_solved=False
						if isinstance(obj['parent'],str):
							parents=obj['parent'].split()
						else:
							parents=obj['parent']
					else:
						parent_solved=True
				parents=list(map(lambda x: x.lower(), parents))
				self.objs[obj_name_lower]={'file_path':file_path,'obj':obj,'parent_solved':parent_solved, 'parents':parents}

	def inject_properties(self, source, target, source_file_path, target_file_path):
		'''
		tries to recursively copy all properties from source into target

		whereever senseful and possible, it combines single scalars into combined lists

		exception: when the target value is a scalar and starts with #, then only the target value is kept
		If the value is only #, then the property will be removed

		'''

		#print('inject',source['name'],'->', target['name'])
		# we go through all source properties
		for source_key, source_value in source.items():
			if str(source_key).lower()=='name': # don't touch the objects name :-)
				continue
			if not source_key in target: # that's easy: we only need to copy source to target
				target[source_key]=copy.deepcopy(source_value)
			else: # not easy: we need to apply different strategies depending on the value types
				target_value=target[source_key]
				if isinstance(target_value,str) and target_value[:1]=='#':
					# the '#' surpresses the source copy operation
					continue
				source_is_dict = isinstance(source_value,collections.Mapping)
				source_is_list = isinstance(source_value, list)
				source_is_scalar = not (source_is_dict or source_is_list)
				target_is_dict = isinstance(target_value,collections.Mapping)
				target_is_list = isinstance(target_value, list)
				target_is_scalar = not (target_is_dict or target_is_list)

				# ok, let's go through all combinations..
				if source_is_scalar:
					if target_is_scalar:
						target[source_key]=[source_value,target_value]
					if target_is_dict:
						target_value.append(source_value)
					if target_is_list:
						target_value[source_value] = True # make a boolean flag out of it..
				if source_is_dict:
					if target_is_scalar:
						target[source_key]=copy.deepcopy(source_value)
						target[source_key][target_value] = True # make a boolean flag out of it..
					if target_is_dict:
						self.inject_properties(source_value,target_value, source_file_path, target_file_path)
					if target_is_list:
						print('Error: Can\'t join property {0} from {1} into {2} :different data type hash -> list'.format(source_key, source_file_path, target_file_path))
				if source_is_list:
					if target_is_scalar:
						target[source_key]=copy.deepcopy(source_value)
						target[source_key].append(target_value) # make a common list out of it..
					if target_is_dict:
						print('Error: Can\'t join property {0} from {1} into {2} :different data type list -> hash'.format(source_key, source_file_path, target_file_path))
					if target_is_list:
						target_value.extend(copy.deepcopy(source_value))



	def copy_parents(self):
		something_has_changed= True
		while something_has_changed:
			something_has_changed= False
			for obj_name, obj_header in self.objs.items():
				if obj_header['parent_solved']:
					continue # already done
				parent_solved= True
				for parent in obj_header['parents']:
					if not parent in self.objs:
						print('Error: object {0} in {1} requests unknown parent {2}'.format(obj_name, obj_header['file_path'], parent))
						continue
					if not self.objs[parent]['parent_solved']:
						parent_solved= False
						break
				if parent_solved: # all parents are solved, so we can fill this
					something_has_changed = True # allow another loop
					for parent in obj_header['parents']:
						obj_header['parent_solved']=True
						print(f'fill {obj_name} with {parent} ')
						self.inject_properties(self.objs[parent]['obj'],obj_header['obj'],self.objs[parent]['file_path'],obj_header['file_path'])

	



	def crawl(self, dirs):
		if isinstance(dirs,str):
			walk_dirs=[dirs]
		else:
			walk_dirs=dirs
		md_objects={}
		for walk_dir in walk_dirs:
			for root, subdirs, files in os.walk(walk_dir):
				for ext_dir_name in exclude_dirs:
					print('exclude',ext_dir_name, root)
					if ext_dir_name in root:
						print('abbruch')
						break
				else: # crazy python: you can have an 'else' as end of the previous for loop!
					for subdir in subdirs:
						pass
					for filename in files:
						if not filename[-3:]=='.md':
							continue
						file_path = os.path.join(root, filename)
						with open(file_path, 'r') as fin:
							print('file_path',file_path)
							with MSONRenderer() as renderer:
								rendered = renderer.render(Document(fin))
								md_objects[file_path]=rendered
		self.remove_scrap(md_objects)
		self.collect_objs_by_name(md_objects)
		self.copy_parents()
		return md_objects

if __name__=='__main__':
	crawler=Crawler()
	md_objects=crawler.crawl(walk_dir)

	print(md_objects)