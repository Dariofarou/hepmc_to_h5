# hepmc_to_h5
Extracts final state particles from HepMC files and stores into hdf5 file.

The output data has a similar format as the R&D Dataset from the LHC Olympics 2020 Anomaly Detection Challenge. Each event is described by a flattened array of particle (hadrons) coordinates in three possible formats:  

  PTEP:  (pT, η, φ, pT, η, φ, ...) 
  PTEPM: (pT, η, φ, M, pT, η, φ, M, ...) 
  EP:    (E, px, py, pz, E, px, py, pz, ...)
 
Event arrays are zero padded to a fixed size M, set by the event in the sample with the largest number of particles. The truth label of each sample file can be appended at the end of each event array. The complete dataset stored in the h5 output is a numpy array of shape (Nevents, M) or (Nevents, M+1) if the truth label is included.

Basic information about the data (shape, number of signal and background events, dtype, etc) is stored as dataset attributes. 

usage: hepmc_to_hdf5.py files [input_files ...] [-h] [--truth TRUTH [TRUTH ...]] [--output OUTPUT] [--dtype DTYPE] 

optional arguments:

  -h, --help                                        show this help message and exit
  --truth TRUTH [TRUTH ...], -t TRUTH [TRUTH ...]   optional list of truth labels for hepmc files
  --output OUTPUT, -o OUTPUT                        name of output file
  --dtype DTYPE, -d DTYPE                           choose data type: PTEP (pT, η, φ, pT, η, φ, ...), 
                                                                      PTEPM (pT, η, φ, M, pT, η, φ, M, ...)
                                                                      EP (E, px, py, pz, E, px, py, pz, ...)


TODO: formats thast include vertex information (x,y,z,ct) and pID. 

Dependencies: h5py, pyjet
