#!/usr/bin/env python
# -*- coding: utf-8 -*-
# some_file.py
import os
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.append('../mistletoe')

from mistletoe import Document
from contrib.mson import MSONRenderer

import sys

#walk_dir = sys.argv[1]
walk_dir = '/home/steffen/PlayGround/markdown_crawler'


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

	



	def crawl(self, dirs):
		if isinstance(dirs,str):
			walk_dirs=[dirs]
		else:
			walk_dirs=dirs
		md_objects={}
		for walk_dir in walk_dirs:
			for root, subdirs, files in os.walk(walk_dir):
				for subdir in subdirs:
					pass
				for filename in files:
					if not filename[-3:]=='.md':
						continue
					file_path = os.path.join(root, filename)
					with open(file_path, 'r') as fin:
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