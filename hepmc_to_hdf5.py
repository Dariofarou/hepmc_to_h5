import h5py 
import numpy as np 
from pyjet import DTYPE_PTEPM,DTYPE_EP 
import os
import sys
import pandas as pd
import argparse
from random import shuffle
from timeit import default_timer as timer
          

'''
README:

Extracts final state particles from hepmc2/hepmc3 files 
and stores into compressed hdf5 file. The output data 
has a similar format as the R&D Dataset from the 
LHC Olympics 2020 Anomaly Detection Challenge. 

Each event is described by a flattened array of hadron
coordinates in three possible formats:  

  PTEP:  (pT, η, φ, pT, η, φ, ...) 
  PTEPM: (pT, η, φ, M, pT, η, φ, M, ...) 
  EP:    (E, px, py, pz, E, px, py, pz, ...)
 
Event arrays are zero padded to a fixed size M, set by the event
in the sample with the largest number of particles. The truth label
of each sample file can be appended at the end of each event array. 
The complete dataset stored in the h5 output is a numpy array of 
shape (Nevents, M) or (Nevents, M+1) if the truth label is included.

Basic information about the data (shape, number of signal and
background events, dtype, etc) is stored as dataset attributes. 


usage: hepmc_to_hdf5.py files [input_files ...] [-h] [--truth TRUTH [TRUTH ...]] [--output OUTPUT] [--dtype DTYPE] 

optional arguments:

  -h, --help                                        show this help message and exit
  --truth TRUTH [TRUTH ...], -t TRUTH [TRUTH ...]   optional list of truth labels for hepmc files
  --output OUTPUT, -o OUTPUT                        name of output file
  --dtype DTYPE, -d DTYPE                           choose data type: PTEP (pT, η, φ, pT, η, φ, ...), 
                                                                      PTEPM (pT, η, φ, M, pT, η, φ, M, ...)
                                                                      EP (E, px, py, pz, E, px, py, pz, ...)

Dependencies: h5py, pyjet

TODO: formats thast include vertex information (x,y,z,ct) and pID. 

'''

################################################          

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

################################################          

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

################################################          

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
        evt.weights = [float(vals[-1])] # TODO: do this right, and handle weight maps
        ## Read the other event header lines until a Vertex line is encountered
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
                self._currentvtx = bc # current vtx barcode for following Particles
                v = Vertex(barcode=bc, pos=[float(x) for x in vals[3:7]], event=evt)
                evt.vertices[bc] = v
            elif not self._currentline or self._currentline == "HepMC::IO_GenEvent-END_EVENT_LISTING":
                break
            self._read_next_line()
        return evt

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

def hepmc_to_hdf5(input_files,output='events.h5',dtype='PTEP',truth_labels=-1):
    t=timer()
    dim=0; X=[]; L=[]
    for i,file in enumerate(input_files):
        print('...processing {}'.format(file))
        line = HepMCReader(file)
        while True:
            evt = line.next()
            if not evt:
                break 
            final_states=[evt.particles[p][2:] for p in evt.particles if evt.particles[p][0]==1]
            x=[]
            for p in final_states:
                mom=np.zeros(1, dtype=DTYPE_EP)
                mom['px']=p[0]; mom['py']=p[1]; mom['pz']=p[2]; mom['E']=p[3]
                if dtype=='EP':
                    x+=list(mom[0])
                elif dtype=='PTEP': 
                    x+=list(ep2ptepm(mom)[0])[:3]
                elif dtype=='PTEPM': 
                    x+=list(ep2ptepm(mom)[0])
            X.append(x)
            if truth_labels!=-1:
                L.append(truth_labels[i])                
            if len(x)>dim:
                dim=len(x)
    for i in range(0,100000,100):
        if i<dim<=i+100:
            dim=i+100
            break
    events=[]
    for i,e in enumerate(X):
        if len(L)==0:
            particles=np.zeros(dim)
            particles[:len(e)]=e 
            events.append(particles)
        else:
            particles=np.zeros(dim+1)
            particles[:len(e)]=e 
            particles[-1]=L[i]
            events.append(particles)   
    shuffle(events)
    data=np.stack(events)
    print('...extracted data shape : {}'.format(data.shape))
    print('...shuffling and saving events to {}'.format(output)) 
    # if data.shape[0]>1000:
    #     nchunk=1000
    # else:
    #     nchunk=data.shape[0]
    # chunks=(nchunk,data.shape[1])
    # chunks=None
    with h5py.File(output,'w', libver='latest') as f:
        dset=f.create_dataset('data',data=data, compression='gzip', compression_opts=9)
        dset.attrs.create(name='shape',data=data.shape)
        dset.attrs.create(name='nsignal',data=int(np.sum(L)))
        dset.attrs.create(name='nbackgr',data=int(len(L)-np.sum(L)))
        dset.attrs.create(name='dtype',data=dtype)
        dset.attrs.create(name='hepmc',data=input_files)
        dset.attrs.create(name='truth',data=truth_labels)
   
    print('...hepmc to hdf5 extraction finished!')
    print('...'+ elapsed_time(t))
    
################################################          

parser = argparse.ArgumentParser()
p1=parser.add_argument('--truth','-t', nargs='+', type=int, default=-1, help='optional list of truth labels for hepmc files...')
p2=parser.add_argument('files', nargs='+', help='list hepmc files to be converted to h5...')
p3=parser.add_argument('--output', '-o', default='events.h5', help='name of output file...')
p4=parser.add_argument('--dtype', '-d',default='PTEP', help='choose one of three data types: PTEP (pT, η, φ, pT, η, φ, ...), PTEPM (pT, η, φ, M, pT, η, φ, M, ...), or EP (E, px, py, pz, E, px, py, pz, ...)')

FLAGS=parser.parse_args()
truths=FLAGS.truth
files=FLAGS.files
output=FLAGS.output
dtype=FLAGS.dtype

if (truths!=-1 and len(truths)!=len(files)):
    raise argparse.ArgumentError(p1,'missing or too many truth labels provided!') 

################################################   

hepmc_to_hdf5(input_files=files,output=output,truth_labels=truths,dtype=dtype)



    