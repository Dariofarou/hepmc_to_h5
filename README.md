# README
```hepmc_to_hdf5``` extracts final state particles from *HepMC2* collider event records and saves them into a single *hdf5* file in a compact format similar to the R&D dataset of the [LHC Olympics 2020 Anomaly Detection Challenge](https://lhco2020.github.io/homepage/). 

Each event is described by a flattened array of particle 'detector' coordinates in three possible kinematical representations:  

 - ```COMPACT```:  (pT, η, φ, pT, η, φ, pT, η, φ,...) 
  
 - ```PTEPM```: (pT, η, φ, M, pT, η, φ, M,pT, η, φ, M,...)
  
 - ```EP```:    (E, px, py, pz, E, px, py, pz, E, px, py, pz,...)
 
In each event array, particles are ordered by transverse momentum (for```COMPACT``` and ```PTEPM```) or energy (for ```EP```), and are zero-padded to a constant size *M*. The padding size *M* can be set by hand (by specyfing the number of leading particles to be kept) or fixed by the event with the largest number of particles in the sample. The truth label of each hepmc file can be appended at the end of each event array. The complete dataset is a numpy array (or a pandas ```DataFrame```) of stacked events with shape *(Nevents, M)*, or *(Nevents, M+1)* if truth labels are  provided. Basic information about the data (shape, number of signal and background events, dtype, etc) are stored as dataset attributes. 

# Requirements: 
- numpy
- pandas
- h5py
- pyjet

# Usage:
```bash
hepmc_to_hdf5.py files [files ...] [-h] [--truth TRUTH ...] [--nevents NEVENTS ...] [--nparts NPARTS] [--output OUTPUT] [--dtype DTYPE] [--gzip] [--chunks CHUNKS]       
```

Optional arguments:

 - ```--help``` or ```-h``` : help message and exit
 - ```--truth``` or ```-t``` : truth level bit per input file
 - ```--nevents``` or ```-N``` : max number of events per input file
 - ```--nparts``` or ```-n``` : max number of leading particles per event with zero-padding
 - ```--pandas``` or ```-pd``` : saves as a pandas ```DataFrame``` (recommenced)
 - ```--output``` or ```-o``` : name of output file
 - ```--dtype``` or ```-d``` : select the data representation: ```COMPACT```, ```PTEPM```, ```EP``` 
 - ```--gzip``` or ``` -gz``` : compress h5 output 
 - ```--chunks``` or ```-k``` : chunk shape when saving to h5 file (may be necessary for very large event files)

# Example:

Running
```bash
python hepmc_to_hdf5.py file_1.hepmc file_2.hepmc file_3.hepmc --pandas --truth 1 0 0 --nevents 10 100 120 --nparts 700 --output combined_events.h5 --dtype COMPACT 
```
saves into a single file the following: 
-  10 *signal* events from *file_1.hepmc*
- 100 *background* events from *file_2.hepmc*
- 120 *background* events from *file_3.hepmc*

where for each event we keep the leading 700 particles (ordered by pT) in the compact format *(pT, η, φ)*. The result is a pandas ```DataFrame ``` with shape *(230, 2101)* stored into *combined_events.h5*.

Dropping the arguments ```--truth```, ```--nevents```, and ```--nparts``` from above yields the following defualt settings: truth-level information is completely omitted, *all* events in each hepmc file are processed, and *all* particles in each event are stored with zero-padding (the padding length is fixed by the event with the largest number of particles in the samples)
