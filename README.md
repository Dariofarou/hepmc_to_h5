# README
```hepmc_to_hdf5``` extracts final state particles (hadrons) from *HepMC2* or *HepMC3* files and saves them into a single *hdf5* file in a compact format similar to the R&D dataset of the [LHC Olympics 2020 Anomaly Detection Challenge](https://lhco2020.github.io/homepage/). 

Each event is described by a flattened array of particle 'detector' coordinates in three possible formats:  

 - ```PTEP```:  (pT, η, φ, pT, η, φ, pT, η, φ,...) 
  
 - ```PTEPM```: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)
  
 - ```EP```:    (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)
 
Event arrays are zero padded to a fixed size *M*, set by the event in the sample with the largest number of particles. The truth label of each sample file can be appended at the end of each event array. The complete dataset is a numpy array with shape *(Nevents, M)*, or *(Nevents, M+1)* if truth labels are  provided. Basic information about the data (shape, number of signal and background events, dtype, etc) are stored as dataset attributes. 

***TODO: include vertex information (x,y,z,ct) and particle ID.*** 

# Requirements: 
- h5py
- pyjet

# Usage:
```bash
hepmc_to_hdf5.py files [files ...] [-h] [--truth TRUTH ...] [--output OUTPUT] [--dtype DTYPE]
```
Example: to extract particles with *(pT, η, φ, M)* coordinates from three hepmc files
- *events_1.hepmc* (signal process)
- *events_2.hepmc* (background process)
- *events_3.hepmc* (another background process) 

and store them into *events.h5* including truth level information, just run:
```bash
python hepmc_to_hdf5.py events_1.hepmc events_2.hepmc events_3.hepmc --truth 1 0 0 --output events.h5 --dtype PTEPM
```
To completely remove truth labels from the output simply remove the ```--truth``` arguments above. 
For more information: 
```bash
hepmc_to_hdf5.py --help
```
