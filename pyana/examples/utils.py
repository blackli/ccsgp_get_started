import sys, os, itertools, inspect, logging
import numpy as np
from uncertainties import unumpy as unp
from uncertainties.umath import fsum
from decimal import Decimal
mass_titles = [ 'pi0', 'LMR', 'omphi', 'IMR' ]
eRanges = np.array([ Decimal(str(e)) for e in [ 0, 0.4, 0.75, 1.1, 3. ] ])

def checkSymLink():
  """check for symbolic link to input directory"""
  link_name = __name__.split('.')[0] + 'Dir'
  if not os.path.islink(link_name):
    logging.critical('create symlink %s to continue!' % link_name)
    sys.exit(1)

def getWorkDirs():
  """get input/output dirs (same input/output layout as for package)"""
  # get caller module
  caller_fullurl = inspect.stack()[1][1]
  caller_relurl = os.path.relpath(caller_fullurl)
  caller_modurl = os.path.splitext(caller_relurl)[0]
  # split caller_url & append 'Dir' to package name
  dirs = caller_modurl.split('/')
  dirs[0] += 'Dir'
  # get, check and create outdir
  outDir = os.path.join(*(dirs + ['output']))
  if not os.path.exists(outDir): os.makedirs(outDir)
  # get and check indir
  dirs.append('input')
  inDir = os.path.join(*dirs)
  if not os.path.exists(inDir):
    logging.critical('create input dir %s to continue!' % inDir)
    sys.exit(1)
  return inDir, outDir

def getUArray(npArr):
  """uncertainty array multiplied by binwidth (col2 = dx)"""
  # propagates systematic uncertainty!
  return unp.uarray(npArr[:,1], npArr[:,4]) * npArr[:,2] * 2

def getEdges(npArr):
  """get np array of bin edges"""
  edges = np.concatenate(([0], npArr[:,0] + npArr[:,2]))
  return np.array([Decimal(str(i)) for i in edges])

def getMaskIndices(mask):
  """get lower and upper index of mask"""
  return [
    list(mask).index(True), len(mask) - 1 - list(mask)[::-1].index(True)
  ]

def enumzipEdges(eArr):
  """zip and enumerate edges into pairs of lower and upper limits"""
  return enumerate(zip(eArr[:-1], eArr[1:]))

def getCocktailSum(e0, e1, eCocktail, uCocktail):
  """get the cocktail sum for a given data bin range"""
  # get mask and according indices
  mask = (eCocktail >= e0) & (eCocktail <= e1)
  # data bin range wider than single cocktail bin
  if np.any(mask):
    idx = getMaskIndices(mask)
    # determine coinciding flags
    eCl, eCu = eCocktail[idx[0]], eCocktail[idx[1]]
    not_coinc_low, not_coinc_upp = (eCl != e0), (eCu != e1)
    # get cocktail sum in data bin (always w/o last bin)
    uCocktailSum = fsum(uCocktail[mask[:-1]][:-1])
    logging.debug('    sum: {}'.format(uCocktailSum))
    # get correction for non-coinciding edges
    if not_coinc_low:
      eCl_bw = eCl - eCocktail[idx[0]-1]
      corr_low = (eCl - e0) / eCl_bw
      abs_corr_low = float(corr_low) * uCocktail[idx[0]-1]
      uCocktailSum += abs_corr_low
      logging.debug(('    low: %g == %g -> %g (%g) -> %g -> {} -> {}' % (
        e0, eCl, eCl - e0, eCl_bw, corr_low
      )).format(abs_corr_low, uCocktailSum))
    if not_coinc_upp:
      if idx[1]+1 < len(eCocktail):
        eCu_bw = eCocktail[idx[1]+1] - eCu
        corr_upp = (e1 - eCu) / eCu_bw
        abs_corr_upp = float(corr_upp) * uCocktail[idx[1]]
      else:# catch last index (quick fix!)
        abs_corr_upp = eCu_bw = corr_upp = 0
      uCocktailSum += abs_corr_upp
      logging.debug(('    upp: %g == %g -> %g (%g) -> %g -> {} -> {}' % (
        e1, eCu, e1 - eCu, eCu_bw, corr_upp
      )).format(abs_corr_upp, uCocktailSum))
  else:
    mask = (eCocktail >= e0)
    idx = getMaskIndices(mask) # only use first index
    # catch if already at last index
    if idx[0] == idx[1] and idx[0] == len(eCocktail)-1:
      corr = (e1 - e0) / (eCocktail[idx[0]] - eCocktail[idx[0]-1])
      uCocktailSum = float(corr) * uCocktail[idx[0]-1]
    else: # default case
      corr = (e1 - e0) / (eCocktail[idx[0]+1] - eCocktail[idx[0]])
      uCocktailSum = float(corr) * uCocktail[idx[0]]
    logging.debug('    sum: {}'.format(uCocktailSum))
  return uCocktailSum

def getMassRangesSums(
  indata,  suffix = "", customRanges = None,
  onlyLMR = False, systLMR = False, singleRange = False
):
  eRangesSyst = [ eRanges if customRanges is None else customRanges ]
  if systLMR:
    step_size, nsteps, rangeOffsetsLMR = 0.05, 4, [0.15, 0.6]
    eEdgesSyst = [ [ # all lower & upper edges for LMR syst. study
      Decimal(str(rangeOffsetsLMR[j]+i*step_size))
      for i in xrange(nsteps)
    ] for j in xrange(2) ]
    # all combos of lower and upper LMR edges
    eRangesSyst = [ [ le, ue ] for ue in eEdgesSyst[1] for le in eEdgesSyst[0] ]
    onlyLMR = False # flag meaningless in this case
  # combine stat. and syst. errorbars
  indata[:,4] = np.sqrt(indata[:,3] * indata[:,3] + indata[:,4] * indata[:,4])
  uInData = getUArray(indata)
  eInData = getEdges(indata)
  uSums = {}
  for erngs in eRangesSyst:
    for i, (e0, e1) in enumzipEdges(erngs):
      if onlyLMR and i != 1: continue
      uSum = getCocktailSum(e0, e1, eInData, uInData)
      if (not systLMR) and (onlyLMR or singleRange): return uSum
      logging.debug('%g - %g: %r' % (e0, e1, uSum))
      key = mass_titles[1 if systLMR else i] + suffix
      if systLMR: key += '_%s-%s' % (e0,e1)
      uSums[key] = uSum
  return uSums

def getEnergy4Key(energy):
  if energy == '19': return '19.6'
  if energy == '62': return '62.4'
  return energy
