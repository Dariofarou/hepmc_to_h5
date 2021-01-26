import h5py 
import numpy as np 
from pyjet import DTYPE_PTEPM,DTYPE_EP 
import os
import sys
import pandas as pd
import argparse
from random import shuffle
from timeit import default_timer as timer      

__version__='1.0.0'
__author__ ='Darius Faroughy <faroughy@physik.uzh.ch>'

'''
README:

hepmc_to_hdf5 extracts final state particles from HepMC2 collider event 
records and saves them into a single hdf5 file in a compact format 
similar to the R&D dataset of the LHC Olympics 2020 Anomaly Detection Challenge.

Each event is described by a flattened array of particle 'detector' coordinates
 in three possible kinematical representations:

COMPACT: (pT, η, φ, pT, η, φ, pT, η, φ,...)

PTEPM: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)

EP: (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)

In each event array, particles are ordered by transverse momentum (for COMPACT and PTEPM)
or energy (for EP), and are zero-padded to a constant size M. 
The padding size M can be set by hand (by specyfing the number of 
leading particles to be kept) or fixed by the event with the largest 
number of particles in the sample. The truth label of each hepmc file
can be appended at the end of each event array. The complete dataset
is a numpy array of stacked events with shape (Nevents, M), or (Nevents, M+1)
if truth labels are provided. Basic information about the data (shape, number of
signal and background events, dtype, etc) are stored as dataset attributes.


usage: 

hepmc_to_hdf5.py [-h] [--truth TRUTH [TRUTH ...]] [--nevents NEVENTS [NEVENTS ...]] [--nparts NPARTS] [--output OUTPUT] [--dtype DTYPE] [--gzip] [--chunks CHUNKS] files [files ...]

optional arguments:

  -h, --help                                                  show this help message and exit
  --truth TRUTH [TRUTH ...], -t TRUTH [TRUTH ...]             truth level bit for each hepmc file
  --nevents NEVENTS [NEVENTS ...], -N NEVENTS [NEVENTS ...]   max event number for each hepmc file
  --nparts NPARTS, -n NPARTS                                  store the n leading particles in each event with zero-padding
  --pandas, -pd                                               save as padas DataFrame (recommended)
  --output OUTPUT, -o OUTPUT                                  name of output file
  --dtype DTYPE, -d DTYPE                                     choose data types: COMPACT (pT, η, φ, pT, η, φ, ...)
                                                                                 PTEPM (pT, η, φ, M, pT, η, φ, M, ...)
                                                                                 EP (E, px, py, pz, E, px, py, pz, ...)
  --gzip, -gz                                                 compress h5 output
  --chunks CHUNKS, -k CHUNKS                                  chunk shape when saving to h5 file

'''          

parser = argparse.ArgumentParser()
p0=parser.add_argument('files', nargs='+', help='input hepmc files')
p1=parser.add_argument('--truth', '-t', nargs='+', type=int, default=-1, help='truth level bit for each hepmc file')
p2=parser.add_argument('--nevents', '-N', nargs='+', type=int, default=-1, help='max event number for each hepmc file')
p3=parser.add_argument('--nparts', '-n', type=int, default=-1, help='store the n leading particles in each event with zero-padding')
p4=parser.add_argument('--pandas', '-pd', action='store_true',default=False, help='save as pandas DataFrame')
p5=parser.add_argument('--output', '-o', default='events.h5', help='name of output file')
p6=parser.add_argument('--dtype', '-d', default='COMPACT', help='choose data types: COMPACT (pT, η, φ, pT, η, φ, ...), PTEPM (pT, η, φ, M, pT, η, φ, M, ...), or EP (E, px, py, pz, E, px, py, pz, ...)')
p7=parser.add_argument('--gzip', '-gz', action='store_true',default=False, help='compress h5 output')
p8=parser.add_argument('--chunks', '-k', default=None, help='chunk shape when saving to h5 file')

FLAGS=parser.parse_args()

if (FLAGS.truth!=-1 and len(FLAGS.truth)!=len(FLAGS.files)):
    raise argparse.ArgumentError(p1,'missing or too many truth labels provided!') 
if (FLAGS.nevents!=-1 and len(FLAGS.nevents)!=len(FLAGS.files)):
    raise argparse.ArgumentError(p2,'missing or too many event numbers provided!') 

def hepmc_to_hdf5(FLAGS):
    
    t=timer()
    truth_labels=FLAGS.truth
    input_files=FLAGS.files
    output=FLAGS.output
    dtype=FLAGS.dtype
    gzip=FLAGS.gzip
    chunks=FLAGS.chunks
    nevents=FLAGS.nevents
    nparts=FLAGS.nparts
    pandas=FLAGS.pandas
    dim=0 

    events=[] 
    labels=[]

    for i,file in enumerate(input_files):
        print('...processing {}'.format(file))
        line = HepMCReader(file)
        Nev=0
        while True:
            evt = line.next()
            if not evt:
                break 
            
            final_states=[evt.particles[p][2:] for p in evt.particles if evt.particles[p][0]==1] # extracts only final state particles
            
            ep_list=[]
            ptepm_list=[]
            compact_list=[]

            for p in final_states: # this is too slow.... need to optimize

                kin_ep=np.zeros(1,dtype=DTYPE_EP)   # dtype=[('E', '<f8'), ('px', '<f8'), ('py', '<f8'), ('pz', '<f8')])
                kin_ep['px']=p[0]
                kin_ep['py']=p[1]
                kin_ep['pz']=p[2]
                kin_ep['E']=p[3]
                kin_ptepm=ep2ptepm(kin_ep)          # dtype=[('pT', '<f8'), ('eta', '<f8'), ('phi', '<f8'), ('mass', '<f8')])
                ep_list.append(list(kin_ep[0]))
                ptepm_list.append(list(kin_ptepm[0]))
                compact_list.append(list(kin_ptepm[0])[:3])

            if dtype=='COMPACT':
                ev=compact_list
                len_dtype=3
                del ptepm_list, ep_list

            if dtype=='EP':
                ev=ep_list
                len_dtype=4
                del compact_list, ptepm_list

            if dtype=='PTEPM':
                ev=ptepm_list
                len_dtype=4
                del compact_list, ep_list 

            # TODO:  add dtypes including particle ID  of form (pid, pT, η, φ, pid, pT, η, φ, ...)
            # if dtype=='ICOMPACT':
            #     ev=compact_list
            #     len_dtype=3
            #     del ptepm_list, ep_list

            # if dtype=='IEP':
            #     ev=ep_list
            #     len_dtype=4
            #     del compact_list, ptepm_list

            # if dtype=='IPTEPM':
            #     ev=ptepm_list
            #     len_dtype=4
            #     del compact_list, ep_list 

            ev.sort(reverse=True)   # sorts particles by decreasing 'pT' for COMPACT/PTEPM, and by decreasing 'E' for EP
            
            if 0<nparts<len(ev):
                ev=ev[:nparts]      # truncates event to keep the 'nparts' leading particles
            if len(ev)>dim:
                dim=len(ev) 
            if truth_labels!=-1:
                labels.append(truth_labels[i]) 

            events.append([item for sublist in ev for item in sublist])

            if nevents!=-1:
                Nev+=1
                if Nev==nevents[i]:
                    break

    print('...zero-padding data')
    events_0pad=[]
    for i,e in enumerate(events):
        if truth_labels==-1:
            particles=np.zeros(dim*len_dtype,dtype=np.float32)
            particles[:len(e)]=e 
            events_0pad.append(particles)
        else:
            particles=np.zeros(dim*len_dtype+1,dtype=np.float32)
            particles[:len(e)]=e 
            particles[-1]=labels[i]
            events_0pad.append(particles)  

    shuffle(events_0pad)
    data=np.stack(events_0pad)
    print('...extracted data shape : {}'.format(data.shape))
    print('...shuffling and saving events to {}'.format(output))

    if pandas:
        df=pd.DataFrame(data)
        df.to_hdf(output, key='df', mode='w')
    else:
        with h5py.File(output,'w', libver='latest') as f:
            dset=f.create_dataset('data',data=data, chunks=chunks, compression=gzip)
            dset.attrs.create(name='shape',data=data.shape)
            dset.attrs.create(name='nevents',data=nevents)
            dset.attrs.create(name='nparticles',data=nparts)
            dset.attrs.create(name='nsignal',data=int(np.sum(labels)))
            dset.attrs.create(name='nbackgr',data=int(len(labels)-np.sum(labels)))
            dset.attrs.create(name='dtype',data=dtype)
            dset.attrs.create(name='hepmc',data=input_files)
            dset.attrs.create(name='truth',data=truth_labels)

    print('...done!')
    print('...'+ elapsed_time(t))
    return data
    
################################################          
# from Python module pyhepmc 1.0.3 

class HepMCReader(object):
    def __init__(self, filename):
        self._file = open(filename)
        self._currentline = None
        self._currentvtx = None
        self.version = None
        ## First non-empty line should be the version info
        while True:
            self._read_next_line()
            if self._currentline.startswith("HepMC::Version"):
                self.version = self._currentline.split()[1]
                break
        ## Read on until we see the START_EVENT_LISTING marker
        while True:
            self._read_next_line()
            if self._currentline == "HepMC::IO_GenEvent-START_EVENT_LISTING":
                break
        ## Read one more line to make the first E line current
        self._read_next_line()

    def _read_next_line(self):
        "Return the next line, stripped of the trailing newline"
        self._currentline = self._file.readline()
        if not self._currentline: # no newline means it's the end of the file
            return False
        if self._currentline.endswith("\n"):
            self._currentline = self._currentline[:-1] # strip the newline
        return True

    def next(self):
        "Return a new event graph"
        evt = Event()
        if not self._currentline or self._currentline == "HepMC::IO_GenEvent-END_EVENT_LISTING":
            return None
        assert self._currentline.startswith("E ")
        vals = self._currentline.split()
        evt.num = int(vals[1])
        evt.weights = [float(vals[-1])] 
        while not self._currentline.startswith("V "):
            self._read_next_line()
            vals = self._currentline.split()
            if vals[0] == "U":
                evt.units = vals[1:3]
            elif vals[0] == "C":
                evt.xsec = [float(x) for x in vals[1:3]]
        # Read the event content lines until an Event line is encountered
        while not self._currentline.startswith("E "):
            vals = self._currentline.split()
            if vals[0] == "P":
                bc = int(vals[1])
                try:
                    mom=[float(x) for x in vals[3:7]]
                    evt.particles[bc]=(int(vals[8]),int(vals[2]),float(vals[3]),float(vals[4]),float(vals[5]),float(vals[6]))
                except:
                    print(vals)
            elif vals[0] == "V":
                bc = int(vals[1])
                self._currentvtx = bc 
                v = Vertex(barcode=bc, pos=[float(x) for x in vals[3:7]], event=evt)
                evt.vertices[bc] = v
            elif not self._currentline or self._currentline == "HepMC::IO_GenEvent-END_EVENT_LISTING":
                break
            self._read_next_line()
        return evt

class Particle(object):
    def __init__(self, pid=0, mom=[0,0,0,0], barcode=0, event=None):
        self.evt = event
        self.barcode = barcode
        self.pid = pid
        self.status = None
        self.mom = list(mom)
        self.nvtx_start = None
        self.nvtx_end = None
        self.mass = None
    def vtx_start(self):
        return self.evt.vertices.get(self.nvtx_start) if self.evt else None
    def vtx_end(self):
        return self.evt.vertices.get(self.nvtx_end) if self.evt else None
    def parents(self):
        return self.vtx_start().parents() if self.vtx_start() else None
    def children(self):
        return self.vtx_end().children() if self.vtx_end() else None
    def __repr__(self):
        return "P" + str(self.barcode)

class Vertex(object):
    def __init__(self, pos=[0,0,0,0], barcode=0, event=None):
        self.evt = event
        self.pos = list(pos)
        self.barcode = barcode
    def parents(self):
        return [p for p in self.evt.particles.values() if p.nvtx_end == self.barcode]
    def children(self):
        return [p for p in self.evt.particles.values() if p.nvtx_start == self.barcode]
    def __repr__(self):
        return "V" + str(self.barcode)

class Event(object):
    def __init__(self):
        self.num = None
        self.weights = None
        self.units = [None, None]
        self.xsec = [None, None]
        self.particles = {}
        self.vertices = {}

    def __repr__(self):
        return "E%d. #p=%d #v=%d, xs=%1.2e+-%1.2e" % \
               (self.num, len(self.particles), len(self.vertices),
                self.xsec[0], self.xsec[1])

################################################          

def ep2ptepm(rec):  #Convert (E, px, py, pz) into (pT, eta, phi, mass)
    E, px, py, pz = rec.dtype.names[:4]
    vects = np.empty(rec.shape[0], dtype=DTYPE_PTEPM)
    ptot = np.sqrt(np.power(rec[px], 2) + np.power(rec[py], 2) + np.power(rec[pz], 2))
    costheta = np.divide(rec[pz], ptot)
    costheta[ptot == 0] = 1.
    good_costheta = np.power(costheta, 2) < 1
    vects['pT'] = np.sqrt(np.power(rec[px], 2) + np.power(rec[py], 2))
    vects['eta'][good_costheta] = -0.5 * np.log(np.divide(1. - costheta, 1. + costheta))
    vects['eta'][~good_costheta & (rec[pz] == 0.)] = 0.
    vects['eta'][~good_costheta & (rec[pz] > 0.)] = 10e10
    vects['eta'][~good_costheta & (rec[pz] < 0.)] = -10e10
    vects['phi'] = np.arctan2(rec[py], rec[px])
    vects['phi'][(rec[py] == 0) & (rec[px] == 0)] = 0
    mass2 = np.power(rec[E], 2) - np.power(ptot, 2)
    neg_mass2 = mass2 < 0
    mass2[neg_mass2] *= -1
    vects['mass'] = np.sqrt(mass2)
    vects['mass'][neg_mass2] *= -1
    return vects

################################################          

def elapsed_time(t0):
    t=timer()-t0
    if t < 60.: 
        res='time: {} sec'.format(t)
    elif (t > 60. and t < 3600.0): 
        res='time: {} min'.format(t/60.)
    elif  t >= 3600.0: 
        res='time: {} hours'.format(t/3600.)
    return res

################################################          
      
# run:
hepmc_to_hdf5(FLAGS)
