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
_executor = None
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

#harness
_harness = None
_harnessArgs = None


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
    print("Modul Harness wird initialisiert")
    global _lift, _atf, _tuner, _executor, _harness, _harnessArgs,  _clPlattform, _clDevice
    global _expression, _name, _inputSize, _cwd, _explorationDir, _expressionLower, _expressionCl, _liftScripts
    global _timeCsv, _epochTimeCsv
    global _atfCsvHeader
    global _ready
    if(_ready): return
    #read the environment values required for this module to work
    _lift = os.path.normpath(envConf['Path']['Lift'])
    _atf = os.path.normpath(envConf['Path']['Atf'])
    _tuner = os.path.normpath(envConf['Path']['LowLevelTuner'])
    _executor = os.path.normpath(envConf['Path']['Executor'])
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
    
    _harnessArgs = explorationConf['Harness']['Args']
    _harness = explorationConf['Harness']['Name']

    _timeCsv = "time_" + str(_inputSize) + ".csv"
    _epochTimeCsv = "time_" + str(_inputSize) + "_" + _name + ".csv"
    
    #module is ready to use now
    _ready = True

#cleans the files created by the last execution    
def clean():
    print("Warning! Cleaning not tested yet!")
    #search kernel folders
    for fileName in os.listdir(explorationDir + "/" + expressionCl):
        if filenName.endswith(".csv"):
            #clean gathered times csv
            silentremove(explorationDir + "/" + expressionCl + "/" + fileName)
        if os.path.isdir(explorationDir + "/" + expressionCl + "/" + fileName):
            #remove tuner from the folder
            silentremove(explorationDir + "/" + expressionCl + "/" + fileName + "/" + tunerName)
            for fN in os.listdir(explorationDir + "/" + expressionCl + "/" + fileName):
                if fN.endswith(".csv"):
                    #clean csv files
                    silentremove(explorationDir + "/" + expressionCl + "/" + fileName + "/" + fN)

            

#runs the exectution
def run():
    _checkState()
    printBlue("\n[INFO] Running Harness recursively")
    
    
    silent = bool(False)
    #args in some case not initialized
    # if(args.silentExecution): 
    #    silent = bool(True)
    #    printBlue("[INFO] Running in silent mode\n") 
    pathToHarness = _executor + "/build/" + _harness
    #redirecting stdout of subprocesses to fnull
    FNULL = open(os.devnull, 'w')
    os.chdir(_explorationDir + "/" + _expressionCl)
    
    kernelNumber = countGeneratedKernels()        
    executedKernels = 1 
    # recursively access every subdirectory and execute harness with harnessArgs
    for fileName in os.listdir(_explorationDir + "/" + _expressionCl):
        os.chdir(_explorationDir + "/" + _expressionCl)
        if os.path.isdir(_explorationDir + "/" + _expressionCl + "/" + fileName):
            os.chdir(fileName)
            #copy tuner to the folder
            shutil.copy2(pathToHarness, _explorationDir + "/" + _expressionCl + "/" + fileName + "/" + _harness)
            #run harness with every kernel in the folder
            for fn in os.listdir(_explorationDir + "/" + _expressionCl + "/" + fileName):
                if fn.endswith(".cl"):
                    if silent:
                        sys.stdout.write("Progress: {}/{}   \r".format(executedKernels, kernelNumber))
                        sys.stdout.flush()
                        p = subprocess.Popen([_explorationDir + "/" + _expressionCl + "/" + fileName + "/" + _harness + " " + _harnessArgs], shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
                    else:
                        p = subprocess.Popen([_explorationDir + "/" + _expressionCl + "/" + fileName + "/" + _harness + " " + _harnessArgs], shell=True)
                   
                    p.wait()
                    executedKernels += 1

#cleans the execution directories and runs the execution afterwards
#Note: I'm not quite sure if we need a rerun function or if we should just always prepare 
def rerun():
    _checkState()
    clean()
    run()

#collects the times of the last execution
def gatherTimes():
    print("Warning! gatherTimes is not tested yet!")
    _checkState()
    printBlue("\n[INFO] Gather time -- " + _epochTimeCsv)

    timeCsvFilePaths = findAll(timeCsv, _explorationDir + "/" + _expressionCl)
    #open the gatheredTimeFile in append mode.
    with open(_explorationDir + "/" + _expressionCl + "/" + _epochTimeCsv, "a") as gatheredTimeFile:
        #write header first
        gatheredTimeFile.write(_atfCsvHeader) 
        for csvfile in timeCsvFilePaths:
            #now write all times from the found timecsv files to the gatheredTimeFile
            with open(csvfile, "r") as currentCsvFile:
                gatheredTimeFile.write(currentCsvFile.read())
    
       		
#exports the kernels and the tuned parameters of the best and worst kernels
def findKernels():
    _checkState()
    printBlue("\n[INFO] Searching best and worst kernel -- ")
    explorationDir = _explorationDir
    expressionCl = _expressionCl
    epochTimeCsv = _epochTimeCsv
    
    csvFile = open(explorationDir + "/" + expressionCl + "/" + epochTimeCsv, "r")
    #lists for the csv values
    rows = []
    times = []
    kernels = []
    header = 0
    #parsing the csv values
    reader = csv.reader(csvFile)
    rownum = 0
    for row in reader:
        if rownum == 0: header = row
        else:
            colnum = 0
            for col in row:
                if header[colnum] == "time": times.append(col)
                if header[colnum] == "kernel": kernels.append(col)
                
                colnum += 1
            rows.append(row) 
        rownum += 1
            
    csvFile.close()
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
    


#tells which rewrites are required to run before the execution module can start its work
def requiredRewrites():
    return ("highLevel", "memoryMapping", "parameter")


def _checkState():
    if(not _ready):error('harnessTuning module was not initialised. Call init before using this module')
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
    explorationDir = _explorationDir
    expressionCl = _expressionCl
    kernelNumber = 0
    os.chdir(explorationDir + "/" + expressionCl)
    ##count the number of generated kernels
    for fileName in os.listdir(explorationDir + "/" + expressionCl):
        os.chdir(explorationDir + "/" + expressionCl)
        if os.path.isdir(explorationDir + "/" + expressionCl + "/" + fileName):
            os.chdir(fileName)
            for fn in os.listdir(explorationDir + "/" + expressionCl + "/" + fileName):
                if fn.endswith(".cl"):
                    kernelNumber += 1
    return kernelNumber
