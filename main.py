import numpy as np
import pandas as pd
from Bond import conBond
from Bond import conzCurve
from Bond import conCzCurve
from data import import_data

class BuildAllCurves:

    def __init__(self) -> None:
        self.irCurve = None
        self.bondRepoCurve = None

        self.allBondRepoCurves = None
            
    def buildAll(self):
        '''
        build all rating cs curves
        '''
        self.buildIRCurve()

        allBondCurves = []
        valuation_date, currency = _data['cs_all']['valuation date'], _data['cs_all']['currency']
        cs_all_df = _data['cs_all']['data']
        for i in range(7):
            bondCurve = conCzCurve(cs_all_df.columns[i+1], currency, valuation_date)
            dateTemp = cs_all_df['Date'].tolist()
            rateTemp = cs_all_df.iloc[:,i+1].tolist()
            bondCurve.setup(dateTemp, rateTemp)
            bondCurve.swapZeroMe = self.irCurve
            bondCurve.buildCurve()
            allBondCurves.append(bondCurve)
        
        
        ratings = ['AAA','AA','A','BBB','BB','B','CCC']
        self.allBondRepoCurves = {}
        for i in range(7):
            self.allBondRepoCurves[ratings[i]] = allBondCurves[i]

        # OUTPUT
        cs_all_output = pd.DataFrame({'Date': cs_all_df['Date'].tolist()})
        for i in range(7):
            cs_all_output[cs_all_df.columns[i+1]] = [allBondCurves[i].getZeroRate(j) for j in range(5)]

        _results['cs_all'] = cs_all_output
    

    def buildbondRepoCurve(self):
        
        self.buildIRCurve()

        name, valuation_date, currency = _data['cs']['name'], _data['cs']['valuation date'], _data['cs']['currency']
        cs_df = _data['cs']['data']
        self.bondRepoCurve = conCzCurve(name, currency, valuation_date)
        dateTemp = cs_df['Date'].tolist()
        rateTemp = cs_df['ParYield'].tolist()
        self.bondRepoCurve.setup(dateTemp, rateTemp)
        self.bondRepoCurve.swapZeroMe = self.irCurve
        self.bondRepoCurve.buildCurve()

        # OUTPUT
        cs_output = pd.DataFrame({'Date': cs_df['Date'].tolist()})
        cs_output['SwapRate'] = [self.bondRepoCurve.getZeroRate(i) for i in range(5)]

        _results['cs'] = cs_output

        
    def buildIRCurve(self):
        
        name, valuation_date, currency = _data['ir']['name'], _data['ir']['valuation date'], _data['ir']['currency']
        ir_df = _data['ir']['data']
        self.irCurve = conzCurve(name, currency, valuation_date)
        dateTemp = ir_df['Date'].tolist()
        rateTemp = ir_df['SwapRate'].tolist()
        self.irCurve.setup(dateTemp, rateTemp)
        self.irCurve.buildCurve()

        # OUTPUT
        ir_output = pd.DataFrame({'Date': ir_df['Date'].tolist()})
        ir_output['SwapRate'] = [self.irCurve.getZeroRate(i) for i in range(10)]

        _results['ir'] = ir_output


    

def runBondPortfolio(numOfBond):

    # import data
    global _data
    _data = import_data(f'./data.xlsx')
    global  _results
    _results = {}

    allBonds = []
    valuation_date = _data['main']['valuation date']
    main_df = _data['main']['data']
    for i in range(numOfBond):
        tempRow = main_df.iloc[i]
        allBonds.append(conBond(tempRow['Id'], None, tempRow['IssuerId'], tempRow['issuerRating'], tempRow['Long/Short'], \
                                tempRow['Notional (mm)'], tempRow['MTM'], tempRow['Coupon'], \
                                valuation_date, tempRow['IssueDate'], tempRow['maturityDate']))
        
    buildall = BuildAllCurves()
    buildall.buildAll()
    buildall.buildbondRepoCurve()

    dirtyPrice = [0] * numOfBond
    irDelta = [0] * numOfBond
    csDelta = [0] * numOfBond
    for i in range(numOfBond):
        allBonds[i].swapZero = buildall.irCurve
        allBonds[i].bondZero = buildall.allBondRepoCurves[allBonds[i].rating]
        allBonds[i].generateCouponDates()
        allBonds[i].computeRepo()
        dirtyPrice[i] = allBonds[i].dirtyPrice()
        allBonds[i].computeIRRisk()
        irDelta[i] = allBonds[i].irDelta
        allBonds[i].computeCSRisk()
        csDelta[i] = allBonds[i].csDelta

        tempOutput = pd.DataFrame({'Date': [allBonds[i].swapZero.getDate(j) for j in range(10)]})
        tempOutput['irDelta'] = irDelta[i]

        _results[allBonds[i].name + allBonds[i].rating + 'ir'] = tempOutput

        tempOutput = pd.DataFrame({'Date': [allBonds[i].bondZero.getDate(j) for j in range(5)]})
        tempOutput['csDelta'] = csDelta[i]

        _results[allBonds[i].name + allBonds[i].rating + 'cs'] = tempOutput

    oas_output = pd.DataFrame({'Bond': [i.name for i in allBonds], 'DirtyPrice': dirtyPrice,\
                               'oas': [dirtyPrice[i]-allBonds[i].dPrice for i in range(numOfBond)]})
    
    _results['oas'] = oas_output
    
    output()

def output():
    path = f'./results.xlsx'
    writer = pd.ExcelWriter(path, engine = 'xlsxwriter')
    for key in _results.keys():
        _results[key].to_excel(writer, sheet_name = key)
    writer.close()

        

if __name__ == '__main__':
    runBondPortfolio(3)