############################################################################
#       Authors: Monica Seglar-Arroyo, Halim Ashkar,  Fabian Schussler     #
#           LST observation scheduler of GBM alerts and GW events          #
############################################################################


from .TilingDetermination import PGWinFoV, PGalinFoV
from .RankingObservationTimes import RankingTimes, RankingTimes_2D
from .PointingPlotting import PointingPlotting
from astropy.coordinates import SkyCoord
from .PointingTools import Tools, LoadGalaxies, getdate, GetGBMMap, GetGWMap, Check2Dor3D, ObservationParameters
from astropy.io import fits, ascii
import time
import healpy as hp
import numpy as np
from astropy import units as u
import datetime
import os
import json



def GetSchedule_confile(URL,date,datasetDir,galcatname,outDir,cfgFile,targetType):
    '''
    Description: Top level function that is called by the user with specific arguments and creates a folder with the tiling schedules for a single telescope and visibility plots.  
    Args:
        URL: the url of the probability fits or  png map
        date: the desired time for scheduling to start 
        datasetDir: Path to the directory containting the datset like the galaxy catalog
        outDir: Path to the output directory where the schedules and plots will eb saved 
        cfgFile: Path to the configuration file 
        Type: The type of the url given. gw if fits GW map, gbm if fits GBM map and gbmpng if PNG GBM map
    '''
    if targetType == 'gbmpng':
        fitsMap, filename = GetGBMMap(URL)
        name = URL.split('/')[-3]
    elif targetType == 'gbm':
        fitsMap = fits.open(URL)
        filename = URL
        name = URL.split('all_')[1].split('_v00')[0]
    else: 
        fitsMap, filename = GetGWMap(URL)
        name = URL.split('/')[-3]

    prob, has3D = Check2Dor3D(fitsMap,filename)

    
    print("===========================================================================================")
    PointingsFile = "False"
    galaxies = datasetDir + galcatname
    #cfgFile = "./configs/FollowupParameters.ini"

    if has3D:

        ObservationTime = date
        outputDir = "%s/%s" % (outDir, name)
        dirName = '%s/PGallinFoV' % outputDir

        if not os.path.exists(dirName):
            os.makedirs(dirName)

        print("===========================================================================================")
        print("Starting the 3D pointing calculation with the following parameters\n")
        print("Filename: ", name)
        print("Date: ", ObservationTime)
        print("Previous pointings: ", PointingsFile)
        print("Catalog: ", galaxies)
        print("Config parameters: ", cfgFile)
        print("Dataset: ", datasetDir)
        print("Output: ", outputDir)
        
        obspar = ObservationParameters()
        obspar.from_configfile(cfgFile)

        SuggestedPointings, cat = PGalinFoV(filename, ObservationTime, PointingsFile, galaxies, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            outfilename = '%s/SuggestedPointings_GalProbOptimisation.txt' % dirName
            ascii.write(SuggestedPointings, outfilename, overwrite=True, fast_writer=False)
            print()
            RankingTimes(ObservationTime, filename, cat, obspar, targetType, dirName,
                         '%s/SuggestedPointings_GalProbOptimisation.txt' % dirName, obspar.name)
            PointingPlotting(prob, obspar, name, dirName,
                             '%s/SuggestedPointings_GalProbOptimisation.txt' % dirName, obspar.name, filename)
        else:
            FOLLOWUP = False
            print('No observations are scheduled')

    else:

        ObservationTime = date
        outputDir = "%s/%s" % (outDir, name)
        dirName = '%s/PGinFoV' % outputDir

        if not os.path.exists(dirName):
            os.makedirs(dirName)

        print("===========================================================================================")
        print("Starting the 2D pointing calculation with the following parameters\n")
        print("Filename: ", name)
        print("Date: ", ObservationTime)
        print("Previous pointings: ", PointingsFile)
        #print("Galaxy Catalog: ", galaxies)
        print("Parameters: ", cfgFile)
        print("Dataset: ", datasetDir)
        print("Output: ", outputDir)
        
        obspar = ObservationParameters()
        obspar.from_configfile(cfgFile)

        SuggestedPointings, t0 = PGWinFoV(filename, ObservationTime, PointingsFile, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            outfilename = '%s/SuggestedPointings_2DProbOptimisation.txt' % dirName
            ascii.write(SuggestedPointings, outfilename, overwrite=True, fast_writer=False)
            print()
            #cat = LoadGalaxies(galaxies)
            RankingTimes_2D(ObservationTime, filename, obspar, targetType, dirName,
                         '%s/SuggestedPointings_2DProbOptimisation.txt' % dirName, obspar.name)
            PointingPlotting(prob, obspar, name, dirName, '%s/SuggestedPointings_2DProbOptimisation.txt' % dirName, obspar.name, filename)
        else:
            FOLLOWUP = False
            print('No observations are scheduled')


def GetSchedule_funcarg(URL, date,datasetDir,galcatname,outDir, targetType, name, Lat, Lon, Height, gSunDown, HorizonSun, gMoonDown,
                 HorizonMoon, gMoonGrey, gMoonPhase, MoonSourceSeparation,
                 MaxMoonSourceSeparation, max_zenith, FOV, MaxRuns, MaxNights,
                 Duration, MinDuration, UseGreytime, MinSlewing, online,
                 MinimumProbCutForCatalogue, MinProbCut, doplot, SecondRound ,
                 FulFillReq_Percentage, PercentCoverage, ReducedNside, HRnside,
                 Mangrove):
    '''
    Description: Top level function that is called by the user with specific arguments and creates a folder with the tiling schedules for a single telescope and visibility plots.  
    Args:
        URL: the url of the probability fits or  png map
        date: the desired time for scheduling to start 
        datasetDir: Path to the directory containting the datset like the galaxy catalog
        outDir: Path to the output directory where the schedules and plots will eb saved 
        cfgFile: Path to the configuration file 
        Type: The type of the url given. gw if fits GW map, gbm if fits GBM map and gbmpng if PNG GBM map
        All the rest of the arguments might be put in one obspar class and can be found in a configuration file
    '''

    if Type == 'gbmpng':
        fitsMap, filename = GetGBMMap(URL)
        name = URL.split('/')[-3]
    elif Type == 'gbm':
        fitsMap = fits.open(URL)
        filename = URL
        name = URL.split('all_')[1].split('_v00')[0]
    else: 
        fitsMap, filename = GetGWMap(URL)
        name = URL.split('/')[-3]

    prob, has3D = Check2Dor3D(fitsMap,filename) 

    print("===========================================================================================")
    PointingsFile = "False"
    galaxies = datasetDir + galcatname
    #cfgFile = "./configs/FollowupParameters.ini"

    obspar = ObservationParameters()
    obspar.from_args(name, Lat, Lon, Height, gSunDown, HorizonSun, gMoonDown,
                 HorizonMoon, gMoonGrey, gMoonPhase, MoonSourceSeparation,
                 MaxMoonSourceSeparation, max_zenith, FOV, MaxRuns, MaxNights,
                 Duration, MinDuration, UseGreytime, MinSlewing, online,
                 MinimumProbCutForCatalogue, MinProbCut, doplot, SecondRound ,
                 FulFillReq_Percentage, PercentCoverage, ReducedNside, HRnside,
                 Mangrove)

    if has3D:

        ObservationTime = date
        outputDir = "%s/%s" % (outDir, name)
        dirName = '%s/PGallinFoV' % outputDir

        if not os.path.exists(dirName):
            os.makedirs(dirName)

        print("===========================================================================================")
        print("Filename: ", name)
        print("Date: ", ObservationTime)
        print("Previous pointings: ", PointingsFile)
        print("Catalog: ", galaxies)
        print("Dataset: ", datasetDir)
        print("Output: ", outputDir)
        

        SuggestedPointings, cat = PGalinFoV(filename, ObservationTime, PointingsFile, galaxies, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            df = SuggestedPointings.to_pandas()
            table_dict = df.to_dict()
            SuggestedPointings_AstroCOLIBRI = json.dumps(table_dict)
            print()
            return SuggestedPointings_AstroCOLIBRI
        else:
            FOLLOWUP = False
            print('No observations are scheduled')
            return None

    else:

        ObservationTime = date
        outputDir = "%s/%s" % (outDir, name)
        dirName = '%s/PGWinFoV' % outputDir

        if not os.path.exists(dirName):
            os.makedirs(dirName)

        print("===========================================================================================")
        print("Filename: ", name)
        print("Date: ", ObservationTime)
        print("Previous pointings: ", PointingsFile)
        print("Catalog: ", galaxies)
        print("Dataset: ", datasetDir)
        print("Output: ", outputDir)
        

        SuggestedPointings, t0 = PGWinFoV(filename, ObservationTime, PointingsFile, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            df = SuggestedPointings.to_pandas()
            table_dict = df.to_dict()
            SuggestedPointings_AstroCOLIBRI = json.dumps(table_dict)
            print()
            return SuggestedPointings_AstroCOLIBRI
        else:
            FOLLOWUP = False
            print('No observations are scheduled')
            return None
