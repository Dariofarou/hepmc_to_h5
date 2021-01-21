# README
```hepmc_to_hdf5``` extracts final state particles from *HepMC2*  collider event record files and saves them into a single *hdf5* file in a compact format similar to the R&D dataset of the [LHC Olympics 2020 Anomaly Detection Challenge](https://lhco2020.github.io/homepage/). 

Each event is described by a flattened array of particle 'detector' coordinates in three possible kinematical representations:  

 - ```COMPACT```:  (pT, η, φ, pT, η, φ, pT, η, φ,...) 
  
 - ```PTEPM```: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)
  
 - ```EP```:    (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)
 
The event arrays are zero padded to a constant size *M*. The padding size *M* is fixed by the event with the largest number of particles in the sample. The truth label of each hepmc file can be appended at the end of each event array. The complete dataset is a numpy array of stacked events with shape *(Nevents, M)*, or *(Nevents, M+1)* if truth labels are  provided. Basic information about the data (shape, number of signal and background events, dtype, etc) are stored as dataset attributes. 

***TODO: include vertex information (x,y,z,ct) and particle ID.*** 

# Requirements: 
- h5py
- pyjet

# Usage:
```bash
hepmc_to_hdf5.py files [files ...] [-h] [--truth TRUTH ...] [--nevents NEVENTS ...] [--nparts NPARTS] [--output OUTPUT] [--dtype DTYPE] [--gzip] [--chunks CHUNKS]       
```

optional arguments:

 - ```--help,-h```: help message and exit
 - ```--truth,-t TRUTH [TRUTH...]```: truth level bit for each hepmc file
 - ```--nevents,-N NEVENTS [NEVENTS...]```: max event number for each hepmc file
 - ```--nparts,-n NPARTS```: keeps the NPARTS leading particles in each event with zero-padding
 - ```--output,-o OUTPUT```: name of output file
 - ```--dtype,-d, DTYPE```: choose data types: COMPACT, PTEPM, EP 
 - ```--gzip, -gz```: compress h5 output
 - ```--chunks,-k CHUNKS```: data chunk shape when saving to h5 file

# Example:

Running
```bash
python hepmc_to_hdf5.py events_1.hepmc events_2.hepmc events_3.hepmc --truth 1 0 0 --nevents 10 100 120 --nparts 700 --output events.h5 --dtype PTEPM
```
saves into a single file *events.h5*: 
-  10 *signal* events from *events_1.hepmc*
- 100 *background* events from *events_2.hepmc*
- 120 *background* events from *events_3.hepmc*

where each event consists of the leading 700 particles, ordered by pT, in the format *(pT, η, φ, M)*. To omit truth level information from the output, simply drop the ```--truth``` argument from above. If the argument ```--nevents``` is not called, then *all* events from each hepmc file are saved.  
