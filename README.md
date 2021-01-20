# README
```hepmc_to_h5``` extracts final state particles from ***HepMC*** files and stores them into a single ***hdf5*** file in a format similar to the R&D Dataset formats for the LHC Olympics 2020 Anomaly Detection Challenge. 

Each event is described by a flattened array of particle 'detector' coordinates in three possible formats:  

 * ```PTEP```:  (pT, η, φ, pT, η, φ, pT, η, φ,...) 
  
 * ```PTEPM```: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)
  
 * ```EP```:    (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)
 
Event arrays are zero padded to a fixed size *M*, set by the event in the sample with the largest number of particles. The truth label of each sample file can be appended at the end of each event array. The complete dataset stored in the hdf5 output is a numpy array with shape *(Nevents, M)*, or *(Nevents, M+1)* if truth labels are  provided. Basic information about the data (shape, number of signal and background events, dtype, etc) are stored as dataset attributes. 

***TODO: include data formats with vertex information (x,y,z,ct) and particle ID.*** 

# Requirements: 
- h5py
- pyjet

# Usage:
```bash
hepmc_to_hdf5.py files [files ...] [-h] [--truth TRUTH ...] [--output OUTPUT] [--dtype DTYPE]
```
Example: To extract particles with *(pT, η, φ, M)* coordinates from three hepmc files
- *events_1.hepmc* (background process)
- *events_2.hepmc* (signal process)
- *events_3.hepmc* (another background process) 

and store into *events.h5* with truth bits, just run:
```bash
python hepmc_to_hdf5.py events_1.hepmc events_2.hepmc events_3.hepmc --truth 0 1 0 --output events.h5 --dtype PTEPM
```
To completely remove truth labels from the output simply remove the ```--truth``` arguments above. 
For more information: 
```bash
hepmc_to_hdf5.py --help
```
