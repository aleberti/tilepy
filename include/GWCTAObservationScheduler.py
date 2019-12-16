import sys
sys.path.append('./include')
from GWCTAPointingTools import *
from astropy.table import Table
import datetime
import healpy as hp

from six.moves import configparser
import six
if six.PY2:
  ConfigParser = configparser.SafeConfigParser
else:
  ConfigParser = configparser.ConfigParser

############################################

#              General definitions              #

############################################
iers_url_mirror='ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all'
#iers.IERS.iers_table = iers.IERS_A.open(download_file(iers.IERS_A_URL, cache=True))

iers.IERS.iers_table = iers.IERS_A.open(download_file(iers_url_mirror, cache=True))

def PGWonFoV(filename,InputObservationList,UseObs,ObservationTime0,parameters,dirName):

    # Main parameters

    ##################
    cfg = parameters
    parser = ConfigParser()
    print(parser.read(cfg))
    print(parser.sections())
    section = 'GWProbDensityIntegration-Parameters'

    try:
        max_zenith = int(parser.get(section, 'max_zenith'))
        MaxNights = int(parser.get(section, 'MaxNights'))
        FOV = float(parser.get(section, 'FOV'))
        MaxRuns = int(parser.get(section, 'MaxRuns'))
        MinProbCut = float(parser.get(section, 'MinProbCut'))
        doplot = (parser.getboolean(section, 'doplot'))
        Duration = int(parser.get(section, 'Duration'))
        MinDuration = int(parser.get(section, 'MinDuration'))
        SecondRound = (parser.getboolean(section, 'SecondRound'))
        PercentCoverage = float(parser.get(section, 'PercentCoverage'))
        ReducedNside = int(parser.get(section, 'ReducedNside'))
        HRnside = int(parser.get(section, 'HRnside'))
        UseGreytime = (parser.getboolean(section, 'UseGreytime'))

    except Exception as x:
        print(x)

    print('GWProbDensityIntegration-Parameters:', max_zenith,MaxNights,FOV, MaxRuns, MinProbCut, doplot, Duration, MinDuration, SecondRound,PercentCoverage,ReducedNside,HRnside,UseGreytime)

    ##################

    #Observatory
    if UseObs=='South':
        print('Observed form the',UseObs)
        observatory=CTASouthObservatory()
    else:
        print('Observed from the',UseObs)
        observatory =CTANorthObservatory()
    #observatory =CTANorthObservatory()
    # link to the GW map
    name = filename.split('.')[0].split('/')[-1]
    #if('G' in filename):
    #    names = filename.split("_")
    #    name= names[0]

    random.seed()

    RAarray = []
    DECarray = []
    pixlist = []
    ipixlistHR=[]
    pixlist1 = []
    ipixlistHR1=[]
    P_GWarray = []
    ObservationTimearray= []
    Round = []
    PreDefWindow =[]


    print()
    print('-------------------   NEW LVC EVENT   --------------------')
    print()

    print('Loading GW map from ', filename)
    tprob, distmu, distsigma, distnorm, detectors, fits_id, thisDistance, thisDistanceErr = LoadHealpixMap(filename)
    prob = hp.pixelfunc.ud_grade(tprob,ReducedNside,power=-2)
    nside = ReducedNside

    highres=hp.pixelfunc.ud_grade(prob, HRnside, power=-2)
    # Create table for 2D probability at 90% containment
    rapix, decpix,areapix=Get90RegionPixReduced(prob,PercentCoverage,ReducedNside)
    radecs= co.SkyCoord(rapix,decpix, frame='fk5', unit=(u.deg, u.deg))
    has3D = True
    if (len(distnorm) == 0):
        print("Found a generic map without 3D information")
        # flag the event for special treatment
        has3D = False
    else:
        print("Found a 3D reconstruction")


    #print('----------   NEW FOLLOW-UP ATTEMPT   ----------')
    #SlewingTime=datetime.timedelta(seconds=210)
    ObservationTime=ObservationTime0+datetime.timedelta(seconds=np.float64(InputObservationList['tI'][0]))
    time = NextWindowTools.NextObservationWindow(ObservationTime, observatory)
    #WindowDurations = [15, 17, 20, 23, 27, 33, 40, 50, 64, 85,119,178,296,595,1905]
    WindowDurations= InputObservationList['Interval']
    NightDarkRuns = NextWindowTools.CheckWindowCreateArray(time, observatory, WindowDurations)
    print(NightDarkRuns)
    #NightDarkRuns = NightDarkObservation(ObservationTime0, CTANorthObservatory(),MaxNights,Duration,MinDuration)

    predefWind=InputObservationList['pointingNumber']
    counter=0
    for j in range(0, len(NightDarkRuns)):
        if (len(ObservationTimearray) < MaxRuns):
            ObservationTime = NightDarkRuns[j]
            print('iteration',j)
            ObsBool,yprob=ZenithAngleCut(prob,nside,ObservationTime,MinProbCut,max_zenith,observatory.Location,False)
            if ObsBool:
                # Round 1
                P_GW,TC,pixlist,ipixlistHR = ComputeProbability2D(prob,highres,radecs,ReducedNside,HRnside,MinProbCut,ObservationTime,observatory.Location,max_zenith,FOV,name,pixlist,ipixlistHR,counter,dirName,False,doplot)

                if ((P_GW <= MinProbCut)and SecondRound):
                    #Try Round 2
                    #print('The minimum probability cut being', MinProbCut * 100, '% is, unfortunately, not reached.')
                    yprob1=highres
                    P_GW, TC, pixlist1,ipixlistHR1 = ComputeProbability2D(prob,yprob1, radecs,ReducedNside,HRnside,MinProbCut, ObservationTime,observatory.Location, max_zenith,FOV, name, pixlist1,ipixlistHR1, counter,dirName,False,doplot)
                    if ((P_GW <= MinProbCut)):
                        print('Fail')
                    else:
                        Round.append(2)
                        P_GWarray.append(P_GW)
                        RAarray.append(TC.ra.deg)
                        DECarray.append(TC.dec.deg)
                        ObservationTimearray.append(ObservationTime)
                        PreDefWindow.append(predefWind[j])
                        counter = counter + 1
                else:
                    Round.append(1)
                    P_GWarray.append(P_GW)
                    RAarray.append(TC.ra.deg)
                    DECarray.append(TC.dec.deg)
                    ObservationTimearray.append(ObservationTime)
                    PreDefWindow.append(predefWind[j])
                    counter=counter+1
        else:
            break


    print()
    print("===========================================================================================")
    print()
    print("===========================================================================================")
    print()
    print("Total GW probability covered: ", sum(P_GWarray), "Number of runs that fulfill darkness condition  :",
                  len(NightDarkRuns), "Number of effective pointings: ", len(ObservationTimearray))

    print()
    print("===========================================================================================")
    print()
    # List of suggested pointings
    SuggestedPointings = Table([ObservationTimearray,RAarray,DECarray,P_GWarray,PreDefWindow,Round], names=['Observation Time UTC','RA(deg)','DEC(deg)','PGW','preDefWind','Round'])
    return(SuggestedPointings,ObservationTime0,FOV,nside)


def PGalonFoV(filename,galFile,InputObservationList,UseObs,distance,Edistance_max,Edistance_min,ObservationTime0,parameters,dirName):


    # Main Parameters

    #########################
    cfg = parameters
    parser = ConfigParser()
    print(parser.read(cfg))
    print(parser.sections())
    section = 'GWGalaxyProbabilityIntegrated-Parameters'

    try:
        max_zenith = int(parser.get(section, 'max_zenith'))
        MaxNights = int(parser.get(section, 'MaxNights'))
        FOV = float(parser.get(section, 'FOV'))
        MaxRuns = int(parser.get(section, 'MaxRuns'))
        probCut = float(parser.get(section, 'probCut'))
        MinimumProbCutForCatalogue = float(parser.get(section, 'MinimumProbCutForCatalogue'))
        doplot = (parser.getboolean(section, 'doplot'))
        Duration = int(parser.get(section, 'Duration'))
        MinDuration = int(parser.get(section, 'MinDuration'))
        SecondRound = (parser.getboolean(section, 'SecondRound'))
        FulFillReq_Percentage = float(parser.get(section, 'FulFillReq_Percentage'))
        UseGreytime = (parser.getboolean(section, 'UseGreytime'))

    except Exception as x:
        print(x)

    print('GWGalaxyProbabilityIntegrated - Parameters:', max_zenith, MaxNights, FOV, MaxRuns, probCut, MinimumProbCutForCatalogue, doplot,
          Duration, MinDuration, SecondRound, FulFillReq_Percentage, dirName, UseGreytime)

    #########################
    
    # load galaxy catalog from local file
    # this could be done at the beginning of the night to save time
    cat = LoadGalaxiesSimulation(galFile)
    print('done loading galaxies')

    #Observatory
    if UseObs=='South':
        print('Observed form the',UseObs)
        observatory=CTASouthObservatory()
    else:
        print('Observed from the',UseObs)
        observatory =CTANorthObservatory()
    #name = filename.split('.')[0].split('/')[-1]
    
    #name = "Default"
    #if ('G' in filename):
    #    names = filename.split("_")
    #    name = names[0]
    
    
    #print()
    #print('-------------------   NEW LVC EVENT   --------------------')
    #print()
    
    print('Loading GW map from ', filename)
    prob, distmu, distsigma, distnorm, detectors, fits_id, thisDistance, thisDistanceErr = LoadHealpixMap(filename)
    npix = len(prob)
    nside = hp.npix2nside(npix)
    
    has3D=True
    if(len(distnorm)==0):
        print("Found a generic map without 3D information")
        # flag the event for special treatment
        has3D=False
    else:
        print("Found a 3D reconstruction")

    name = filename.split('.')[0].split('/')[-1]
    # correlate GW map with galaxy catalog, retrieve ordered list
    tGals,sum_dP_dV=GiveProbToGalaxy(prob,cat,distance,Edistance_max,Edistance_min,MinimumProbCutForCatalogue)
    tGals_aux = tGals
    tGals_aux2 = tGals

    P_GALarray = []
    P_GWarray = []
    ObservationTimearray = []
    RAarray = []
    DECarray = []
    alreadysumipixarray1 = []
    alreadysumipixarray2 = []
    PreDefWindow = []
    Round = []

    print('----------   NEW FOLLOW-UP ATTEMPT   ----------')
    print('MaxRuns: ',MaxRuns,'MinimumProbCutForCatalogue: ',MinimumProbCutForCatalogue)
    #SlewingTime=datetime.timedelta(seconds=210)
    ObservationTime=ObservationTime0
    time = NextWindowTools.NextObservationWindow(ObservationTime, observatory)
    WindowDurations= InputObservationList['Interval']
    #WindowDurations = [15, 17, 20, 23, 27, 33, 40, 50, 64, 85,119,178,296,595,1905]
    NightDarkRuns = NextWindowTools.CheckWindowCreateArray(time, observatory, WindowDurations)

    # print('EffectiveRunsTime',len(NightDarkRuns),'being',NightDarkRuns)

    predefWind=InputObservationList['pointingNumber']
    totalProb=0.
    counter=0
    for j in range(0, len(NightDarkRuns)):
        if (len(ObservationTimearray) < MaxRuns):
            ObservationTime = NightDarkRuns[j]
            visible, altaz, tGals_aux = VisibleAtTime(ObservationTime, tGals_aux, max_zenith,observatory.Location)
            
            if (visible):
                
                # select galaxies within the slightly enlarged visiblity window
                visiMask = altaz.alt.value > 90 - (max_zenith+FOV)
                visiGals= tGals_aux[visiMask]
                visiGals = ModifyCatalogue(prob,visiGals,FOV,sum_dP_dV,nside)
                
                mask, minz = FulfillsRequirement(visiGals, max_zenith,FOV,FulFillReq_Percentage,UsePix=False)

                finalGals = visiGals[mask]

                if(finalGals['dp_dV_FOV'][:1] > probCut):
                    # final galaxies within the FoV
                    if ((finalGals['dp_dV_FOV'][:1] < (2 * probCut)) and (sum(P_GWarray) > 0.40) and SecondRound):  # This notes LIGOVirgo type of signal
                        print('probability', finalGals['dp_dV_FOV'][:1])
                        visible, altaz, tGals_aux2 = VisibleAtTime(ObservationTime, tGals_aux2, max_zenith,observatory.Location)
                        if (visible):
                            visiMask = altaz.alt.value > 90 - (max_zenith + FOV)
                            visiGals2 = tGals_aux2[visiMask]
                            visiGals2 = ModifyCatalogue(prob,visiGals2, FOV, sum_dP_dV,nside)
                            
                            mask, minz = FulfillsRequirement(visiGals2, max_zenith,FOV,FulFillReq_Percentage,UsePix=False)

                            finalGals2 = visiGals2[mask]
                            p_gal, p_gw, tGals_aux2, alreadysumipixarray2 = ComputeProbPGALIntegrateFoV(prob,ObservationTime,finalGals2,False,visiGals2,tGals_aux2,sum_dP_dV, alreadysumipixarray2,nside, minz,max_zenith, FOV,counter,name,dirName,doplot)


                            RAarray.append(finalGals2['RAJ2000'][:1])
                            DECarray.append(finalGals2['DEJ2000'][:1])
                            PreDefWindow.append(predefWind[j])
                            Round.append(2)
                    else:
                        #print("\n=================================")
                        #print("TARGET COORDINATES AND DETAILS...")
                        #print("=================================")
                        #print(finalGals['RAJ2000', 'DEJ2000', 'Bmag', 'Dist', 'Alt', 'dp_dV','dp_dV_FOV'][:1])
                        p_gal, p_gw, tGals_aux, alreadysumipixarray1 = ComputeProbPGALIntegrateFoV(prob,ObservationTime,finalGals,False, visiGals,tGals_aux, sum_dP_dV,alreadysumipixarray1,nside, minz,max_zenith, FOV, counter,name,dirName,doplot)
                        RAarray.append(finalGals['RAJ2000'][:1])
                        DECarray.append(finalGals['DEJ2000'][:1])
                        PreDefWindow.append(predefWind[j])
                        Round.append(1)
                    P_GALarray.append(p_gal)
                    P_GWarray.append(p_gw)
                    ObservationTimearray.append(ObservationTime)
                    counter = counter + 1
                    #ObservationTimearrayNamibia.append(Tools.UTCtoNamibia(ObservationTime))
            
                else:
                    #print("Optimal pointing position is: ")
                    #print(finalGals['RAJ2000', 'DEJ2000', 'Bmag', 'Dist', 'Alt', 'dp_dV','dp_dV_FOV'][:1])
                    print("NOT passing the cut on dp_dV_FOV > ",probCut,'as',finalGals['dp_dV_FOV'][:1],visiGals['dp_dV_FOV'][:1] )
        else:
            break

    print()
    print("===========================================================================================")
    print()
    # List of suggested pointings
    SuggestedPointings = Table([ObservationTimearray,RAarray,DECarray ,P_GWarray,P_GALarray,PreDefWindow,Round], names=['Observation Time UTC','RA(deg)','DEC(deg)','PGW','Pgal','preDefWind','Round'])
    return SuggestedPointings,cat,FOV,nside

def PGalonFoV_PixRegion(filename,ObservationTime0):

    # Main Parameters

    ###############################
    max_zenith = 60
    MaxNights = 1
    FOV = 2.5
    MaxRuns = 20  # Maximum number of pointings/runs
    probCut = 0.005
    MinimumProbCutForCatalogue = 0.01
    doplot = False
    FulFillReq_Percentage = 0.75
    NewNside = 64
    PercentCoverage = 0.99
    Duration=5
    MinDuration=1
    ###############################

    # load galaxy catalog from local file
    # this could be done at the beginning of the night to save time
    # galFile='./GLADE_2clean.txt'

    cat = LoadGalaxies(galFile)
    print('done loading galaxies')

    name = filename.split('.')[0].split('/')[-1]

    # name = "Default"
    # if ('G' in filename):
    #    names = filename.split("_")
    #    name = names[0]

    print()
    print('-------------------   NEW LVC EVENT   --------------------')
    print()

    print('Loading GW map from ', filename)
    prob, distmu, distsigma, distnorm, detectors, fits_id, thisDistance, thisDistanceErr = LoadHealpixMap(filename)
    npix = len(prob)
    nside = hp.npix2nside(npix)

    has3D = True
    if (len(distnorm) == 0):
        print("Found a generic map without 3D information")
        # flag the event for special treatment
        has3D = False
    else:
        print("Found a 3D reconstruction")

    # correlate GW map with galaxy catalog, retrieve ordered list
    tGals, sum_dP_dV = CorrelateGalaxies_LVC(prob, distmu, distsigma, distnorm, cat, has3D, MinimumProbCutForCatalogue)
    tGals_aux = tGals
    tGals_aux2 = tGals

    P_GALarray = []
    P_GWarray = []
    ObservationTimearray = []
    RAarray = []
    DECarray = []
    alreadysumipixarray1 = []
    alreadysumipixarray2 = []


    # In case one wants to see if a next round would give us better results..
    # So the time will be j-1
    nextround = False
    Round = []
    print('----------   NEW FOLLOW-UP ATTEMPT   ----------')
    print('MaxRuns: ', MaxRuns, 'MinimumProbCutForCatalogue: ', MinimumProbCutForCatalogue)

    SlewingTime = datetime.timedelta(minutes=210)
    ObservationTime = ObservationTime0 + SlewingTime
    time = NextWindowTools.NextObservationWindow(ObservationTime, CTANorthObservatory())
    WindowDurations = [15, 17, 20, 23, 27, 33, 40, 50, 64, 85,119,178,296,595,1905]
    NightDarkRuns = NextWindowTools.CheckWindowCreateArray(time, CTANorthObservatory(), WindowDurations)

    totalProb = 0.
    n = 0

    ###############################

    # Get the RA & DEC of pixles of the pixels in an enclosed probability region (% precised by PercentCoverage).
    # Reduce these RA DEC to angles in maps with smaller resolution (NewNside)


    pix_ra1, pix_dec1, area = Get90RegionPixReduced(prob, PercentCoverage, NewNside)



    ##############################

    for j in range(0, len(NightDarkRuns)):
        if (len(ObservationTimearray) < MaxRuns):
            ObservationTime = NightDarkRuns[j]
            if (nextround):
                ObservationTime = NightDarkRuns[j - 1]
                nextround = False
            visible, altaz, tGals_aux = VisibleAtTime(ObservationTime, tGals_aux, max_zenith,
                                                      CTANorthObservatory().Location)

            if (visible):

                # select galaxies within the slightly enlarged visiblity window
                visiMask = altaz.alt.value > 90 - (max_zenith + FOV)
                visiGals = tGals_aux[visiMask]

                mask, minz = FulfillsRequirement(visiGals, max_zenith, FOV, FulFillReq_Percentage, UsePix=True)

                finalGals = visiGals[mask]
                visiPix = ModifyCataloguePIX(pix_ra1, pix_dec1, ObservationTime, max_zenith, prob, finalGals, FOV,
                                             sum_dP_dV, nside, NewNside, minz)

                if (visiPix['PIXFOVPROB'][:1] > probCut):
                    n = n + 1
                    # final galaxies within the FoV

                    # print("\n=================================")
                    # print("TARGET COORDINATES AND DETAILS...")
                    # print("=================================")
                    # print(finalGals['RAJ2000', 'DEJ2000', 'Bmag', 'Dist', 'Alt', 'dp_dV','dp_dV_FOV'][:1])
                    p_gal, p_gw, tGals_aux, alreadysumipixarray1 = ComputeProbPGALIntegrateFoV(prob, ObservationTime,
                                                                                               visiPix, True, visiGals,
                                                                                               tGals_aux, sum_dP_dV,
                                                                                               alreadysumipixarray1,
                                                                                               nside, minz, max_zenith,
                                                                                               FOV, name, doplot)
                    RAarray.append(visiPix['PIXRA'][:1])
                    DECarray.append(visiPix['PIXDEC'][:1])
                    Round.append(1)
                    P_GALarray.append(p_gal)
                    P_GWarray.append(p_gw)
                    ObservationTimearray.append(ObservationTime)

                else:
                    print("Optimal pointing position is: ")
                    print(visiPix['PIXRA', 'PIXDEC', 'PIXFOVPROB'][:1])
                    print("NOT passing the cut on dp_dV_FOV > ", probCut)

        else:
            break

    print()
    print("===========================================================================================")
    print()
    # List of suggested pointings
    SuggestedPointings = Table([ObservationTimearray, RAarray, DECarray, P_GWarray, P_GALarray, Round],
                               names=['Observation Time UTC', 'RA(deg)', 'DEC(deg)', 'PGW',
                                      'Pgal', 'Round'], )
    print(SuggestedPointings)
    print("Name", name, "Total GW probability covered: ", sum(P_GWarray), "Total Gal probability covered: ", sum(P_GALarray),
    "Number of runs that fulfill darkness condition  :", len(NightDarkRuns), "Number of effective pointings: ",
    len(ObservationTimearray))
    return SuggestedPointings,cat,area

    #print("===========================================================================================")
    #print()
    #print()

