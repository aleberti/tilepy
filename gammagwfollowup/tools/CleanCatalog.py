import numpy as np
from astropy.io import ascii
import matplotlib.pyplot as plt
from astropy.table import Table
import astropy.coordinates as co
from astropy import units as u
import pandas as pd
import collections

def Clean_catalog_from_NaNs_5var(catalog, name):
    
    diste=catalog['col9']
    dist = np.where(np.isnan(diste), -99, diste)
    print('max(dist),min(dist)',max(dist),min(dist))
    countere=0
    for n,i in enumerate(dist):
        if i==-99:
            countere=countere+1
    print(countere,'objects are nans')
    
    #bmag = np.nan_to_num(bmag)
    bmage=catalog['col12']
    bmag = np.where(np.isnan(bmage), 99, bmage)
    counterbmag=0
    for n,i in enumerate(bmag):
        if i==99:
            counterbmag=counterbmag+1
    print(counterbmag,'objects are nans')
    
    
    ze=catalog['col11']
    z = np.where(np.isnan(ze), 99, bmage)
    counterz=0
    for n,i in enumerate(z):
        if i==99:
            counterbmag=counterbmag+1
    print(counterbmag,'objects are nans')
    
    
    print('bmag',bmag.sum())
    print('maximin',max(bmag),min(bmag))
    plt.hist(dist,50, facecolor='green', alpha=0.75)
    
    for n,i in enumerate(dist):
       if i==0:
         dist[n]=-1
    
    for n,i in enumerate(bmag):
       if i==0:
         bmag[n]=99
    
    for n,i in enumerate(z):
        if i==0:
            z[n]=-1
    
    ascii.write([ra, dec,dist,bmag,z], name+'_noNans.txt',names = ['RAJ2000','DEJ2000','Dist','Bmag','z'])

def Plot_Catalog(tcat):
    plt.hist(tcat['Dist'], 100, facecolor='blue', alpha=0.75, log=True)
    plt.xlabel('Distance(Mpc)')
    plt.ylabel('#')
    plt.show()
    
    distCut = tcat['Dist']
    largedistCUT = distCut < 1000
    shortCat = tcat[largedistCUT]
    print('If we make a cut on distance<1000,lenght=', len(shortCat['Dist']))

    # plt.hist(tcat['Dist'],50, facecolor='blue', alpha=0.75,log=True)
    plt.hist(shortCat['Dist'], 50, facecolor='blue', alpha=0.75, log=True)
    plt.xlabel('Distance(Mpc)')
    plt.ylabel('#')
    plt.show()

def PlotValueandError(value, error, string,stringError):
    fig = plt.figure()
    plt.hist(value, 100, facecolor='blue', alpha=0.75, log=True)
    plt.xlabel(string)
    plt.ylabel('#')
    plt.savefig(string+'.png')
    
    fig = plt.figure()
    plt.hist(error, 100, facecolor='blue', alpha=0.75)
    plt.xlabel(stringError)
    plt.ylabel('#')
    plt.savefig(stringError+'.png')
    
    fig = plt.figure()
    plt.plot(value, error,'.')
    plt.savefig(string+'_'+stringError+'.png')
    
    
catName = 'GLADE+test.txt'

#Method1 returns a astropy Table
cat = ascii.read(catName,delimiter=' ')
#print(cat)
ra = cat['col9']
dec = cat['col10']
dist = cat['col33']
Edist = cat['col34']
mass = cat['col36']
Emass = cat['col37']

#mergerRate = np.array(cat['col39'])
#EmergerRate = np.array(cat['col40'])

#PlotValueandError(dist,Edist,'Distance [Mpc]','ErrorDistance[Mpc]')
#PlotValueandError(mass,Emass,'Solar Mass','Error Solar Mass')
#PlotValueandError(mergerRate,EmergerRate, 'Merger Rate', 'Error Merger Rate')
#mass = cat['M*']
#mergerRate = cat['Merger rate']

#Method 2 uses numpy but one needs to handle NaNs
#ra,dec, dist,Edist, mass,Emass, mergerRate, EmergerRate = np.loadtxt(catName, usecols = (9,10,33,34,36,37,39,40), dtype=str, unpack = True)

# NSBH RANGE IS 300–330 Mpc FOR O4 (aLIGO), so I used 500 Mpc as a reasonable cut
ra_C = ra[dist!='null'and dist<500]
dec_C = dec[dist!='null'and dist<500]
dist_C = dist[dist!='null'and dist<500]
mass_C = mass[dist!='null'and dist<500]

print(len(mass),'vs',len(mass_C),'when cleaned')
#print('There are',len(dist[(dist)=='null')]),'NaNs in Distance')
#print('There are',len(mass[(np.isnan(mass)==True)]),'NaNs in mass')
#print('There are',len(mergerRate[(np.isnan(mergerRate)==True)]),'NaNs in mergerRate')


tcat = Table([ra_C,dec_C,dist_C,mass_C], names=('RAJ2000', 'DEJ2000', 'Dist','Mass'))

#print('If we make a cut on nans in distance,lenght=',len(tcat['Dist']))
ascii.write(tcat, 'GLADE+clean.txt',overwrite=True)


#GLADE = Table.read('GLADE_2.2.txt', format='ascii')
