import os, argparse, logging
from .utils import getWorkDirs, checkSymLink, getEnergy4Key, particleLabel4Key
from collections import OrderedDict
from ..ccsgp.ccsgp import make_plot, make_panel
from ..ccsgp.config import default_colors
import numpy as np

def gp_syserr():
    energies = ['19.6', '27', '39', '62.4']
    inDir, outDir = getWorkDirs()
    inDir = os.path.join(inDir, 'syserr')
    data = OrderedDict()
    shift, factor = 0.7, -1.5
    ymin = OrderedDict((energy, 100) for energy in energies)
    ymax = OrderedDict((energy, -100) for energy in energies)
    for particle in ['e', 'pi']:
        for charge in ['plus', 'minus']:
            fname = particle + charge + '.dat'
            key = '{/Symbol \160}' if particle == 'pi' else 'e'
            key += '^{+}' if charge == 'plus' else '^{-}'
            data[key] = np.loadtxt(open(os.path.join(inDir, fname), 'rb'))
            # get y-values for error box
            for dp in data[key]:
                energy = '%g' % dp[0]
                curymin, curymax = dp[1]-dp[3], dp[1]+dp[3]
                if curymin < ymin[energy]: ymin[energy] = curymin
                if curymax > ymax[energy]: ymax[energy] = curymax
            # shift data for visibility
            data[key][:,0] += factor*shift
            factor += 1
    print ymax
    make_plot(
        data = data.values(),
        properties = [
            'lc %s lw 5 ps 2 pt %d' % (default_colors[10+i/2],18+i%2)
            for i in xrange(len(data))
        ],
        titles = data.keys(),
        tmargin = 0.98, rmargin = 0.99, bmargin = 0.13,
        yr = [0,22], xr = [15,68],
        xlabel = '{/Symbol \326}s_{NN} (GeV)',
        ylabel = 'Relative Systematic Uncertainty on {/Symbol \145}_{qual}{/Symbol \327}{/Symbol \145}_{glDCA} (%)',
        name = os.path.join(outDir, 'syserr'),
        size = '11in,8.5in', key = ['nobox', 'at graph 0.7,0.2', 'maxrows 2'],
        lines = dict(('y=%s' % energy,'lw 4 lt 2 lc "black"') for energy in energies),
        gpcalls = [
            'object %d rectangle back from %f,%f to %f,%f fc rgb "#FF9999" lw 2 fs border lc rgb "#FF6666"' % (
                50+i, float(energy)-1.5*shift, ymin[energy], float(energy)+1.5*shift, ymax[energy]
            ) for i,energy in enumerate(energies)
        ]
    )

def gp_tpc_select_eff():
    data = OrderedDict()
    inDir, outDir = getWorkDirs()
    for energy in ['19', '27', '39', '62']:
        infile = os.path.join(inDir, 'tpc_select_eff', 'electrons_%sGeV.dat' % energy)
        data_import = np.loadtxt(open(infile, 'rb'))
        nrows = len(data_import)
        data_import[:,1:] *= 100. # convert to %
        if energy != '19': data_import[:,2:] = 0
        key = '%s GeV' % getEnergy4Key(energy)
        data[key] = np.c_[
            data_import[:,:2], np.zeros(nrows),
            np.zeros(nrows), data_import[:,-1]
        ]
    make_plot(
        data = data.values(), titles = data.keys(),
        properties = [
            'with filledcurves lt 1 lc %s lw 5 pt 0' % default_colors[i]
            for i in range(len(data))
        ],
        tmargin = 0.98, rmargin = 0.99, yr = [75,100], xr = [0.2,2.052],
        gpcalls = ['xtics 0.5', 'mxtics 5', 'mytics 2'], key = ['nobox'],
        xlabel = 'momentum, p (GeV/c)', ylabel = 'TPC Selection Efficiency (%)',
        name = os.path.join(outDir, 'tpc_select_eff'), size = '8.8in,6.8in',
        labels = {'Electrons': [1.0,93,True]}
    )

def gp_tof_match():
    data = OrderedDict()
    inDir, outDir = getWorkDirs()
    subtitles = [
        '-1 < {/Symbol \150} < 1, -180 < {/Symbol \146} < 180',
        '0 < {/Symbol \150} < 0.25, -180 < {/Symbol \146} < 180',
        '-1 < {/Symbol \150} < 1, 45 < {/Symbol \146} < 60',
        '0 < {/Symbol \150} < 0.25, 45 < {/Symbol \146} < 60',
    ]
    for isuf,suffix in enumerate([
        'Eta1_Phi1', 'Eta8_Phi1', 'Eta1_Phi24', 'Eta8_Phi24'
    ]):
        subkey = subtitles[isuf]
        data[subkey] = [[], [], []]
        d = OrderedDict()
        for ip,particle in enumerate(['pi', 'e']):
            infile = os.path.join(inDir, 'tof_match', '%sminus_39_%s.dat' % (particle, suffix))
            data_import = np.loadtxt(open(infile, 'rb'))
            data_import[:,3:] *= 100. # convert to %
            data_import = data_import[data_import[:,0]<2.]
            if particle == 'pi': data_import[:,4] = 0
            if suffix != 'Eta8_Phi24': data_import[:,-1] = 0
            nrows = len(data_import)
            d[particle] = np.c_[ data_import[:,0], data_import[:,3], np.zeros(nrows), data_import[:,4:] ]
            data[subkey][0].append(d[particle])
            data[subkey][1].append('with %s lc %s lw 5 lt 1' % (
                'points pt 18 ps 1.5' if particle == 'e' else 'filledcurves pt 0', default_colors[ip]
            ))
            data[subkey][2].append('e^{-} (39 GeV)' if particle == 'e' else 'scaled {/Symbol \160}^{-} (39 GeV)')
        chi2i = [
            ((o-e)/s)**2
            for o,e,s in np.c_[d['e'][:,1], d['pi'][:,1], d['e'][:,3]]
            if o > 0 and e > 0 and s > 0
        ]
        newsubkey = subkey + ', {/Symbol \543}@^{2}_{red} = %.2g' % (sum(chi2i)/len(chi2i))
        print newsubkey
        data[newsubkey] = data[subkey]
        del data[subkey]
    make_panel(
        dpt_dict = data,
        name = os.path.join(outDir, 'tof_match'),
        xlog = True, xr = [0.18, 2.1], yr = [35, 97],
        xlabel = 'transverse momentum, p_{T} (GeV/c)',
        ylabel = 'TOF Matching Efficiency (%)',
        layout = '2x2', size = '5in,7.5in',
        key = ['nobox', 'bottom right'],
        gpcalls = [ 'xtics add (.2,.5,1,2)' ],
    )

if __name__ == '__main__':
  checkSymLink()
  parser = argparse.ArgumentParser()
  parser.add_argument("--log", help="show log output", action="store_true")
  args = parser.parse_args()
  loglevel = 'DEBUG' if args.log else 'WARNING'
  logging.basicConfig(
    format='%(message)s', level=getattr(logging, loglevel)
  )
  #gp_syserr()
  #gp_tpc_select_eff()
  gp_tof_match()
