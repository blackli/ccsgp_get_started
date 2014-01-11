import sys, os, itertools, inspect

def getOpts(i):
  opts = 'lt 1 lw 4 ps 2 '
  if not i%2: opts += 'lc %d pt 18' % int(i/2)
  else: opts += 'lc 0'
  return opts

def checkSymLink():
  link_name = __name__.split('.')[0] + 'Dir'
  if not os.path.islink(link_name):
    logging.critical('create symlink %s to continue!' % link_name)
    sys.exit(1)

def getWorkDirs():
  # pydoc: use same output layout as for package
  # get caller module
  caller_fullurl = inspect.stack()[1][1]
  caller_relurl = os.path.relpath(caller_fullurl)
  caller_modurl = os.path.splitext(caller_relurl)[0]
  # split caller_url & append 'Dir' to package name
  dirs = caller_modurl.split('/')
  dirs[0] += 'Dir'
  # get, check and create outdir
  outDir = os.path.join(*dirs)
  if not os.path.exists(outDir): os.makedirs(outDir)
  # get and check indir
  dirs.insert(1, 'input')
  inDir = os.path.join(*dirs)
  if not os.path.exists(inDir):
    logging.critical('create input dir %s to continue!' % inDir)
    sys.exit(1)
  return inDir, outDir

def zip_flat(a, b):
  return list(itertools.chain.from_iterable(zip(a, b)))

