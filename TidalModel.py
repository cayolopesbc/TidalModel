import pandas as pd
import os
import numpy as np
from datetime import datetime
from sklearn import metrics


def harmonicEq(semiH0,phase,period,dt,beta,heightSimu):
    return heightSimu + semiH0*2*np.cos(1/period*(dt + beta)+ np.deg2rad(phase))

def simuTidal(harmonics,meanLvl,beta,simuTime):
    tidalHeights = []
    for dt in range(1,simuTime + 1):
        heightSimu = 0
        for harmonic in harmonics.itertuples():
            semiH0 = float(harmonic[2])/100 # Converte centimetros para metro
            phase  = float(harmonic[3])
            period = float(harmonic[4])
            heightSimu = harmonicEq(semiH0,phase,period,dt,beta,heightSimu)
        tidalHeights.append(heightSimu + meanLvl)
    return tidalHeights

def MSE(obsHeight,heightCalib):
    metric = {}
    heightCalibFilt = pd.DataFrame([], columns = heightCalib.columns)
    aux = 0
    for i in obsHeight.index:
        height = heightCalib[aux:].iloc[heightCalib[aux:].index == i]
        aux = heightCalib.index.get_loc(height.index[0])
        heightCalibFilt = pd.concat([heightCalibFilt,height])
    for col in heightCalib.columns:
        metric[col] = [metrics.mean_squared_error(obsHeight['Nivel'],heightCalibFilt[col])]
    print(metric)
    return pd.DataFrame.from_dict(metric)

def simulation(harmonics, meanLvl, simuDate = None, betaSimu = 0,CalibFlag = False, betaCalibRange = None, obsHeight = None):    
    if CalibFlag:
        heightCalib = {}
        calibDate   = pd.date_range(start = obsHeight.index[0], end = obsHeight.index[-1], freq = "1H")
        for betaCalib in range(betaCalibRange[0],betaCalibRange[-1] + 1):
            heightCalib['beta_'+ str(betaCalib)] = simuTidal(harmonics,meanLvl,betaCalib,len(calibDate))
        heightCalib = pd.DataFrame.from_dict(heightCalib)
        heightCalib['DataHora'] = calibDate
        heightCalib = heightCalib.set_index('DataHora')
        metricsResults = MSE(obsHeight,heightCalib)
    else:
        for i in range(0,len(simuDate)):
            simuDate[i] = datetime.strptime(simuDate[i], '%d/%m/%Y %H:%M')
        simuDate    = pd.date_range(start = simuDate[0], end = simuDate[1], freq = '1H')
        simuTime    = len(simuDate)
        tidalHeight = pd.DataFrame(simuTidal(harmonics,meanLvl,betaSimu,simuTime), columns =['TidalHeight(m)'])
        tidalHeight['DataHora'] = simuDate
        tidalHeight = tidalHeight.set_index('DataHora')

    if CalibFlag:
        print("----Calibracao - Beta-----\n")
        print("Melhor resultado: {}\n".format(metricsResults.describe()[min].name))
        print("Mean Square Error: {}".format(round(metricsResults.describe()[min]['min'],2)))

        return heightCalib, metrics
    else:
        return tidalHeight

def readHarmonics(harmonicFile):
    harmDF  = pd.read_csv(harmonicFile, header = None)
    header  = ['Harmonic','semiH0', 'Phase', 'Period']
    meanLvl = float(harmDF[1][0])
    harmonics  = harmDF.loc[3:,:].reset_index(drop = True)
    harmonics.columns = header
    return meanLvl,harmonics

def readObsHeights(obsFile):
    obsHeight   = pd.read_csv(obsFile)
    obsHeight['DataHora'] = pd.to_datetime(obsHeight['Data'] + obsHeight['Hora'], format = '%m/%d/%Y%H:%M')
    obsHeight = obsHeight.drop(['Data','Hora'], axis = 1)
    return obsHeight.set_index('DataHora')
 

if __name__ == '__main__':

    harmPath = 'C://Users//IPHECO//Desktop//Cayo//Limnologia Computacional'
    harmFile = 'harmonicosMCZ.csv'
    obsFile = 'tabuaMareMCZ.csv'
    simuDate    = ['01/01/2019 00:00','01/02/2019 23:00'] # Data inicial, data final

    meanLvl, harmonics = readHarmonics(os.path.join(harmPath,harmFile))
    obsHeight =  readObsHeights(os.path.join(harmPath,obsFile)).groupby(pd.Grouper(freq = '1H')).first().dropna()

    #tidalHeight = simulation(harmonics, meanLvl, simuDate = simuDate, betaSimu = 0)# Simulacao comum
    calibHeight,metricsResults = simulation(harmonics, meanLvl, CalibFlag = True, betaCalibRange = [1,5], obsHeight = obsHeight) # Simulacao de calibracao








