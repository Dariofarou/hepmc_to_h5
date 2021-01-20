# README
```hepmc_to_h5``` extracts final state particles from a set of ***HepMC*** files and stores them in a compact format into a single ***hdf5*** file.

The output data has a similar format as the R&D Dataset from the LHC Olympics 2020 Anomaly Detection Challenge. Each event is described by a flattened array of particle 'detector' coordinates in three possible formats:  

  ```PTEP```:  (pT, η, φ, pT, η, φ, pT, η, φ,...) 
  
  ```PTEPM```: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)
  
  ```EP```:    (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)
 
Event arrays are zero padded to a fixed size *M*, set by the event in the sample with the largest number of particles. The truth label of each sample file can be appended at the end of each event array. The complete dataset stored in the h5 output is a numpy array of shape *(Nevents, M)* or *(Nevents, M+1)* if truth labels are  provided. Basic information about the data (shape, number of signal and background events, dtype, etc) are stored as dataset attributes. 

***TODO: include data formats with vertex information (x,y,z,ct) and particle ID.*** 

# Requirements: 
h5py, pyje

# Usage:
```bash
hepmc_to_hdf5.py files [files ...] [-h] [--truth TRUTH ...] [--output OUTPUT] [--dtype DTYPE]
```
For example: in order to extract final state hadrons in *(pT, η, φ, M)* coordinates from three hepmc files *events_1.hepmc* (signal process), events_2.hepmc (background process), events_3.hepmc (another background process) and store into a single hdf5 file *events.h5* with truth bits, just do:
```bash
python hepmc_to_hdf5.py events_1.hepmc events_2.hepmc events_3.hepmc --truth 1 0 0 --output events.h5 --dtype PTEPM
```
To omit truth labels simply remove the ```--truth``` arguments above. For more info: 
```bash
hepmc_to_hdf5.py --help
```
