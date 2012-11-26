#!/usr/bin/python
#
# A simple script to check a python file or project path
# to see which modules it is importing
#
# 

import re
import argparse
import os
import os.path
import sys
from operator import itemgetter

import_pe = [
	re.compile('^\s*from (\S+) import'),
	re.compile('^\s*import (\S+) as \w+'),
	re.compile('^\s*import (.+)')
]

def extract_modules(filename):
	mods = set()
	with open(filename) as f:
		for line in f:
			if 'import' not in line:
				continue
			for pe in import_pe:
				m = pe.search(line)
				if m:
					match = m.groups()[0].rstrip()
					# fix for when someone imports multiple modules on one line
					mods.update(re.split(',\s*', match))
					break
	return mods	


def walk_files(paths):
	modules = set()
	for path in paths:
		if os.path.isfile(path):
			modules.update(extract_modules(path))
		elif os.path.isdir(path):
			for root, dirs, files in os.walk(path):
				dirs[:] = [d for d in dirs if not path_excludes.match(d)]
				files = [ f for f in files if f.endswith('.py') and not file_excludes.match(f)]
				for f in files:
					modules.update(extract_modules(os.path.join(root,f)))
	return modules
	
def import_test(modules):

	# TODO - include list for standard library modules.  seeminly not a simple task
	
	project_modules={
		'available':[],
		'notfound':[],
		'builtin':[]
	}
	
	for m in modules:
		if m in sys.builtin_module_names:
			project_modules['builtin'].append(m)
			continue

		try:
			module = __import__(m)
		except Excption as err:
			project_modules['notfound'].append("%s (%s)" % (m,err))
			continue
	
		try:
			ver = module.__version__
			if not ver:
				ver = module.version
		except:
			ver = "n/a"
		try:
			f = os.path.dirname(module.__file__)
		except:
			f = ''
	
		project_modules['available'].append((m,ver,f))
	return project_modules

def extended_output(project_modules,verbose=False,summary=False):

	if summary:
		verbose = False

	if verbose:
		print "===== System Paths ====="
		for i in sorted(sys.path):
			print i
		print
	
	print "===== Built-in Modules ====="
	for b in sorted(project_modules['builtin']):
		print b
	print
	
	print "===== Available Modules ====="
	if summary:
		for m,v,f in sorted(project_modules['available'],key=itemgetter(0)):
			print m
	else:
		print "%-30s %-10s %s" % ('Module','Version','Path')
		print '-'*60
		for m,v,f in sorted(project_modules['available'],key=itemgetter(2,0)):
			print "%-30s %-10s %s" % (m,v,f)
	print
		
	print "===== Unable to Import ====="
	for i in sorted(project_modules['notfound']):
		print i
	print

def main(args):
	modules = walk_files(args.paths)
	if not modules:
		print "No modules found"
		exit()
	if args.importtest:
		project_modules = import_test(modules)
		extended_output(project_modules,args.verbose)
	else:
		for m in sorted(modules):
			print m

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Find all python modules used in a project')
	parser.add_argument('paths', metavar='PATH|FILE', type=str, nargs='+', 
						help='path to project')
	parser.add_argument('--verbose','-v', dest='verbose', action='store_true', default=False)
	parser.add_argument('--import-test','-t', dest='importtest', action='store_true', default=False,
						help='attempt to import each modules. Output will print version and path of each module')
	parser.add_argument('--exclude-file', dest='exclude_file', type=str, action='append', default=[],
						help='regex for filename to exclude.  Use multiple times for different regexes')
	parser.add_argument('--exclude-path', dest='exclude_path', type=str, action='append', default=[],
						help='regex for path to exclude.  Use multiple times for different regexes')
	args = parser.parse_args()
	
	def_path_excludes = '\.(git|svn)'
	args.exclude_path.append(def_path_excludes)
	path_excludes = re.compile(r'|'.join(args.exclude_path))
	file_excludes = re.compile(r'|'.join(args.exclude_file) or r'$.')
	
	main(args)

