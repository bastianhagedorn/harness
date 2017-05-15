#!/usr/bin/python3
import subprocess
import os
import sys
import argparse
import errno
import shutil
import time
import configparser
import calendar
import csv
 


### README ###########################################################
# Script to start exploration run for a Lift high-level expression
#
# Requirements:
#       * ParameterRewrite settings need to be in LIFT/highLevel/
#
######################################################################

### ARGPARSER ########################################################
parser = argparse.ArgumentParser( description='Lift exploration utility')
parser.add_argument('--environment', dest='envConf', action='store', default='~/.lift/environment.conf',
        help='environment config. If there is no such file the mkEnvironemnt.sh will be executed.')
#parser.add_argument('--portable', dest='isPortable', action='store_true',
#        help='same as "--environment ../../.lift/environment.conf"')
parser.add_argument('--noEnvironment', dest='noEnv', action='store_true',
        help='do not use any environment.conf.')

parser.add_argument('--clean', dest='clean', action='store_true',
        help='clean all generated folders and log-files')
parser.add_argument('--highLevelRewrite', dest='highLevelRewrite', action='store_true',
        help='run HighLevelRewrite')
parser.add_argument('--memoryMappingRewrite', dest='memoryMappingRewrite', action='store_true',
        help='run MemoryMappingRewrite')
parser.add_argument('--parameterRewrite', dest='parameterRewrite', action='store_true',
        help='run ParameterRewrite')
parser.add_argument('--runHarness', dest='runHarness', action='store_true',
        help='run harness recursively')
parser.add_argument('--runAtf', dest='runAtf', action='store_true',
        help='run atf recursively')
parser.add_argument('--executeAtf', dest='executeAtf', action='store_true',
        help='execute with atf and plot results')
parser.add_argument('--fullAtf', dest='fullAtf', action='store_true',
        help='run atf recursively')
parser.add_argument('--findKernels', dest='findKernels', action='store_true',
        help='find the best and worst kernel')
parser.add_argument('--gatherTimesAtf', dest='gatherTimesAtf', action='store_true',
        help='gather runtimes in csv')
parser.add_argument('--gatherTimes', dest='gatherTimes', action='store_true',
        help='gather runtimes in csv')
parser.add_argument('--plot', dest='plot', action='store_true',
        help='plot csv')
parser.add_argument('--full', dest='full', action='store_true',
        help='start full exploration run (rewrite -> execute)')
parser.add_argument('--rewrite', dest='rewrite', action='store_true',
        help='start rewriting process')
parser.add_argument('--execute', dest='execute', action='store_true',
        help='execute and plot kernels')
parser.add_argument('--rerun', dest='rerun', action='store_true',
        help='removeBlacklist + execute')
parser.add_argument('--removeBlacklist', dest='removeBlacklist', action='store_true',
        help='remove blacklisted files to enable re-running things')
parser.add_argument('config', action='store', default='config',
        help='config file')
args = parser.parse_args()

# CONFIG (PARSER) ##################################################
# environment config
def mkEnvironment(path):
    scriptsDir = os.path.dirname(os.path.realpath(__file__))
    subprocess.call([scriptsDir+"/mkEnvironment.sh",path])

#check if environment config exists
envConf = os.path.abspath(os.path.expanduser(args.envConf))
print('[INFO] using environment config '+envConf)
if not args.noEnv:
    if os.path.exists(envConf):
        if not os.path.isfile(envConf):
            sys.exit("[ERROR] environment config already exists but it's not a file.")
    else:
        mkEnvironment(envConf)
        if not os.path.exists(envConf):
            sys.exit("[ERROR] environment config file was not found and could not be created. You can try the --noEnv flag if you don't want to use it.")
    envConfigParser = configparser.RawConfigParser()
    envConfigParser.read(envConf)

# check if config exists
print('[INFO] using explore config '+args.config)
configPath = os.path.expanduser(args.config)
if not os.path.exists(configPath): sys.exit("[ERROR] config file not found!")
configParser = configparser.RawConfigParser()
configParser.read(configPath)



### ENVIRONMENT
if not args.noEnv:
    lift=envConfigParser.get('Path','Lift')
    executor=envConfigParser.get('Path','Executor')
    tuner=envConfigParser.get('Path','Tuner')
    Rscript=envConfigParser.get('Path','Rscript')
    
    clPlattform=envConfigParser.get('OpenCl','Platform')
    clDevice=envConfigParser.get('OpenCl','Device')
    
else: # if there is no environment.conf
    # GENERAL
    lift = configParser.get('General', 'Lift')
    executor = configParser.get('General', 'Executor')
    tuner = configParser.get('General', 'Tuner')
    # R
    Rscript = configParser.get('R', 'Script')
    # openCL
    clPlattform=""
    clDevice=""
    
lift = os.path.normpath(lift)
executor = os.path.normpath(executor)
tuner = os.path.normpath(tuner)
Rscript = os.path.normpath(Rscript)


### GENERAL
expression = configParser.get('General', 'Expression')
inputSize = configParser.get('General', 'InputSize')
name = configParser.get('General', 'Name')
if (name == ""): name = str(calendar.timegm(time.gmtime()))
#secondsSinceEpoch = str(calendar.timegm(time.gmtime()))

### HIGH-LEVEL-REWRITE
depth = configParser.get('HighLevelRewrite', 'Depth')
distance = configParser.get('HighLevelRewrite', 'Distance')
explorationDepth = configParser.get('HighLevelRewrite', 'ExplorationDepth')
repetitions = configParser.get('HighLevelRewrite', 'Repetition')
collection = configParser.get('HighLevelRewrite', 'Collection')
onlyLower = configParser.get('HighLevelRewrite', 'OnlyLower')
highLevelRewriteArgs = " --depth " + depth + " --distance " + distance
highLevelRewriteArgs += " --explorationDepth " + explorationDepth + " --repetition " + repetitions
highLevelRewriteArgs += " --collection " + collection
if(onlyLower == "true"): highLevelRewriteArgs += " --onlyLower"

### MEMORY-MAPPING-REWRITE
unrollReduce= configParser.get('MemoryMappingRewrite', 'UnrollReduce')
global0 = configParser.get('MemoryMappingRewrite', 'Global0')
global01 = configParser.get('MemoryMappingRewrite', 'Global01')
global10 = configParser.get('MemoryMappingRewrite', 'Global10')
global012 = configParser.get('MemoryMappingRewrite', 'Global012')
global210 = configParser.get('MemoryMappingRewrite', 'Global210')
group0 = configParser.get('MemoryMappingRewrite', 'Group0')
group01 = configParser.get('MemoryMappingRewrite', 'Group01')
group10 = configParser.get('MemoryMappingRewrite', 'Group10')
memoryMappingRewriteArgs = ""
if(global0 == "true"): memoryMappingRewriteArgs += " --global0"
if(global01 == "true"): memoryMappingRewriteArgs += " --global01"
if(global10 == "true"): memoryMappingRewriteArgs += " --global10"
if(global012 == "true"): memoryMappingRewriteArgs += " --global012"
if(global210 == "true"): memoryMappingRewriteArgs += " --global210"
if(group0 == "true"): memoryMappingRewriteArgs += " --group0"
if(group01 == "true"): memoryMappingRewriteArgs += " --group01"
if(group10 == "true"): memoryMappingRewriteArgs += " --group10"
if(unrollReduce  == "true"): memoryMappingRewriteArgs += " --unrollReduce"

### PARAMETER-REWRITE
settings = configParser.get('ParameterRewrite', 'Settings')
exploreNDRange = configParser.get('ParameterRewrite', 'ExploreNDRange')
sampleNDRange = configParser.get('ParameterRewrite', 'SampleNDRange')
disableNDRangeInjection = configParser.get('ParameterRewrite', 'DisableNDRangeInjection')
sequential = configParser.get('ParameterRewrite', 'Sequential')
parameterRewriteArgs = " --file " + lift + "/highLevel/" + settings 
if(sequential == "true"): parameterRewriteArgs += " --sequential"
if(disableNDRangeInjection == "true"): parameterRewriteArgs += " --disableNDRangeInjection"
if(exploreNDRange == "true"): parameterRewriteArgs += " --exploreNDRange"
if (exploreNDRange == "true")and not (sampleNDRange == ""): parameterRewriteArgs += " --sampleNDRange " + sampleNDRange

### HARNESSS
harness = configParser.get('Harness', 'Name')
harnessArgs = " " + configParser.get('Harness', 'Args')
if clPlattform != "":
    harnessArgs += ' -p ' + clPlattform
if clDevice != "":
    harnessArgs += ' -d ' + clDevice

### ATF
#atf = configParser.get('ATF', 'atf')
atfCsvHeader = configParser.get('ATF', 'header')
tunerName = configParser.get('ATF', 'tunerName')  

### CSV
#csvHeader = "kernel,time,lsize0,lsize1,lsize2"
csvHeader = configParser.get('CSV', 'Header')
epochTimeCsv = "time_" + inputSize +  "_" + name + ".csv"
timeCsv = "time_" + inputSize + ".csv"
blacklistCsv = "blacklist_" + inputSize + ".csv"

### R
output = expression + "_" + inputSize +  "_" + name + ".pdf"
RscriptArgs = " --file " + epochTimeCsv + " --out " + output

### DIRECTORIES
currentDir = os.getcwd() #current working directory
explorationDir = currentDir + "/" + name
expressionLower = expression + "Lower"
expressionCl = expression + "Cl"
plotsDir = "plots"
scriptsDir = lift + "/scripts/compiled_scripts/"

# HELPER FUNCTIONS #################################################
def printBlue( string ):
    print(bcolors.BLUE + string + bcolors.ENDC)
    return

class bcolors:
    BLUE= '\033[95m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

def silent_mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

# SCRIPT FUNCTIONS #################################################
def clean():
    printBlue("[INFO] Cleaning")
    shutil.rmtree(explorationDir, ignore_errors=True)
    #silentremove("exploration.log")
    #silentremove("generation.log")
    #shutil.rmtree(expression, ignore_errors=True)
    #shutil.rmtree(expressionLower, ignore_errors=True)
    #shutil.rmtree(expressionCl, ignore_errors=True)
    #shutil.rmtree(plotsDir, ignore_errors=True)

def callExplorationStage(rewrite, args):
    printBlue("\n[INFO] Running " + rewrite)
    printBlue("[INFO] args: " + args)
    subprocess.call([scriptsDir + rewrite, args])

def highLevelRewrite():
    args = highLevelRewriteArgs + " " + lift + "/highLevel/" + expression
    callExplorationStage("HighLevelRewrite", args)

def memoryMappingRewrite():
    args = memoryMappingRewriteArgs + " " + expression
    callExplorationStage("MemoryMappingRewrite", args)

def parameterRewrite():
    args = parameterRewriteArgs + " " + expression
    callExplorationStage("ParameterRewrite", args)

def runHarness():
    printBlue("\n[INFO] Running Harness recursively")
    pathToHarness = executor + "/build/" + harness
    shutil.copy2(pathToHarness, expressionCl)
    os.chdir(expressionCl)
    # recursively access every subdirectory and execute harness with harnessArgs
    
    command = "for d in ./*/ ; do (cp " + harness + " \"$d\" && cd \"$d\" && ./"+ harness + harnessArgs + "); done"
    os.system(command)
    os.chdir(explorationDir)

def runAtf():
    printBlue("\n[INFO] Tuning Kernels with Atf recursively")
    pathToTuner = tuner + "/" + tunerName
    shutil.copy2(pathToTuner, expressionCl)
    os.chdir(explorationDir +"/"+ expressionCl)
    #search kernel folders
    for fileName in os.listdir(explorationDir+"/"+expressionCl):
        os.chdir(explorationDir+"/"+expressionCl)
        if os.path.isdir(explorationDir+"/"+expressionCl+"/"+fileName) :
            os.chdir(fileName)
            #copy tuner to the folder
            shutil.copy2(pathToTuner, explorationDir+"/"+expressionCl+"/"+fileName+"/"+tunerName)
            #run atf with every kernel in the folder
            currentKernelNumber=1;
            for fn in os.listdir(explorationDir+"/"+expressionCl+"/"+fileName):
                if fn.endswith(".cl"):
                    atfArg=explorationDir+"/"+expressionCl+"/"+fileName+"/"+fn
                    p= subprocess.Popen([explorationDir+"/"+expressionCl+"/"+fileName+"/"+tunerName, atfArg])
                    p.wait()
                    addKernelNameToRow = "sed -i \""+str(currentKernelNumber)+"s/$/"+str(fn.partition(".")[0])+"/\" results.csv"
                    os.system(addKernelNameToRow)
                    currentKernelNumber+=1
   


def gatherTimes():
    printBlue("\n[INFO] Gather time -- " + epochTimeCsv)
    os.chdir(expressionCl)
    command = "find . -name \"" + timeCsv + "\" | xargs cat >> " + epochTimeCsv
    os.system(command)
    # add header
    addHeader = "sed -i 1i\""+ csvHeader + "\" " + epochTimeCsv
    os.system(addHeader)
    os.chdir(explorationDir)

def gatherTimesAtf():
    printBlue("\n[INFO] Gather time -- " + epochTimeCsv)
    os.chdir(explorationDir+"/"+expressionCl)
    command = "find . -name \""  +"results.csv"+ "\" | xargs cat >> " + epochTimeCsv
    os.system(command)
    # add header
    addHeader = "sed -i 1i\""+ atfCsvHeader + "\" " + epochTimeCsv
    os.system(addHeader)
    os.chdir(explorationDir)

def findBestAndWorst():
    printBlue("\n[INFO] Searching best and worst kernel -- " )
    os.chdir(explorationDir+"/"+expressionCl)
    csvFile= open(epochTimeCsv,"r")
    #lists for the csv values
    rows=[]
    times = []
    kernels = []
    header=0
    #parsing the csv values
    reader=csv.reader(csvFile)
    rownum=0
    for row in reader:
        if rownum ==0: header=row
        else:
            colnum = 0
            for col in row:
                if header[colnum]=="time": times.append(col)
                if header[colnum]=="kernel": kernels.append(col)
                
                colnum+=1
            rows.append(row) 
        rownum += 1
            
    csvFile.close()
    #find the best and worst kernel
    index=0
    bestTime=99999999
    bestKernel=()
    bestKernelIndex=0
    worstKernelIndex=0
    worstTime=0;
    worstKernel=()

    for time in times:
        if(isfloat(time)):
            if bestTime > float(time):
                bestKernel=(kernels[index],float(time))
                bestTime=float(time)
                bestKernelIndex=index
            if worstTime < float(time):
                worstTime=float(time)
                worstKernel=(kernels[index],float(time))
                worstKernelIndex=index
            index+=1;
        else:
            if bestTime > int(time):
                bestKernel=(kernels[index],int(time))
                bestTime=int(time)
                bestKernelIndex=index
            if worstTime < int(time):
                worstTime=int(time)
                worstKernel=(kernels[index],int(time))
                worstKernelIndex=index
            index+=1;   
        
    #print("Best Time:"+str(bestKernel[1])+" Kernel: "+str(bestKernel[0]))
    #print("Worst Time:"+str(worstKernel[1])+" Kernel: "+str(worstKernel[0]))
   #
    os.chdir(explorationDir)
        #save best kernel
    command = "mkdir bestkernel; cd bestkernel ;echo \""+str(header)+"\n"+str(rows[bestKernelIndex])+"\" > kernelinfo.csv ;find "+explorationDir+"/"+expressionCl+" -name '"+bestKernel[0]+"*.cl' -exec cp '{}' "+explorationDir+"/bestkernel/kernel.cl \\;" 
    os.system(command)
        #save lowelevel expression
    os.chdir(explorationDir+"/bestkernel")
    command = "mkdir lowlevelexpression; find "+explorationDir+"/"+expressionLower+" -name '"+getVariable(explorationDir+"/bestkernel/kernel.cl","Low-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/bestkernel/lowlevelexpression/expression.low \\;" 
    os.system(command)
        #save highlevel expression
    os.chdir(explorationDir+"/bestkernel")
    command = "mkdir highlevelexpression; find "+explorationDir+"/"+expression+" -name '"+getVariable(explorationDir+"/bestkernel/kernel.cl","High-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/bestkernel/highlevelexpression/expression.high \\;" 
    os.system(command)
    os.chdir(explorationDir)
        #save worst kernel
    command = "mkdir worstkernel; cd worstkernel; echo \""+str(header)+"\n"+str(rows[worstKernelIndex])+"\" > kernelinfo.csv ;find "+explorationDir+"/"+expressionCl+" -name '"+worstKernel[0]+".cl' -exec cp '{}' "+explorationDir+"/worstkernel/kernel.cl \\;" 
    os.system(command)  
        #save lowelevel expression
    os.chdir(explorationDir+"/worstkernel")
    command = "mkdir lowlevelexpression; find "+explorationDir+"/"+expressionLower+" -name '"+getVariable(explorationDir+"/worstkernel/kernel.cl","Low-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/worstkernel/lowlevelexpression/expression.low \\;" 
    os.system(command)
            #save highlevel expression
    os.chdir(explorationDir+"/worstkernel")
    command = "mkdir highlevelexpression; find "+explorationDir+"/"+expression+" -name '"+getVariable(explorationDir+"/worstkernel/kernel.cl","High-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/worstkernel/highlevelexpression/expression.high \\;" 
    os.system(command)
    saveExplorationMetaInformation()
    
def getVariable(filePath,variableName):
    ffile=open(filePath,'r').read()
    ini=ffile.find(variableName)+(len(variableName)+1)
    rest=ffile[ini:]
    search_enter=rest.find('\n')
    return rest[:search_enter]
    
def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True


def plot():
    printBlue("\n[INFO] Plotting results")
    silent_mkdir(plotsDir)
    shutil.copy2(expressionCl + "/" + epochTimeCsv, plotsDir)
    shutil.copy2(Rscript, plotsDir)
    os.chdir(plotsDir)
    command = "Rscript " + Rscript + RscriptArgs
    os.system(command)
    os.chdir(explorationDir)

def rewrite():
    printBlue("[INFO] Start rewriting process")
    highLevelRewrite()
    memoryMappingRewrite()
    parameterRewrite()

def execute():
    printBlue("[INFO] Execute generated kernels")
    runHarness()
    gatherTimes()
    plot()

def executeAtf():
    printBlue("[INFO] Execute generated kernels")
    runAtf()
    gatherTimesAtf()
    plot()

def rerun():
    printBlue("[INFO] Rerunning:")
    removeBlacklist()
    execute()
    printSummary()
    
#global exploration length in mins
explorationLength = 0

def exploreAtf():
    printBlue("[INFO] Starting exploration -- " + expression)
    start = time.time()
    rewrite()
    executeAtf()
    end = time.time()
    elapsed = (end-start)/60
    global explorationLength
    explorationLength = elapsed
    printBlue("[INFO] Finished exploration! Took " + str(elapsed) + " minutes to execute")
    printSummary()
    findBestAndWorst()

def explore():
    printBlue("[INFO] Starting exploration -- " + expression)
    start = time.time()
    rewrite()
    execute()
    end = time.time()
    elapsed = (end-start)/60
    global explorationLength
    explorationLength = elapsed
    printBlue("[INFO] Finished exploration! Took " + str(elapsed) + " minutes to execute")
    printSummary()
    findBestAndWorst()

def printOccurences(name):
    print(bcolors.BLUE + "[INFO] " + name + ": " + bcolors.ENDC, end='', flush=True)
    find = "find . -name \"" + name + "_" + inputSize + ".csv\" | xargs cat | wc -l"
    os.system(find)
    
def saveExplorationMetaInformation():
    global explorationLength
    os.chdir(explorationDir+"/bestkernel")
    kernelNumber = "cd "+explorationDir+"/"+expressionCl+";  ls */*.cl | wc -l"
    validExecutions = "find . -name \"" + timeCsv + "\" | xargs cat | wc -l"
    allExecutions = "find . -name \"exec_" + inputSize + ".csv\" | xargs cat | wc -l"
    liftBranch = "cd "+lift+" ; git branch | grep -e \"^*\" | cut -d' ' -f 2-"
    liftCommit = "cd "+lift+" ; git rev-parse HEAD"
    arithExpBranch = "cd "+lift+"/lib/ArithExpr ;  git branch | grep -e \"^*\" | cut -d' ' -f 2-"
    arithExpCommit = "cd "+lift+"/lib/ArithExpr  ; git rev-parse HEAD"
    harnessBranch = "cd "+executor+" ; git branch | grep -e \"^*\" | cut -d' ' -f 2-"
    harnessCommit = "cd "+executor+" ; git rev-parse HEAD"
    
    
    saveMetadataHeader = "echo \"explorationTime,kernelNumber,allExecutions,validExecutions,liftBramch,currentLiftCommit,arithExprBranch,currentArithExprCommit,harnessBranch,currentHarnessCommit\" >> metaData.csv"
    saveExplorationTime = "echo \""+str(explorationLength)+",$("+kernelNumber+"),$("+allExecutions+"),$("+validExecutions+"),$("+liftBranch+"),$("+liftCommit+"),$("+arithExpBranch+"),$("+arithExpCommit+"),$("+harnessBranch+"),$("+harnessCommit+")\" >> metaData.csv"
    os.system(saveMetadataHeader)
    os.system(saveExplorationTime)
    
def printSummary():
    #print how many executed runs there are
    os.chdir(expressionCl)
    validExecutions = "find . -name \"" + timeCsv + "\" | xargs cat | wc -l"
    allExecutions = "find . -name \"exec_" + inputSize + ".csv\" | xargs cat | wc -l"
    print(bcolors.BLUE + "[INFO] Executed runs: " + bcolors.ENDC, end='', flush=True)
    command = " echo -n $("+validExecutions+") && echo -n '/' && " + allExecutions
    os.system(command)
    printOccurences("blacklist")
    printOccurences("incompatible")
    printOccurences("invalid")
    printOccurences("timing")
    printOccurences("compilationerror")
    os.chdir(explorationDir)

def removeCsv(name):
    #filename = name + "_" + inputSize + ".csv"
    #printBlue("[INFO] Removing " + filename)
    command = "find . -name \"" + name + "_" + inputSize + ".csv\" | xargs rm"
    os.system(command)

def removeBlacklist():
    printBlue("[INFO] Removing blacklist:")
    os.chdir(expressionCl)
    removeCsv("blacklist")
    removeCsv("incompatible")
    removeCsv("invalid")
    removeCsv("time")
    removeCsv("compilationerror")
    # remove /tmp gold files
    command = "rm /tmp/lift*"
    os.system(command)
    os.chdir(explorationDir)

def setupExploration():
    silent_mkdir(name)
    shutil.copy2(args.config, name)
    os.chdir(name)

# START OF SCRIPT ##################################################
if(args.clean): clean()
else:
    setupExploration()
    if(args.highLevelRewrite): highLevelRewrite()
    if(args.memoryMappingRewrite): memoryMappingRewrite()
    if(args.parameterRewrite): parameterRewrite()
    if(args.runHarness): runHarness()
    if(args.gatherTimes): gatherTimes()
    if(args.plot): plot()
    if(args.rewrite): rewrite()
    if(args.execute): execute()
    if(args.removeBlacklist): removeBlacklist()
    if(args.rerun): rerun()
    if(args.full): explore()
    if(args.runAtf): runAtf()
    if(args.executeAtf): runAtf()
    if(args.fullAtf): exploreAtf()
    if(args.findKernels): findBestAndWorst()
    if(args.gatherTimesAtf): gatherTimesAtf()

os.chdir(currentDir)
