#!/usr/bin/env python
# -*- coding: utf-8 -*-
# some_file.py


import os
import sys
import argparse
from pprint import pprint
import json
import copy

from mistletoe import Document
from contrib.mson import MSONRenderer


class Crawler:

    def __init__(self, verbose=False):
        self.objs = {}
        self.verbose = verbose

    def print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def remove_scrap(self, md_objects):
        for file_path, file_obj in md_objects.items():
            list_items_to_delete = []
            # in case of a list we search for dicts with a name property
            if isinstance(file_obj, list):
                for inner_obj in file_obj:
                    # on the root level we search only for dicts
                    if not isinstance(inner_obj, dict):
                        list_items_to_delete.append(
                            inner_obj)  # remember to delete
                    if isinstance(inner_obj, dict) and not 'name' in inner_obj:
                        list_items_to_delete.append(
                            inner_obj)  # remember to delete
            for del_obj in list_items_to_delete:
                file_obj.remove(del_obj)  # clean up
            if not file_obj:
                self.print(f'Warning: {file_path} does not contain any object data')

    def collect_objs_by_name(self, md_objects):
        for file_path, file_obj in md_objects.items():
            if file_obj==None or (not isinstance(file_obj, list) and not 'name' in file_obj):
                continue
            for obj in file_obj:
                if not isinstance(obj, list) and not 'name' in obj:
                    continue
                try:
                    obj_name_lower = obj['name'].lower()
                except Exception as ex:
                    print("exception", str(ex), "in", obj['name'])
                    sys.exit(0)
                parents = []
                if not 'parent' in obj:
                    parent_solved = True
                else:
                    if obj['parent'] and not isinstance(obj['parent'], bool):
                        parent_solved = False
                        if isinstance(obj['parent'], str):
                            parents = obj['parent'].split()
                        else:
                            parents = obj['parent']
                    else:
                        parent_solved = True
                parents = list(map(lambda x: x.lower(), parents))
                if obj_name_lower in self.objs:  # the object is already descripted in another file
                    other_objs = self.objs[obj_name_lower]
                    other_objs['file_path'].append(file_path)
                    self.renderer.inject_properties(
                        obj, other_objs['obj'], file_path, other_objs['file_path'][0])
                    other_objs['parent_solved'] = other_objs['parent_solved'] and parent_solved
                    other_objs['parents'] += parents
                else:
                    self.objs[obj_name_lower] = {'file_path': [
                        file_path], 'obj': obj, 'parent_solved': parent_solved, 'parents': parents}

    def copy_parents(self):
        something_has_changed = True
        while something_has_changed:
            something_has_changed = False
            for obj_name, obj_header in self.objs.items():
                if obj_header['parent_solved']:
                    continue  # already done
                parent_solved = True
                for parent in obj_header['parents']:
                    if not parent in self.objs:
                        self.print('Error: object {0} in {1} requests unknown parent {2}'.format(
                            obj_name, obj_header['file_path'], parent))
                        continue
                    if not self.objs[parent]['parent_solved']:
                        parent_solved = False
                        break
                if parent_solved:  # all parents are solved, so we can fill this
                    something_has_changed = True  # allow another loop
                    for parent in obj_header['parents']:
                        obj_header['parent_solved'] = True
                        try:
                            self.renderer.inject_properties(
                                self.objs[parent]['obj'], obj_header['obj'], self.objs[parent]['file_path'], obj_header['file_path'])
                            self.print(f'fill {obj_name} with {parent} ')
                        except KeyError as e:
                            self.print(
                                f'Error: {parent} is refenced in {obj_name}, but does not exist')

    def import_file(self, file_path):
        with open(file_path, 'r', encoding="utf-8") as fin:
            with MSONRenderer() as renderer:
                self.renderer = renderer
                rendered = renderer.render(Document(fin))
                return rendered

    def import_json_file(self, file_path):
        try:
            with open(file_path, 'r', encoding="utf-8") as fin:
                return [json.load(fin)]
        except Exception as ex:
            print(f"Error: Couldn't load {file_path}: {str(ex)}")

    def save(self, output_file):
        try:
            if isinstance(output_file, str):
                file_path = os.path.abspath(output_file.strip())
                with open(file_path, 'w') as fout:
                    json.dump(self.objs, fout, indent=4, sort_keys=True)
            else:  # its a filesystem object, hopefully...
                file_path = output_file.path
                with output_file.open('w') as fout:
                    json.dump(self.objs, fout, indent=4, sort_keys=True)
        except Exception as ex:
            self.print(f'Error: Couldn\' save result to {file_path} : {str(ex)}')

    def get(self):
        '''
        returns a copy of the found object
        '''
        return copy.deepcopy(self.objs)

    def crawl(self, dirs, exclude_dirs=[]):
        if isinstance(dirs, str):
            walk_dirs = [os.path.abspath(dirs.strip())]
        else:
            walk_dirs = []
            for path in dirs:
                try:
                    walk_dirs.append(os.path.abspath(path.strip()))
                except:
                    self.print(f'Error: {path} is no valid directory or file')
        md_objects = {}
        for walk_dir in walk_dirs:
            if os.path.isfile(walk_dir):
                md_objects[walk_dir] = self.import_file(walk_dir)
                continue
            for root, subdirs, files in os.walk(walk_dir):
                directories_to_exclude = []
                for subdir in subdirs:
                    pass
                    dir_name = os.path.basename(subdir)
                    if dir_name.lower() in exclude_dirs:  # do not read that
                        directories_to_exclude.append(subdir)
                        continue
                for excluded_dir in directories_to_exclude:
                    subdirs.remove(excluded_dir)
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if filename[-3:] == '.md':
                        self.print(f'actual md File: {file_path}')
                        md_objects[file_path] = self.import_file(file_path)
                    if filename[-3:] == '.jd':
                        self.print(f'actual jd File: {file_path}')
                        md_objects[file_path] = self.import_json_file(file_path)
        self.remove_scrap(md_objects)
        self.collect_objs_by_name(md_objects)
        self.copy_parents()
        return md_objects


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Converts markdown files in directories into one json structure')
    parser.add_argument("-o", "--output", dest="output_filename",
                        help="write json output to OUTPUT", metavar="OUTPUT", default="mdcrawler_result.json")

    parser.add_argument("-i", "--input", dest="input_paths", action='append',
                        help="read from INPUT , can be file or directory", metavar="INPUT", required=True)

    parser.add_argument("-x", "--exclude", dest="exclude_dirs", action='append', default=[],
                        help="exclude directories", metavar="INPUT", required=False)

    args = parser.parse_args()
    crawler = Crawler(True)
    md_objects = crawler.crawl(args.input_paths, args.exclude_dirs)

    # print(md_objects)
    pprint(crawler.objs)
    crawler.save(args.output_filename)
