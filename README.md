# README
```hepmc_to_hdf5``` extracts final state particles (irrespective of particle ID) from *HepMC2* or *HepMC3* files and saves them into a single *hdf5* file in a compact format similar to the R&D dataset of the [LHC Olympics 2020 Anomaly Detection Challenge](https://lhco2020.github.io/homepage/). 

Each event is described by a flattened array of particle 'detector' coordinates in three possible formats:  

 - ```COMPACT```:  (pT, η, φ, pT, η, φ, pT, η, φ,...) 
  
 - ```PTEPM```: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)
  
 - ```EP```:    (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)
 
The event arrays are zero padded to a fixed size *M*, set by the event with the largest number of particles in the sample. The truth label of each hepmc file can be appended at the end of each event array. The complete dataset is a numpy array of stacked events with shape *(Nevents, M)*, or *(Nevents, M+1)* if truth labels are  provided. Basic information about the data (shape, number of signal and background events, dtype, etc) are stored as dataset attributes. 

***TODO: include vertex information (x,y,z,ct) and particle ID.*** 

# Requirements: 
- h5py
- pyjet

# Usage:
```bash
hepmc_to_hdf5.py files [files ...] [-h] [--truth TRUTH ...] [--nevents NEVENTS ...] [--output OUTPUT] [--dtype DTYPE] [--compress COMPRESS] [--chunks CHUNKS]
                      
```
For more information: 
```bash
hepmc_to_hdf5.py --help
```
# Example:

Running,
```bash
python hepmc_to_hdf5.py events_1.hepmc events_2.hepmc events_3.hepmc --truth 1 0 0 --nevents 10 100 120 --output events.h5 --dtype PTEPM
```
saves into a single file *events.h5* 
-  10 *signal* events from *events_1.hepmc*,
- 100 *background* events from *events_2.hepmc*,
- 120 *background* events from *events_3.hepmc*,

in format *(pT, η, φ, M)*. Not calling ```--truth``` above will remove any truth level information from the output, and not calling ```--nevents``` saves all events from each hepmc file.  
