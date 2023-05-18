import datetime
import pandas as pd

class utils_methods:
    
    @staticmethod   
    def generateDates(startDate, endDate, aperiod, dayRoll="F", holCenter='NA', dayCount='ACT/ACT'):
        
        j = aperiod[0]
        strtemp = aperiod[-1]
        
        templist = conOrderedList()
        templist.Add(endDate)
        
        while endDate >= startDate:
            
            valTemp = utils_methods.DateAdd(strtemp, -int(j), endDate)
            endDate = valTemp
            valTemp = utils_methods.NextWorkingDay(valTemp)
            if valTemp > startDate:
                templist.Add(valTemp)
        
        templist.Add(startDate)
        templist.Shrink()
        return templist
            
            
            
    @staticmethod
    def DateAdd(unit, number, dt):
        if unit == "D":
            return dt + pd.DateOffset(days=number)
        elif unit == "M":
            return dt + pd.DateOffset(months=number)
        elif unit == "Y":
            return dt + pd.DateOffset(years=number)

    @staticmethod
    def NextWorkingDay(dt):
        if dt.weekday() == 6:
            return utils_methods.DateAdd("D", 1, dt)
        elif dt.weekday() == 5:
            return utils_methods.DateAdd("D", 2, dt)
        else:
            return dt
        
        
class conOrderedList:
    def __init__(self) -> None:
        self.ChunkSize = 150
        self.minIndex = 0
        self.maxIndex = -1
        
        self.val = [None] * self.ChunkSize
        
    def getValue(self, inputIndex):
        try: 
            return self.val[inputIndex]
        except IndexError:
            print("too big")
            
    def Add(self, x):
        i = self.maxIndex
        while i >= self.minIndex:
            if x == self.val[i]: return
            if x > self.val[i]: break
            i -= 1
        
        for j in range (self.maxIndex, i, -1):
            self.val[j+1] = self.val[j]
            
        self.val[i+1] = x
        self.maxIndex = self.maxIndex + 1

    def index(self, xVal):
        self.minIndex = 0
        nPts = self.maxIndex - self.minIndex + 1

        if nPts < 1: return 

        if xVal < self.val[self.minIndex] or xVal > self.val[self.maxIndex]: return

        jl = self.minIndex -1
        ju = self.maxIndex +1
        while ju - jl > 1:
            jm = int((ju+jl)/2)
            if xVal > self.val[jm]: jl = jm
            else: ju = jm
        
        if ju > self.maxIndex: ju = self.maxIndex
        return ju
    
    def Shrink(self):
        self.val = self.val[self.minIndex: self.maxIndex + 1]