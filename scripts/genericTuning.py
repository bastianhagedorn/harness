import calendar
import csv
import errno
import json
import os
import shutil
import subprocess
import sys
import time
#kernletuning is an execution module so we can use it as any other execution module using the executionModule api


### Module attributes ###
#Note: Inside functions We can read these without any problems but if we want to assign them, we need to explicitly tell the function scope that this variable is not local.
#Also note: these can be accessed from the outside of the module but one should not do this.
_ready = False
#environment
    #Paths
_lift = None
_atf = None
_tuner = None
    #openCL
_clPlattform = None
_clDevice = None

#general
_expression = None
_name = None
_inputSize = None
_cwd = None
_explorationDir = None
_expressionLower = None
_liftScripts = None
_expressionCl = None

#atf
_atfCsvHeader = None
_tunerName = "genericLiftKernel"



### public API ###
#void init(ConfigParser envConf, ConfigParser explorationConf, String envConfPath, String explorationConfPath)
#void clean()
#void run()
#void rerun()
#void gatherTimes()
#void findKernels()
#void requiredRewrites()

#Initializes the module
def init(envConf, explorationConf, envConfPath, explorationConfPath):
    print("Modul wird initiatlisiert")
    global _lift, _atf, _tuner, _clPlattform, _clDevice
    global _expression, _name, _inputSize, _cwd, _explorationDir, _expressionLower, _expressionCl, _liftScripts
    global _atfCsvHeader
    global _ready
    if(_ready): return
    #read the environment values required for this module to work
    _lift = os.path.normpath(envConf['Path']['Lift'])
    _atf = os.path.normpath(envConf['Path']['Atf'])
    _tuner = os.path.normpath(envConf['Path']['Tuner'])
    _clPlattform = envConf['OpenCL']['Platform']
    _clDevice = envConf['OpenCL']['Device']
    
    #read the explore values required for this module to work
    _expression = explorationConf['General']['Expression']
    _name = explorationConf['General']['Name']
    if (_name == ""): _name = str(calendar.timegm(time.gmtime()))
    _inputSize = explorationConf['General']['InputSize']

    _cwd = os.getcwd()
    _explorationDir = _cwd + "/" + _name
    _expressionLower = _expression + "Lower"
    _expressionCl = _expression + "Cl"
    _liftScripts = _lift + "/scripts/compiled_scripts"

    _atfCsvHeader = explorationConf['ATF']['Header']
    
    
    
    #module is ready to use now
    _ready = True

#cleans the files created by the last execution    
def clean():
    print("Warning! Cleaning not tested yet!")
    #search kernel folders
    clDir = _explorationDir + "/" + _expressionCl
    for fileName in os.listdir(clDir):
        if filenName.endswith(".csv"):
            #clean gathered times csv
            silentremove(clDir + "/" + fileName)
        elif os.path.isdir(clDir + "/" + fileName):
            #remove tuner from the folder
            silentremove(clDir + "/" + fileName + "/" + tunerName)
            #remove results.csv
            silentremove(clDir + "/" + fileName + "/results.csv")

            

#runs the exectution
def run():
  print("Warning! Exectution is not tested yet!")
  _checkState()
  printBlue("\n[INFO] Tuning OpenCL kernels with atf -- ")
  silent = bool(False)
  #args in some case not initialized
  #if(args.silentExecution): 
  #    silent = bool(True)
  #    printBlue("[INFO] Running in silent mode\n")
  
  print("using tuner " + _tuner + "/" + _tunerName)
      
  kernelNumber = countGeneratedKernels()         
  executedKernels = 1   
  
  #prepare the tuning
  tunerDir = _explorationDir + '/atf'
  silent_mkdir(tunerDir)
  print('copying tuner to ' + tunerDir+'/'+_tunerName)
  shutil.copy2(_tuner + "/" + _tunerName, tunerDir+'/'+_tunerName)
  
  timesCsvFile = open(tunerDir+'/times.csv','w')
  timesCsvWriter = csv.writer(timesCsvFile)
  #TODO This header won't match the contents when we tune more than gs/ls
  timesCsvWriter.writerow(['time','unknown0','unknown1','unknown2','glsize0','lsize0','kernel'])
  
  
  #enter each cl expression dir
  for fileName in os.listdir(_explorationDir + "/" + _expressionCl):
    if os.path.isdir(_explorationDir + "/" + _expressionCl + "/" + fileName):
      expressionDir=_explorationDir + "/" + _expressionCl + "/" + fileName
      #run atf with every kernel in the folder
      #for each file in that dir check if it's an openCL file
      for clKernel in os.listdir(expressionDir):
        clKernelPath=expressionDir + '/' + clKernel
        if os.path.isfile(clKernelPath) and clKernel.endswith('.cl'):
          
          if(silent):
            stdout=subprocess.FNULL
            stderr=subprocess.STDOUT
            sys.stdout.write("Progress: {}/{}   \r".format(executedKernels, kernelNumber))
            sys.stdout.flush()
          else:
            stdout=None
            stderr=None               
          
          p = subprocess.Popen([tunerDir+'/'+_tunerName, clKernelPath], stdout=stdout, stderr=stderr, cwd=tunerDir)
          p.wait()
          
          print("tunerDir: " + tunerDir)
          resultsCsvFile = open(tunerDir+'/results.csv','r')
          resultsCsvReader = csv.reader(resultsCsvFile)
          
          # results.csv doesn't have a header so we don't need to skip it.
          for line in resultsCsvReader:
            line[0]=str(float(line[0]) * (10**6))
            line[-1]=clKernel
            timesCsvWriter.writerow(line)
          resultsCsvFile.close()
          silentremove(tunerDir+'/results.csv') # we have to remove it otherwise atf will append to it.
          
          executedKernels += 1

        else:
          warn('Not a .cl file: "' + expressionDir + '/' + clKernel + '"')
  
  timesCsvFile.close()
  

  """
  if(silent):
      sys.stdout.write("Progress: {}/{}   \r".format(executedKernels, kernelNumber))
      sys.stdout.flush()
      atfArg = _explorationDir + "/" + _expressionCl + "/" + fileName + "/" + clKernel
      p = subprocess.Popen([_explorationDir + "/" + _expressionCl + "/" + fileName + "/" + _tunerName + " " + atfArg], stdout=subprocess.FNULL, stderr=subprocess.STDOUT, shell=True)
      #eventuell einen fehler hier
  else:
      atfArg = _explorationDir + "/" + _expressionCl + "/" + fileName + "/" + clKernel
      p = subprocess.Popen([_explorationDir + "/" + _expressionCl + "/" + fileName + "/" + _tunerName + " " +  atfArg], shell=True)
  p.wait()
  """
  
  """
  #schreib mal das ergebnis zurueck. GGfs hier anpassen
  addKernelNameToRow = "sed -i \"" + str(currentKernelNumber) + "s/$/" + str(clKernel.partition(".")[0]) + "/\" results.csv"
  os.system(addKernelNameToRow)
  """
#cleans the execution directories and runs the execution afterwards
#Note: I'm not quite sure if we need a rerun function or if we should just always clean the dir before running
def rerun():
  clean()
  run()

#collects the times of the last execution
def gatherTimes():
  _checkState()
  shutil.move(_explorationDir+'/atf/times.csv',_explorationDir+'/' + _expressionCl +'/times.csv')
  
  
  
  """
  print("Warning! gatherTimes is not tested yet!")
  _checkState()
  timesCsv = _explorationDir+'/times.csv'
  #timeCsv = "time_" + str(_inputSize) + ".csv"

  printBlue("\n[INFO] Gathering times to " + timesCsv)

  timeCsvFilePaths = findAll("results.csv", _explorationDir + "/"+_expressionCl)
  #open the gatheredTimeFile in append mode.
  with open(_explorationDir + "/" + _expressionCl + "/" + timesCsv, "a") as gatheredTimeFile:
      #write header first
      gatheredTimeFile.write(_atfCsvHeader)
      for csvfile in timeCsvFilePaths:
          #now write all times from the found timecsv files to the gatheredTimeFile
          with open(csvfile, "r") as currentCsvFile:
              gatheredTimeFile.write(currentCsvFile.read())
  """
       		
#exports the kernels and the tuned parameters of the best and worst kernels
def findKernels():
    printBlue("\n[INFO] Searching best and worst kernel -- ")

    _checkState()

    #open CsvFile "times.csv"
    timesCsvFile = open(_explorationDir+ "/" + _expressionCl + "/" +"times.csv", "r")
    
    #init reader
    reader = csv.reader(timesCsvFile)

    #read in header 
    header = next(reader)

    timeIndex = 0
    kernelIndex = 0
    #get indices of time and kernel 
    for col in header:
        if col == "time":
            break
        timeIndex += 1

    for col in header:
        if col == "kernel":
            break
        kernelIndex += 1

    #init current minTime, current minKernel, minKernelRowNum
    currentMinTime = 0
    currentMinKernel = " "
    minKernelRowNum = 0

    #because we don't know maximum time, init with first kernel and his time found in firstLine after header 
    #save rowNum of first kernel as well
    firstLine = next(reader)
    rowNum = 1

    #get time, kernelname and rowNumber an write it to variables
    colnum = 0
    currentMinTime = firstLine[timeIndex]
    currentMinKernel = firstLine[kernelIndex]
    minKernelRowNum = rowNum

    #get minKernel
    #iterate over rows 
    for row in reader:
        rowNum += 1
        #if time is smaller than current mintime 
        try:
            if float(row[timeIndex]) < float(currentMinTime):
                currentMinTime = row[timeIndex]
                minKernelRowNum = rowNum
                currentMinKernel = row[kernelIndex]
        except IndexError:
            break

    #close timesCsvFile
    timesCsvFile.close()

    
    #get Kernel, save information and code to bestKernelsFolder 

    #get header from times 
    with open(_explorationDir+ "/" + _expressionCl + "/" +"times.csv") as file:
        header = list(file)[0]

    #get row of minKernel from times 
    with open(_explorationDir + "/" + _expressionCl + "/" + "times.csv") as file:
        minKernelRow = list(file)[minKernelRowNum]

    #create folder 
    silent_mkdir(_explorationDir + "/" + "bestkernel")

    #delete old kernelinfo.csv if exists 
    try:
        os.remove(_explorationDir + "/bestkernel/kernelinfo.csv")
    except OSError:
        pass

    #create kernelinfo.csv and write row to file
    with open(_explorationDir + "/bestkernel/kernelinfo.csv", "a") as kernelinfo:
        kernelinfo.write(str(header))
        kernelinfo.write(str(minKernelRow))
    
    #save kernel
    bestKernelFilePath = find(currentMinKernel, _explorationDir + "/" + _expressionCl)
    shutil.copy2(bestKernelFilePath, _explorationDir + "/bestkernel/" + currentMinKernel)

    #save lowLevelExpression
    bestKernelLowLevelHash = getVariable(_explorationDir + "/bestkernel/" + currentMinKernel, "Low-level hash:")
    bestKernelLowLevelExpressionPath = find(bestKernelLowLevelHash, _explorationDir + "/" + _expressionLower)
    shutil.copy2(bestKernelLowLevelExpressionPath, _explorationDir + "/bestkernel/" + bestKernelLowLevelHash) 

    #save highLevelExpression
    bestKernelHighLevelHash = getVariable(_explorationDir + "/bestkernel/" + currentMinKernel, "High-level hash:")
    bestKernelHighLevelExpressionPath = find(bestKernelHighLevelHash, _explorationDir + "/" + _expression)
    shutil.copy2(bestKernelHighLevelExpressionPath, _explorationDir + "/bestkernel/" + bestKernelHighLevelHash)

    return
"""  
    print("Warning! findKernels is not tested yet!")
    _checkState()
    printBlue("\n[INFO] Searching best and worst kernel -- ")
    timesCsvFile = open(_explorationDir+'/times.csv', "r")
    #lists for the csv values
    rows = []
    times = []
    kernels = []
    header = 0
    #parsing the csv values
    timesCsvReader = csv.DictReader(timesCsvFile)
    rownum = 0
    
    # init as very high/very low so we don't need to handle the first value explicitly.
    bestTime=float('inf')
    worstTime=0
    bestConfig=None
    worstConfig=None
    for row in timesCsvReader:
      time=row['time']
      if(time > worstTime):
        worstTime=time
        worstConfig=row
      
      if(time < bestTime):
        bestTime=time
        worstConfig=row
        
    print('best')
    print(bestConfig)
    
    print('worst')
    print(worstConfig)
 """     
 
"""
      if rownum == 0:
        header = row
      else:
        colnum = 0
        for col in row:
          if header[colnum] == "time": times.append(col)
          if header[colnum] == "kernel": kernels.append(col)
          
          colnum += 1
        rows.append(row) 
      rownum += 1
"""
"""  
    timesCsvFile.close()
    #find the best and worst kernel
    index = 0
    bestTime = 99999999
    bestKernel = "null"
    bestKernelIndex = 0
    worstKernelIndex = 0
    worstTime = 0;
    worstKernel = "null"

    for time in times:
        if(isfloat(time)):
            if bestTime > float(time):
                bestKernel = kernels[index]
                bestTime = float(time)
                bestKernelIndex = index
            if worstTime < float(time):
                worstTime = float(time)
                worstKernel = kernels[index]
                worstKernelIndex = index
            index += 1;
        else:
            if bestTime > int(time):
                bestKernel = kernels[index]
                bestTime = int(time)
                bestKernelIndex = index
            if worstTime < int(time):
                worstTime = int(time)
                worstKernel = kernels[index]
                worstKernelIndex = index
            index += 1;   
        

    #save best kernel
    silent_mkdir(_explorationDir + "/bestkernel")
    with open(_explorationDir + "/bestkernel/kernelinfo.csv", "a") as kernelinfo:
       kernelinfo.write(str(header))
       kernelinfo.write(str(rows[bestKernelIndex]))
    #save kernel.cl
    bestKernelFilePath = find(bestKernel + ".cl", _explorationDir + "/" + expressionCl)
    shutil.copy2(bestKernelFilePath, _explorationDir + "/bestkernel/kernel.cl")
    #save expression.low
    bestKernelLowLevelHash = getVariable(explorationDir + "/bestkernel/kernel.cl", "Low-level hash:")
    bestKernelLowLevelExpressionPath = find(bestKernelLowLevelHash, _explorationDir + "/" + _expressionLower)
    shutil.copy2(bestKernelLowLevelExpressionPath, _explorationDir + "/bestkernel/expression.low")
    #save expression.high
    bestKernelHighLevelHash = getVariable(explorationDir + "/bestkernel/kernel.cl", "High-level hash:")
    bestKernelHighLevelExpressionPath = find(bestKernelHighLevelHash, _explorationDir + "/" + _expressionLower)
    shutil.copy2(bestKernelHighLevelExpressionPath, _explorationDir + "/bestkernel/expression.high")

    
    #save worst kernel
    silent_mkdir(_explorationDir + "/worstkernel")
    with open(_explorationDir + "/worstkernel/kernelinfo.csv", "a") as kernelinfo:
       kernelinfo.write(str(header))
       kernelinfo.write(str(rows[worstKernelIndex]))
    #save kernel.cl
    worstKernelFilePath = find(worstKernel + ".cl", _explorationDir + "/" + expressionCl)
    shutil.copy2(worstKernelFilePath, _explorationDir + "/worstkernel/kernel.cl")
    #save expression.low
    worstKernelLowLevelHash = getVariable(explorationDir + "/worstkernel/kernel.cl", "Low-level hash:")
    worstKernelLowLevelExpressionPath = find(worstKernelLowLevelHash, _explorationDir + "/" + _expressionLower)
    shutil.copy2(worstKernelLowLevelExpressionPath, _explorationDir + "/worstkernel/expression.low")
    #save expression.high
    worstKernelHighLevelHash = getVariable(explorationDir + "/worstkernel/kernel.cl", "High-level hash:")
    worstKernelHighLevelExpressionPath = find(worstKernelHighLevelHash, _explorationDir + "/" + _expressionLower)
    shutil.copy2(worstKernelHighLevelExpressionPath, _explorationDir + "/worstkernel/expression.high")
"""

#tells which rewrites are required to run before the execution module can start its work
def requiredRewrites():
    return ("highLevel", "memoryMapping", "parameter")


def _checkState():
    if(not _ready):error('kernelTuning module was not initialised. Call init before using this module')
    elif(not os.path.isdir(_explorationDir + '/' + _expressionCl)):error('The directory ' + _explorationDir + '/' + _expressionCl + ' does not exist. Please run the HighLevel, MemoryMapping and Parameter Rewrites before executing')

########### utility functions ###########

#TODO move to explore util module
def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

#TODO move to explore util module
def silent_mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

#returns all files with filenames == name starting from path.
def findAll(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result

#will find first match
def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

### More helper that should be located in some explorationUtil module
class bcolors:
    BLUE= '\033[95m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def printBlue( string ):
    print(bcolors.BLUE + string + bcolors.ENDC)
    return
    
def info(string):
    print('[INFO] ' + string )

def warn(string):
    print(bcolors.FAIL+'[WARN] ' + bcolors.ENDC + string )

def error(string):
    sys.exit(bcolors.FAIL+'[ERROR] ' + bcolors.ENDC + string)

########### private helper functions ###########
   
def getVariable(filePath, variableName):
    ffile = open(filePath, 'r').read()
    ini = ffile.find(variableName) + (len(variableName) + 1)
    rest = ffile[ini:]
    search_enter = rest.find('\n')
    return rest[:search_enter]
 
def countGeneratedKernels():
    kernelNumber = 0
    explorationDir = _explorationDir
    expressionCl = _expressionCl
    ##count the number of generated kernels
    for fileName in os.listdir(explorationDir + "/" + expressionCl):
        if os.path.isdir(explorationDir + "/" + expressionCl + "/" + fileName):
            for fn in os.listdir(explorationDir + "/" + expressionCl + "/" + fileName):
                if fn.endswith(".cl"):
                    kernelNumber += 1
    return kernelNumber

