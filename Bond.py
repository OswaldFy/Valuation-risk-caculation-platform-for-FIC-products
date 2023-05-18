import numpy as np
from scipy.optimize import fsolve
import utils
from utils import utils_methods

class conBond:
    def __init__(self, name, id, issuer, rating, direction, notional, dPrice, couponRate, baseDate, startDate, endDate) -> None:
        self.name = name
        self.id = id
        self.issuer = issuer
        self.rating = rating
        self.direction = direction

        self.baseDate = baseDate
        self.startDate = startDate
        self.endDate = endDate
        
        self.notional = notional
        self.cPrice = None
        self.dPrice = dPrice
        self.accural = None

        self.parYield = None
        self.couponRate = couponRate
        self.couponP = None
        self.repoFactor = None
        
        self.couponDates = None
        
        self.swapZero = None
        self.bondZero = None
        self.cIndex = None
        self.isRepo = None
        
        self.irDelta = None
        self.csDelta = None
    
    def dirtyPrice(self):  
        '''
        compute dirty price of current bond
        '''  
        valTemp = 0
        
        for i in range(self.couponDates.minIndex, self.couponDates.maxIndex):
            valTemp1 = self.couponDates.getValue(i+1)
            
            valTemp += self.couponP * self.bondZero.getZeroAdjustment(valTemp1) \
                * self.swapZero.getDF(valTemp1) * np.exp(-self.repoFactor * (valTemp1 - self.baseDate).days / 365)

        valTemp += self.notional * self.bondZero.getZeroAdjustment(self.couponDates.getValue(self.couponDates.maxIndex)) \
                * self.swapZero.getDF(self.couponDates.getValue(self.couponDates.maxIndex)) * \
                np.exp(-self.repoFactor * (self.couponDates.getValue(self.couponDates.maxIndex) - self.baseDate).days / 365)

        return valTemp
    
    def computeIRRisk(self):
        baseDirtyPrice = self.dirtyPrice()
        self.irDelta = [0] * 10
        for i in range(10):
            self.swapZero.applyRateShock(i)
            self.swapZero.buildCurve()

            self.irDelta[i] = (self.dirtyPrice() - baseDirtyPrice) / 0.0001
            self.swapZero.removeRateShock(i)
            self.swapZero.buildCurve()
    
    def computeCSRisk(self):
        baseDirtyPrice = self.dirtyPrice()
        self.csDelta = [0] * 5
        for i in range(5):
            self.bondZero.applyzRateShock(i)

            self.csDelta[i] = (self.dirtyPrice() - baseDirtyPrice) / 0.0001
            self.bondZero.removezRateShock(i)

    def exportIRRisk(self, inputI):
        return self.irDelta[inputI]
    
    def exportCSRisk(self, inputI):
        return self.csDelta[inputI]
    
    def computeRepo(self):
        
        repoFactor = 0
        
        ABSERR = 0.0000000001
        RMIN = -5
        RMAX = 5
        R1GUESS = 0.0001

        solver = self
        self.isRepo = True
        self.repoFactor = fsolve(solver.eval, 0)
        
    def generateCouponDates(self):
        '''
        generate coupon dates
        update bond info
        calculate acurred interest
        '''
        self.couponDates = utils_methods.generateDates(self.startDate, self.endDate, '6M', 'F', 'NA', 'ACT/ACT')
        self.couponP = self.notional * self.couponRate / 2
        lastCouponDate = utils_methods.DateAdd('M', -6, self.couponDates.getValue(1))
        self.accural = self.couponP * (self.couponDates.getValue(0)-lastCouponDate).days / \
                        (self.couponDates.getValue(1) - lastCouponDate).days
        self.repoFactor = 0
        self.isRepo = False

    def eval(self, x):
        if self.isRepo == True:
            self.repoFactor = x
        else:
            self.bondZero.applyzRate(self.cIndex, x)

        valTemp = 0
        
        for i in range(self.couponDates.minIndex, self.couponDates.maxIndex):
            valTemp1 = self.couponDates.getValue(i+1)
            
            valTemp += self.couponP * self.bondZero.getZeroAdjustment(valTemp1) \
                * self.swapZero.getDF(valTemp1) * np.exp(-self.repoFactor * (valTemp1 - self.baseDate).days / 365)

        valTemp += self.notional * self.bondZero.getZeroAdjustment(self.couponDates.getValue(self.couponDates.maxIndex)) \
                * self.swapZero.getDF(self.couponDates.getValue(self.couponDates.maxIndex)) * \
                np.exp(-self.repoFactor * (self.couponDates.getValue(self.couponDates.maxIndex) - self.baseDate).days / 365)
        
        if self.isRepo == True:
            return self.dPrice - valTemp
        else:
            return self.cPrice - valTemp + self.accural


class conzCurve:
    def __init__(self, name, curr, baseDate) -> None:
        self.name = name
        self.curr = curr

        self.baseDate = baseDate
        
        self.minIndex = None
        self.maxIndex = None
        self.dateList = None

        self.dates = None
        self.rates = None
        self.zRates = None
    
    def getDate(self, inputI):
        return self.dates[inputI]
    
    def applyRateShock(self, inputI):
        self.rates[inputI] = self.rates[inputI] + 0.0001
    
    def removeRateShock(self, inputI):
        self.rates[inputI] = self.rates[inputI] - 0.0001

    def getRate(self, inputI):
        return self.rates[inputI]
    
    def getZeroRate(self, inputI):
        return self.zRates[inputI]

    def setup(self, inputDates, inputRates):
        
        # TODO: define i,j
        self.minIndex = 0
        self.maxIndex = len(inputDates) - 1
        
        self.dates = []
        self.rates = []
        self.zRates = []
        self.dateList = utils.conOrderedList()
        for i in range(self.maxIndex+1):
            self.dates.append(inputDates[i])
            self.rates.append(inputRates[i])
            self.zRates.append(0)
            self.dateList.Add(self.dates[i])

        self.dateList.Shrink()

    def getDF(self,inputDate):
        if inputDate <= self.dates[self.minIndex]:
            if inputDate < self.baseDate:
                return 0
            else:
                return np.exp(-self.zRates[self.minIndex] * (inputDate - self.baseDate).days/365)
        elif inputDate > self.dates[self.maxIndex]:
            return np.exp(-self.zRates[self.maxIndex] * (inputDate - self.baseDate).days/365)
        else:
            iTemp = self.dateList.index(inputDate)
            valTemp1 = self.zRates[iTemp - 1] + (self.zRates[iTemp] - self.zRates[iTemp-1]) \
                /(self.dates[iTemp] - self.dates[iTemp-1]).days * (inputDate - self.dates[iTemp-1]).days
            return np.exp(-valTemp1 * (inputDate - self.baseDate).days / 365)

    def applyzRate(self, i, x):
        self.zRates[i] = x

    def buildCurve(self):
        numofSwap = self.maxIndex - self.minIndex + 1
        allSwaps = []
        for i in range(numofSwap):
            swap = conIRSwap(self.baseDate, self.dates[i], self.rates[i], i, self)
            swap.generateAccural()
            allSwaps.append(swap)
        
        ABSERR = 0.0000000000001
        RMIN = 0
        RMAX = 10
        R1GUESS = 0.0001

        r = R1GUESS
        for i in range(numofSwap):
            solver = allSwaps[i]
            result = fsolve(solver.eval, 0)
            self.zRates[i] = result

class conCzCurve:
    def __init__(self, name, curr, baseDate) -> None:
        self.name = name
        self.curr = curr

        self.baseDate = baseDate
        
        self.minIndex = None
        self.maxIndex = None
        self.dateList = None

        self.swapZeroMe = None

        self.dates = None
        self.rates = None
        self.zRates = None
    
    def getDate(self, inputI):
        return self.dates[inputI]
    
    def applyzRateShock(self, inputI):
        self.zRates[inputI] = self.zRates[inputI] + 0.0001
    
    def removezRateShock(self, inputI):
        self.zRates[inputI] = self.zRates[inputI] - 0.0001

    def getRate(self, inputI):
        return self.rates[inputI]
    
    def getZeroRate(self, inputI):
        return self.zRates[inputI]

    def setup(self, inputDates, inputRates):
        
        # TODO: define i,j
        self.minIndex = 0
        self.maxIndex = len(inputDates) - 1
        
        self.dates = []
        self.rates = []
        self.zRates = []
        self.dateList = utils.conOrderedList()
        for i in range(self.maxIndex+1):
            self.dates.append(inputDates[i])
            self.rates.append(inputRates[i])
            self.zRates.append(0)
            self.dateList.Add(self.dates[i])

        self.dateList.Shrink()

    def getZeroAdjustment(self,inputDate):
        if inputDate <= self.dates[self.minIndex]:
            if inputDate <= self.baseDate:
                return 1
            else:
                return np.exp(-self.zRates[self.minIndex] * (inputDate - self.baseDate).days/365)
        elif inputDate > self.dates[self.maxIndex]:
            return np.exp(-self.zRates[self.maxIndex] * (inputDate - self.baseDate).days/365)
        else:
            iTemp = self.dateList.index(inputDate)
            valTemp1 = self.zRates[iTemp - 1] + (self.zRates[iTemp] - self.zRates[iTemp-1]) \
                /(self.dates[iTemp] - self.dates[iTemp-1]).days * (inputDate - self.dates[iTemp-1]).days
            return np.exp(-valTemp1 * (inputDate - self.baseDate).days / 365)

    def applyzRate(self, i, x):
        self.zRates[i] = x

    def buildCurve(self):
        numofBonds = self.maxIndex - self.minIndex + 1
        allBonds = []
        for i in range(numofBonds):
            bond = conBond(None, None, None, None, None, 100, None, self.rates[i], self.baseDate, self.baseDate, self.dates[i])
            bond.cPrice = 100
            bond.cIndex = i
            bond.bondZero = self
            bond.swapZero = self.swapZeroMe
            bond.generateCouponDates()
            allBonds.append(bond)
        
        ABSERR = 0.0000000000001
        RMIN = 0
        RMAX = 10
        R1GUESS = 0.0001

        r = R1GUESS
        for i in range(numofBonds):
            solver = allBonds[i]
            result = fsolve(solver.eval, 0)
            self.zRates[i] = result

class conIRSwap:
    def __init__(self, startDate, endDate, rate, cIndex, discountCurve) -> None:
        self.startDate = startDate
        self.endDate = endDate
        self.rate = rate
        self.cIndex = cIndex
        self.discountCurve = discountCurve
        self.dates = None
        self.accural = None

    def eval(self, x):
        self.discountCurve.applyzRate(self.cIndex, x)

        valTemp = 0
        for i in range(self.dates.minIndex, self.dates.maxIndex):
            valTemp += self.accural[i] * self.discountCurve.getDF(self.dates.getValue(i+1))
        valTemp = 1 - self.discountCurve.getDF(self.endDate) - self.rate * valTemp
        return valTemp
        
    def generateAccural(self):
        self.dates = utils_methods.generateDates(self.startDate, self.endDate, '3M', 'F', 'NA', 'ACT/360')
        
        self.accural = [0] * self.dates.maxIndex
        for i in range(self.dates.minIndex, self.dates.maxIndex):
            self.accural[i] += (self.dates.getValue(i+1)-self.dates.getValue(i)).days/360
