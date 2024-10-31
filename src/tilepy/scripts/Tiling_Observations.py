########################################################################
#    Authors: Monica Seglar-Arroyo, Halim Ashkar,  Fabian Schussler    #
#  Script to obtained the pointing observations of a GW/GRB follow-up  #
#  ------------------------- Version 1.3.0 -------------------------   #
########################################################################

from tilepy.include.ObservationScheduler import GetSchedule
from tilepy.include.PointingTools import ObservationParameters, getdate
import time
import argparse
import os

__all__ = ["Tiling_Observations"]

def Tiling_Observations(obspar):

    GetSchedule(obspar)

def main():

    start = time.time()

    ###########################
    #####    Parsing  ######
    ###########################

    parser = argparse.ArgumentParser(description='Start the LST pointing observation of a GW event')
    parser.add_argument('-skymap', metavar='skymap', default = 'https://gracedb.ligo.org/api/superevents/MS230522j/files/bayestar.fits.gz',
                        help='FITS file with the sky localization, e.g.for GW https://urlpath/Bayestar.fits.gz')
    parser.add_argument('-time', metavar='\"YYYY-MM-DD HH:MM:SS\"', default= "2023-07-27 08:30:10",
                        help='optional: date and time of the event (default: NOW, i.e. %(default)s)')
    parser.add_argument('-i',metavar = 'input path', help='Path to the input datasets (where galaxy cat should be for GW case)', default = "../../dataset/")
    parser.add_argument('-o',metavar = 'output path', help='Path to the output folder',default='./output')
    parser.add_argument('-cfg',metavar = 'config file', help='Config file for the tiling scheduling',default='../config/FollowupParameters_LST.ini')
    parser.add_argument('-galcatName', metavar='galaxy catalog name', default="Gladeplus.h5")
    parser.add_argument('-tiles', metavar='tiles already observed', default= None)

    args = parser.parse_args()
    skymap = args.skymap
    obsTime = getdate(args.time)
    datasetDir = args.i
    outDir = args.o
    cfgFile = args.cfg
    galcatName = args.galcatName
    pointingsFile = args.tiles


    if not os.path.exists(outDir):
        os.makedirs(outDir)

    ################################################

    obspar = ObservationParameters()
    obspar.add_parsed_args(skymap, obsTime, datasetDir, galcatName, outDir, pointingsFile)
    obspar.from_configfile(cfgFile)

    Tiling_Observations(obspar)

    end = time.time()
    print('Execution time: ', end - start)


if __name__ == "__main__":
    main()
