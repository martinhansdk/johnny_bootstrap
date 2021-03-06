#!/usr/bin/python
import argparse
import codecs
import datetime
import os.path
import re
import shutil
import string
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "PyOrgMode"))

from PyOrgMode import PyOrgMode

# work around issues with output encoding in the Windows terminal
if sys.stdout.encoding != 'UTF-8':
  sys.stdout = codecs.getwriter('UTF-8')(sys.stdout, 'strict')
if sys.stderr.encoding != 'UTF-8':
  sys.stderr = codecs.getwriter('UTF-8')(sys.stderr, 'strict')

parser = argparse.ArgumentParser(description='Process an org mode for Johnny Decimal organization of files.')
parser.add_argument('file', help='the source file to process')
parser.add_argument('--minimum-groupspace', action='store', default=10, type=int, help='The minimum number of unallocated subgroups must be at least this many to allow for future additions. Default: %(default)s')
parser.add_argument('--copy', action='store_true', default=False, help='do the copying')
parser.add_argument('--no-dry-run', action='store_true', default=False, help='actually do the copying')
parser.add_argument('--force', action='store_true', default=False, help='copy files in spite of warnings')

args = parser.parse_args()


warnings=0
def warn(msg):
  global warnings
  warnings += 1
  print "WARNING: %s" % msg


# calculate the group, subgroup, folder vars from the category as
# shown in the testcases array

#           input                        output
testcases=[("group/subgroup/folder",   ( "group", "subgroup", "folder")),
           ("//folder",                ( "",      "",         "folder")),
           ("group",                   ( "group", "",         "")),
           ("",                        ( "",      "",         "")),
           ("group/subgroup",          ( "group", "subgroup", "")) ]

category_re = re.compile(r'(?P<group>[^/]*)/?(?P<subgroup>[^/]*)/?(?P<folder>[^/]*)')            
def parse_category(category):
    mo = category_re.match(category)

    return mo.group("group", "subgroup", "folder")

# from https://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if os.path.exists(d):
                raise Exception("File already exists, can't copy %s -> %s" % (s, d))
            else:
                shutil.copy2(s, d)

# 
# for input, expected in testcases:
#     actual = parse_category(input)
# 
#     if expected == actual:
#         print "OK ",
#     else:
#         print "NOK",
#     print "  %s -> %s" % (repr(input), repr(actual))
# 
doc = PyOrgMode.OrgDataStructure()
doc.load_from_file(args.file)

def find_elements(element, typ):
    results=[] 
    
    if isinstance(element, typ):
        results.append(element)
    
    if isinstance(element, PyOrgMode.OrgElement):
        for element in element.content:
            results.extend(find_elements(element, typ))

    return results

date_re = re.compile(r'\[(\d{4})-(\d{2})-(\d{2})\]')
year_re = re.compile(r'((19[789]\d)|(20[01]\d))')

def get_timestamp_from_string(s, default):
    mo = year_re.search(s)
    if mo:
        return datetime.datetime(year=int(mo.group(1)), month=1, day=1)
    else:
        return default

def get_timestamp(category, filename, default):
    timestamp=default
    clean_category=category
    timestamp_specifier=''

    mo1 = date_re.search(category)
    mo2 = year_re.search(category)
    mo3 = year_re.search(filename)        
    if mo1:
        timestamp = datetime.datetime(year=int(mo1.group(1)), month=int(mo1.group(2)), day=int(mo1.group(3)))
        clean_category=string.strip(date_re.sub('', category))
        timestamp_specifier='  '+mo1.group(0)
    elif mo2:
        timestamp = datetime.datetime(year=int(mo2.group(1)), month=1, day=1)
    elif mo3:
        timestamp = datetime.datetime(year=int(mo3.group(1)), month=1, day=1)

    return timestamp, clean_category, timestamp_specifier
      
      
class Path(object):
    def __init__(self, filename, timestamp, is_directory, action, category):
        self.filename=filename

        self.timestamp, category, self.timestamp_specifier = get_timestamp( category, filename, timestamp)

        self.is_directory=is_directory
        self.action=action
        self.category=category

        self.date = self.timestamp.date

        self.group, self.subgroup, self.folder = parse_category(self.category)
        if self.folder == "!":
            if self.filename.endswith(os.sep):
                self.folder = os.path.basename(self.filename[0:-1])
            else:
                self.folder = os.path.basename(self.filename)

            self.category = '%s/%s/%s' % (self.group, self.subgroup, self.folder)

    def row(self):
        """Returns the org-table row"""
        fname = self.filename
        if self.is_directory and not self.filename.endswith(os.sep):
            fname += os.sep
        
        return [self.category+self.timestamp_specifier, self.action, fname]

    def category_complete(self):
        return "" not in [self.group, self.subgroup, self.folder]

    def check(self):
        if self.action not in 'kKd':
            return "Action must be k, K or d for copying: %s" % self.filename
        if self.action != 'd' and not self.category_complete():
            return "Category not completely specified: %s" % self.filename            
        if self.action == 'd' and self.category != '':
            return "Action is delete, but category is non-empty: %s" % self.filename

        return None


properties=find_elements(doc.root, PyOrgMode.OrgDrawer.Property)

props={}
for p in properties:
    props[p.name]=unicode(p.value)

subgroups_per_group=int(props['subgroups-per-group'])
    
def get_files(relpath, category):
    abspath = os.path.join(props['sourcedir'], relpath)
    print "recursing into %s" % abspath

    result=[]
    for f in os.listdir(abspath):
        frel = os.path.join(relpath, f)
        fabs = os.path.join(abspath, f)

        path = Path(filename=frel,
                    timestamp=datetime.datetime.fromtimestamp(os.path.getmtime(fabs)),
                    is_directory=os.path.isdir(fabs),
                    action='u',
                    category=category)
        result.append(path)

    return result
    
filetable=find_elements(doc.root, PyOrgMode.OrgTable.Element)[0]

if len(filetable.content) < 2:
    print "no files, doing the initial scan of %s" % props['sourcedir']

    elements=get_files(relpath='', category=u'')
else:
    # process existing entries

    elements=[]
    
    for row in filetable.content:
        #print row
        category, action, frel = [c.strip() for c in row]


        if action == 'r':
            elements.extend(get_files(frel, category=category))
        else:
            fabs = os.path.join(props['sourcedir'], frel)

            if os.path.exists(fabs):            
               elements.append(Path(filename=frel,
                                    timestamp=datetime.datetime.fromtimestamp(os.path.getmtime(fabs)),
                                    is_directory=os.path.isdir(fabs),
                                    action=action,
                                    category=category))
            else:
               warn("Entry disappeared: %s" % fabs)
            

# look at the disk and see if there are any files not mentioned in the table
# add those to the list
existing_files = set([e.filename for e in elements])

def find_new_files(relpath, existing_files):
    abspath = os.path.join(props['sourcedir'], relpath)

    result=[]
    for f in os.listdir(abspath):
        frel = os.path.join(relpath, f)
        fabs = os.path.join(abspath, f)

        if os.path.isdir(fabs):
            if frel+'\\' not in existing_files:
                result.extend(find_new_files(frel, existing_files))
        else:
            if frel not in existing_files:
                path = Path(filename=frel,
                            timestamp=datetime.datetime.fromtimestamp(os.path.getmtime(fabs)),
                            is_directory=os.path.isdir(fabs),
                            action='u',
                            category='')
                result.append(path)

    return result

new_files = find_new_files('', existing_files)
elements.extend(new_files)


# sort the list
#  first by if it will be deleted or not
#  then by group
#  then by  subgroup
#  then by  folder
#  then by  if it is a direcory
#  then by  date (not time)
#  then by  filename
def make_sortkey(e):
  return (e.action=='d', e.group, e.subgroup, e.folder, e.is_directory, e.timestamp, e.filename)

elements.sort(key=make_sortkey)

filetable.content = [ e.row() for e in elements ]


# Build the category tree of all files with action k or K
groups = {}
# even simpler with defaultdict 
for e in elements:
    if e.action in ['k', 'K']:
        group = groups.setdefault(e.group, {})
        subgroup = group.setdefault(e.subgroup, {})
        subgroup.setdefault(e.folder, [0, e.timestamp])    
        subgroup[e.folder][0]+=1
        subgroup[e.folder][1]=min(subgroup[e.folder][1], e.timestamp)

nodes=find_elements(doc.root, PyOrgMode.OrgNode.Element)

# clear the category tree and build a fresh one
# also compose the list of copy operations
doc.root.content[-1].content=[]

text=[]

def dt(t):
    if t == "":
        return "(uncategorized)"
    return t

gid = subgroups_per_group
categories=dict() # maps categories to target directories
for group in sorted(groups.keys()):
    sgid = gid - 1

    subgroups=len(groups[group].keys())

    if (subgroups_per_group-subgroups) < args.minimum_groupspace:
      warn(("Group '%s' has %d subgroups, but that means that there is less than %d spare places for future additions.\n"+
           "Fix this by reorganizing the groups, increasing the subgroups-per-group setting in %s or by decreasing the --minimum-groupspace option.") %
           (group, subgroups, args.minimum_groupspace, args.file))
    
    groupname = "%d-%d %s" % (gid, gid+subgroups_per_group-1, dt(group))
    doc.root.append_clean(" * %s\n" % groupname)
    for subgroup in sorted(groups[group].keys()):
        sgid += 1
        fid = 0
        subgroupname = "%d %s" % (sgid, dt(subgroup))
        doc.root.append_clean("   * %s\n" % subgroupname)

        for folder in sorted(groups[group][subgroup].keys(), key=lambda f: groups[group][subgroup][f][1]):
            fid += 1
            foldername =  "%d.%02d %s" % (sgid, fid, dt(folder))
            doc.root.append_clean("     * %s (%d)\n" % (foldername, groups[group][subgroup][folder][0]))
            
            category = '%s/%s/%s' % (group, subgroup, folder)
            targetdir = os.sep.join([groupname, subgroupname, foldername])
            categories[category]=targetdir

    gid += subgroups_per_group

            
tmpfile=args.file+'.tmp'
doc.save_to_file(tmpfile)
shutil.move(tmpfile, args.file)

if args.copy:
    # check input
    for e in elements:
        warning = e.check()

        if warning is not None:
            warn("WARNING: %s" % warning)

    if warnings > 0 and not args.force:
        print "ERROR: Refusing to copy files because there were warnings. Fix or use --force."
        sys.exit(1)

    for e in [el for el in elements if el.action in ['k', 'K'] ]:
        if not e.category_complete():
            print "SKIPPING %s because a complete target has not been set" % e.filename
        else:
            src = os.path.join(props['sourcedir'], e.filename)

            if e.is_directory:

                if e.action == 'k':
                    # folder is copied as subdir to the new folder

                    head, subdir = os.path.split(e.filename)
                    if subdir == '': # if there is a trailing slash then the last
                        head, subdir = os.path.split(head)

                    dst = os.path.join(props['targetdir'], categories[e.category], subdir)
                    print (props['targetdir'], categories[e.category], subdir)
                elif e.action == 'K':
                    #  folder becomes the new folder
                    dst = os.path.join(props['targetdir'], categories[e.category])

                else:
                    raise Exception("Internal error - unknown action: %s" % e.action)
                print "%s -> %s" % (src, dst)

                if args.no_dry_run:
                    copytree(src, dst)
            else:
                dst = os.path.join(props['targetdir'], categories[e.category], os.path.basename(e.filename))
                
                print "%s -> %s" % (src, dst)

                if args.no_dry_run:
                    dir = os.path.dirname(dst)
                    if not os.path.exists(dir):
                        os.makedirs(dir)
                    shutil.copy2(src, dst)
