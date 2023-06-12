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
import ligo.skymap.postprocess as lsp


def GetSchedule_ConfigFile(obspar):
    """
    Top level function that is called by the user with specific arguments and creates a folder 
    with the tiling schedules for a single telescope and visibility plots.  

    :param obspar: the set of parameters needed to launch the tiling scheduler
    :type obspar: class ObservationParameters
    """

    URL = obspar.url

    if obspar.alertType == 'gbmpng':
        fitsMap, filename = GetGBMMap(URL)
        if fitsMap is None and filename is None:
            print('The localization map is not available, returning.')
            return
        name = URL.split('/')[-3]
    elif obspar.alertType == 'gbm':
        fitsMap = fits.open(URL)
        if fitsMap is None:
            print('The localization map is not available, returning.')
            return
        filename = URL
        name = URL.split('all_')[1].split('_v00')[0]
    else:
        fitsMap, filename = GetGWMap(URL)
        name = URL.split('/')[-3]

    prob, has3D = Check2Dor3D(fitsMap, filename, obspar.distCut)
    if obspar.LocCut != None:
        ra, dec, a, b, pa, area = lsp.ellipse.find_ellipse(prob, cl=90)
        if (obspar.LocCut== 'loose' and area > 10000) or (obspar.LocCut== 'std' and area > 1000):
            return

    print("===========================================================================================")

    galaxies = obspar.datasetDir + obspar.galcatname
    # cfgFile = "./configs/FollowupParameters.ini"

    ObservationTime = obspar.ObsTime
    outputDir = "%s/%s" % (obspar.outDir, name)

    if has3D:
        dirName = f"{outputDir}/PGallinFoV"
    else:
        dirName = f"{outputDir}/PGinFoV"

    if not os.path.exists(dirName):
        os.makedirs(dirName)

    if has3D:
        print("===========================================================================================")
        print("Starting the 3D pointing calculation with the following parameters\n")
        print("Filename: ", name)
        print("Date: ", obspar.ObsTime)
        print("Previous pointings: ", obspar.PointingsFile)
        print("Catalog: ", galaxies)
        print("Dataset: ", obspar.datasetDir)
        print("Output: ", outputDir)

        SuggestedPointings, cat = PGalinFoV(
            filename, obspar.ObsTime, obspar.PointingsFile, galaxies, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            outfilename = '%s/SuggestedPointings_GalProbOptimisation.txt' % dirName
            ascii.write(SuggestedPointings, outfilename,
                        overwrite=True, fast_writer=False)
            print()
            RankingTimes(obspar.ObsTime, filename, cat, obspar, obspar.alertType, dirName,
                         '%s/SuggestedPointings_GalProbOptimisation.txt' % dirName, obspar.name)
            PointingPlotting(prob, obspar, name, dirName,
                             '%s/SuggestedPointings_GalProbOptimisation.txt' % dirName, obspar.name, filename)
        else:
            FOLLOWUP = False
            print('No observations are scheduled')

    else:

        print("===========================================================================================")
        print("Starting the 2D pointing calculation with the following parameters\n")
        print("Filename: ", name)
        print("Date: ", obspar.ObsTime)
        print("Previous pointings: ", obspar.PointingsFile)
        print("Parameters: ", obspar.cfgFile)
        print("Dataset: ", obspar.datasetDir)
        print("Output: ", obspar.outputDir)

        SuggestedPointings, t0 = PGWinFoV(
            filename, obspar.ObsTime, obspar.PointingsFile, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            outfilename = '%s/SuggestedPointings_2DProbOptimisation.txt' % dirName
            ascii.write(SuggestedPointings, outfilename,
                        overwrite=True, fast_writer=False)
            print()
            RankingTimes_2D(obspar.ObsTime, prob, obspar, ObsTime.alertType, dirName,
                            '%s/SuggestedPointings_2DProbOptimisation.txt' % dirName, obspar.name)
            PointingPlotting(prob, obspar, name, dirName,
                             '%s/SuggestedPointings_2DProbOptimisation.txt' % dirName, obspar.name, filename)
        else:
            FOLLOWUP = False
            print('No observations are scheduled')


def GetSchedule_funcarg(URL, date, datasetDir, galcatname, outDir, targetType, name, Lat, Lon, Height, gSunDown, HorizonSun, gMoonDown,
                        HorizonMoon, gMoonGrey, gMoonPhase, MoonSourceSeparation,
                        MaxMoonSourceSeparation, max_zenith, FOV, MaxRuns, MaxNights,
                        Duration, MinDuration, UseGreytime, MinSlewing, online,
                        MinimumProbCutForCatalogue, MinProbCut, doplot, SecondRound,
                        ZenithWeighting, percentageMOC, ReducedNside, HRnside,distcut,
                        Mangrove):
    """
    Top-level function that is called by the user with specific arguments and creates a folder with the tiling schedules for a single telescope and visibility plots.  
    
    :param URL: The url of the probability fits or  png map
    :type URL: str
    :param date: yhe desired time for scheduling to start 
    :type date: str
    :param datasetDir: Path to the directory containting the datset like the galaxy catalog
    :type datasetDir: str
    :param galcatname: name of the galaxy catalog to be used
    :type galcatname: str
    :param outDir: Path to the output directory where the schedules and plots will eb saved
    :type  outDir: str
    :param cfgFile: Path to the configuration file 
    :type cfgFile: str
    :param Type: The type of the url given. gw if fits GW map, gbm if fits GBM map and gbmpng if PNG GBM map
    :type Type: str
    :return: SuggestedPointings_AstroCOLIBRI
    rtype: Astropy table
    """

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

    prob, has3D = Check2Dor3D(fitsMap, filename, distcut)


    print("===========================================================================================")
    PointingsFile = "False"
    galaxies = datasetDir + galcatname
    # cfgFile = "./configs/FollowupParameters.ini"

    obspar = ObservationParameters()
    obspar.from_args(name, Lat, Lon, Height, gSunDown, HorizonSun, gMoonDown,
                     HorizonMoon, gMoonGrey, gMoonPhase, MoonSourceSeparation,
                     MaxMoonSourceSeparation, max_zenith, FOV, MaxRuns, MaxNights,
                     Duration, MinDuration, UseGreytime, MinSlewing, online,
                     MinimumProbCutForCatalogue, MinProbCut, doplot, SecondRound,
                     ZenithWeighting, percentageMOC, ReducedNside, HRnside,
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

        SuggestedPointings, cat = PGalinFoV(
            filename, ObservationTime, PointingsFile, galaxies, obspar, dirName)

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

        SuggestedPointings, t0 = PGWinFoV(
            filename, ObservationTime, PointingsFile, obspar, dirName)

        print(SuggestedPointings)
        print("===========================================================================================")
        print()

        if (len(SuggestedPointings) != 0):
            FOLLOWUP = True
            df = SuggestedPointings.to_pandas()
            table_dict = df.to_dict()
            table_dict["event_name"] = name
            SuggestedPointings_AstroCOLIBRI = json.dumps(table_dict)
            print()
            return SuggestedPointings_AstroCOLIBRI
        else:
            FOLLOWUP = False
            print('No observations are scheduled')
            return None
