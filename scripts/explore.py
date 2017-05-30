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
import json

#Which module to require depends on the used flag (--atf, --llatf, --harness)
import lowLevelTuning as executionModule
#import kernelTuning as executionModule
#import harnessTuning as executionModule


### README ###########################################################
# Script to start exploration run for a Lift high-level expression
#
# Requirements:
#       * ParameterRewrite settings need to be in LIFT/highLevel/
#
######################################################################

### ARGPARSER ########################################################
parser = argparse.ArgumentParser( description='Lift exploration utility')
parser.add_argument('--environment', dest='envConf', action='store', default='~/.lift/environment.json',
        help='environment config. If there is no such file the mkEnvironemnt.sh will be executed.')
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
parser.add_argument('--silentExecution', dest='silentExecution', action='store_true',
        help='run the execution without output')

parser.add_argument('config', action='store', default='config',
        help='config file')

#TODO flag naming
parser.add_argument('--makeTuner', dest='makeTuner', action='store_true',help='just don\'t use this flag!')
    
#parser.add_argument('--lowLevelAtf', dest='lowLevelAtf', action='store_true',
#        help='run the tuning of low level expressions with atf ccfg')
#parser.add_argument('--atfHarness', dest='atfHarness', action='store_true',
#        help='harness run from atf')   
#parser.add_argument('--atfHarnessDir', action='store', default='store_false',
#        help='explicit dir needed for ccfg execution and cost file generation')

args = parser.parse_args()

# CONFIG (PARSER) ##################################################
# environment config
def mkEnvironment(path):
    scriptsDir = os.path.dirname(os.path.realpath(__file__))
    subprocess.call([scriptsDir+"/mkEnvironment.sh",path])

#check if environment config exists
envConf = os.path.abspath(os.path.expanduser(args.envConf))
print('[INFO] using environment config '+envConf)
if os.path.exists(envConf):
    if not os.path.isfile(envConf):
        sys.exit("[ERROR] environment config already exists but it's not a file.")
else:
    mkEnvironment(envConf)
    if not os.path.exists(envConf):
        sys.exit("[ERROR] environment config file was not found and could not be created.")
json_envFile = open(envConf)
json_envConfig = json.load(json_envFile)


# check if config exists
print('[INFO] using explore config '+args.config)
configPath = os.path.expanduser(args.config)
absoluteConfigPath = os.path.realpath(configPath)
if not os.path.exists(configPath): sys.exit("[ERROR] config file not found!")
#open Json config
json_file = open(absoluteConfigPath)
json_config = json.load(json_file)



### ENVIRONMENT
lift=json_envConfig["Path"]["Lift"]
executor=json_envConfig["Path"]["Executor"]
atf=json_envConfig["Path"]["Atf"]
tuner=json_envConfig["Path"]["Tuner"]
lowLevelTuner=json_envConfig["Path"]["LowLevelTuner"]
Rscript=json_envConfig["Path"]["Rscript"]

clPlattform=json_envConfig["OpenCL"]["Platform"]
clDevice=json_envConfig["OpenCL"]["Device"]

    
lift = os.path.normpath(lift)
executor = os.path.normpath(executor)
tuner = os.path.normpath(tuner)
lowLevelTuner = os.path.normpath(lowLevelTuner)
Rscript = os.path.normpath(Rscript)


### GENERAL
expression = json_config["General"]["Expression"]
inputSize = json_config["General"]["InputSize"]
name = json_config["General"]["Name"]
if (name == ""): name = str(calendar.timegm(time.gmtime()))
#secondsSinceEpoch = str(calendar.timegm(time.gmtime()))

### HIGH-LEVEL-REWRITE
depth = json_config["HighLevelRewrite"]["Depth"]
if (name == ""): name = str(calendar.timegm(time.gmtime()))
distance = json_config["HighLevelRewrite"]["Distance"]
explorationDepth = json_config['HighLevelRewrite']['ExplorationDepth']
repetitions = json_config["HighLevelRewrite"]["Repetition"]
collection = json_config["HighLevelRewrite"]["Collection"]
onlyLower = json_config["HighLevelRewrite"]["OnlyLower"]
highLevelRewriteArgs = " --depth " + str(depth) + " --distance " + str(distance)
highLevelRewriteArgs += " --explorationDepth " + str(explorationDepth) + " --repetition " + str(repetitions)
highLevelRewriteArgs += " --collection " + collection
if(onlyLower == "true"): highLevelRewriteArgs += " --onlyLower"

### MEMORY-MAPPING-REWRITE
unrollReduce= json_config["MemoryMappingRewrite"]["UnrollReduce"]
global0 = json_config["MemoryMappingRewrite"]["Global0"]
global01 = json_config["MemoryMappingRewrite"]["Global01"]
global10 = json_config["MemoryMappingRewrite"]["Global10"]
global012 = json_config["MemoryMappingRewrite"]["Global012"]
global210 = json_config["MemoryMappingRewrite"]["Global210"]
group0 = json_config["MemoryMappingRewrite"]["Group0"]
group01 = json_config["MemoryMappingRewrite"]["Group01"]
group10 = json_config["MemoryMappingRewrite"]["Group10"]
memoryMappingRewriteArgs = ""
if(global0 == True): memoryMappingRewriteArgs += " --global0"
if(global01 == True): memoryMappingRewriteArgs += " --global01"
if(global10 == True): memoryMappingRewriteArgs += " --global10"
if(global012 == True): memoryMappingRewriteArgs += " --global012"
if(global210 == True): memoryMappingRewriteArgs += " --global210"
if(group0 == True): memoryMappingRewriteArgs += " --group0"
if(group01 == True): memoryMappingRewriteArgs += " --group01"
if(group10 == True): memoryMappingRewriteArgs += " --group10"
if(unrollReduce  == True): memoryMappingRewriteArgs += " --unrollReduce"

### PARAMETER-REWRITE
settings = json_config["ParameterRewrite"]["Settings"]
exploreNDRange = json_config["ParameterRewrite"]["ExploreNDRange"]
sampleNDRange = json_config["ParameterRewrite"]["SampleNDRange"]
disableNDRangeInjection = json_config["ParameterRewrite"]["DisableNDRangeInjection"]
sequential = json_config["ParameterRewrite"]["Sequential"]
parameterRewriteArgs = " --file " + lift + "/highLevel/" + settings 
if(sequential == True): parameterRewriteArgs += " --sequential"
if(disableNDRangeInjection == True): parameterRewriteArgs += " --disableNDRangeInjection"
if(exploreNDRange == True): parameterRewriteArgs += " --exploreNDRange"
if (exploreNDRange == True)and not (sampleNDRange == ''): parameterRewriteArgs += " --sampleNDRange " + str(sampleNDRange)

### HARNESSS
harness = json_config["Harness"]["Name"]
harnessArgs = "" + json_config["Harness"]["Args"]
if clPlattform != "":
    harnessArgs += ' -p ' + clPlattform
if clDevice != "":
    harnessArgs += ' -d ' + clDevice

### ATF
atfCsvHeader = json_config["ATF"]["Header"]
tunerName = json_config["ATF"]["TunerName"]

### CSV
#csvHeader = "kernel,time,lsize0,lsize1,lsize2"
csvHeader =json_config["CSV"]["Header"]
epochTimeCsv = "time_" + str(inputSize) +  "_" + name + ".csv"
timeCsv = "time_" + str(inputSize) + ".csv"
blacklistCsv = "blacklist_" + str(inputSize) + ".csv"

### R
output = expression + "_" + str(inputSize) +  "_" + name + ".pdf"
RscriptArgs = " --file " + epochTimeCsv + " --out " + output

### DIRECTORIES
currentDir = os.getcwd() #current working directory
explorationDir = currentDir + "/" + name
expressionLower = expression + "Lower"
expressionCl = expression + "Cl"
plotsDir = "plots"
scriptsDir = lift + "/scripts/compiled_scripts"

# HELPER FUNCTIONS #################################################
#TODO move to explore util module
def printBlue( string ):
    print(bcolors.BLUE + string + bcolors.ENDC)
    return

#TODO move to explore util module
def warn(string):
    print(bcolors.FAIL+'[WARN] ' + bcolors.ENDC + string )
    
#TODO move to explore util module
def info(string):
    print('[INFO] ' + string )

class bcolors:
    BLUE= '\033[95m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#TODO move to explore util module
def clearDir(dirname):
    for f in os.listdir(dirname):
        silentremove(f)

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
    subprocess.call([scriptsDir + "/" + rewrite, args])

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
    
    silent = bool(False)
    if(args.silentExecution): 
        silent = bool(True)
        printBlue("[INFO] Running in silent mode\n")
    
    pathToHarness = executor + "/build/" + harness
    #redirecting stdout of subprocesses to fnull
    FNULL = open(os.devnull, 'w')
    os.chdir(explorationDir +"/"+ expressionCl)
    
    kernelNumber = countGeneratedKernels()        
    executedKernels =1 
    # recursively access every subdirectory and execute harness with harnessArgs
    for fileName in os.listdir(explorationDir+"/"+expressionCl):
        os.chdir(explorationDir+"/"+expressionCl)
        if os.path.isdir(explorationDir+"/"+expressionCl+"/"+fileName) :
            os.chdir(fileName)
            #copy tuner to the folder
            shutil.copy2(pathToHarness, explorationDir+"/"+expressionCl+"/"+fileName+"/"+harness)
            #run harness with every kernel in the folder
            for fn in os.listdir(explorationDir+"/"+expressionCl+"/"+fileName):
                if fn.endswith(".cl"):
                    if silent:
                        sys.stdout.write("Progress: {}/{}   \r".format(executedKernels,kernelNumber) )
                        sys.stdout.flush()
                        p= subprocess.Popen([explorationDir+"/"+expressionCl+"/"+fileName+"/"+harness+" "+harnessArgs], shell=True,stdout=FNULL, stderr=subprocess.STDOUT)
                    else:
                        p= subprocess.Popen([explorationDir+"/"+expressionCl+"/"+fileName+"/"+harness+" "+harnessArgs], shell=True)
                   
                    p.wait()
                    executedKernels+=1

def runHarnessInDir(pathOfDirectory):
    printBlue("\n[INFO] Running Harness with every Kenrel in "+pathOfDirectory)
    
    silent = bool(False)
    if(args.silentExecution): 
        silent = bool(True)
        printBlue("[INFO] Running in silent mode\n")
    
    pathToHarness = executor + "/build/" + harness
    #redirecting stdout of subprocesses to fnull
    FNULL = open(os.devnull, 'w')
    os.chdir(pathOfDirectory)
    

    shutil.copy2(pathToHarness, pathOfDirectory+"/"+harness)
    #run harness with every kernel in the folder
    for fn in os.listdir(pathOfDirectory):
        if fn.endswith(".cl"):
            if silent:
                sys.stdout.write("Progress: {}/{}   \r".format(executedKernels,kernelNumber) )
                sys.stdout.flush()
                p= subprocess.Popen([pathOfDirectory+"/"+harness+" "+harnessArgs], shell=True,stdout=FNULL, stderr=subprocess.STDOUT)
            else:
                p= subprocess.Popen([pathOfDirectory+"/"+harness+" "+harnessArgs], shell=True)

            p.wait()


def generateCostFile(pathOfDirectory):
    printBlue("\n[INFO] Generating cost file in "+pathOfDirectory)
    os.chdir(pathOfDirectory)
    addHeader = "sed -i 1i\""+ csvHeader + "\" " + pathOfDirectory+"/"+timeCsv
    os.system(addHeader)
    csvFile= open(pathOfDirectory+"/"+timeCsv,"r")
    #lists for the csv values
    rows=[]
    times = []
    kernels = []

    #parsing the csv values
    reader=csv.reader(csvFile)
    header=next(reader)
    for row in reader:        
        colnum = 0
        for col in row:
            if header[colnum]=="time": times.append(col)
            colnum+=1
        rows.append(row) 

    csvFile.close()

    bestTime=99999999
    for time in times:
        if bestTime > float(time):
            bestTime=float(time)

    print("COST: "+str(int(bestTime*10000))+"\nPATH: "+currentDir+"/costFile.txt\n")
    #*10000 übergangslösung da atf noch keine floats als cost nimmt
    costfile = open(currentDir+"/costfile.txt",'w+')
    costfile.write(str(int(bestTime*10000)))
    costfile.close()

    

def runAtf():
    printBlue("\n[INFO] Tuning Kernels with Atf recursively")
    silent = bool(False)
    if(args.silentExecution): 
        silent = bool(True)
        printBlue("[INFO] Running in silent mode\n")
    
    #redirecting stdout of subprocesses to fnull
    FNULL = open(os.devnull, 'w')
    pathToTuner = tuner + "/" + tunerName
    os.chdir(explorationDir +"/"+ expressionCl)
    
    kernelNumber = countGeneratedKernels()         
    executedKernels =1         
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
                    if(silent):
                        sys.stdout.write("Progress: {}/{}   \r".format(executedKernels,kernelNumber) )
                        sys.stdout.flush()
                        atfArg=explorationDir+"/"+expressionCl+"/"+fileName+"/"+fn
                        p= subprocess.Popen([explorationDir+"/"+expressionCl+"/"+fileName+"/"+tunerName, atfArg],stdout=FNULL, stderr=subprocess.STDOUT)

                    else:
                        atfArg=explorationDir+"/"+expressionCl+"/"+fileName+"/"+fn
                        p= subprocess.Popen([explorationDir+"/"+expressionCl+"/"+fileName+"/"+tunerName, atfArg])
                    p.wait()
                    addKernelNameToRow = "sed -i \""+str(currentKernelNumber)+"s/$/"+str(fn.partition(".")[0])+"/\" results.csv"
                    os.system(addKernelNameToRow)
                    currentKernelNumber+=1
                    executedKernels+=1
   

def countGeneratedKernels():
    kernelNumber =0
    os.chdir(explorationDir +"/"+ expressionCl)
    ##count the number of generated kernels
    for fileName in os.listdir(explorationDir+"/"+expressionCl):
        os.chdir(explorationDir+"/"+expressionCl)
        if os.path.isdir(explorationDir+"/"+expressionCl+"/"+fileName) :
            os.chdir(fileName)
            for fn in os.listdir(explorationDir+"/"+expressionCl+"/"+fileName):
                if fn.endswith(".cl"):
                    kernelNumber +=1
    return kernelNumber

def gatherTimes():
    printBlue("\n[INFO] Gather time -- " + epochTimeCsv)
    os.chdir(explorationDir+"/"+expressionCl)
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

#TODO check if we still need this
def atfHarness():
    #check if environment config exists #TODO Why should we check this here?
    runDir = args.atfHarnessDir
    print('[INFO] running harness in '+runDir)
    if os.path.exists(runDir):
        if not os.path.isdir(runDir):
            sys.exit("[ERROR] environment config already exists but it's not a dir.")
        #remove times.csv of previous runs
        runHarnessInDir(runDir)
        generateCostFile(runDir)
        #TODO hacky stuff! We have to clear the dir because we call atfHarness for each TP set that gets generated by the atf.
        #     We should not clear the directory here nor we should gather times here.
        
        csvFile = open(runDir+"/"+timeCsv,"r")
        next(csvFile) #skip the first line
        gatheredCsv = open(runDir+"/../"+epochTimeCsv,"a")
        for line in csvFile:
            gatheredCsv.write(line)     
        
        clearDir(runDir)  


#TODO check if we still need this
def lowLevelAtf():
    printBlue("\n[INFO] Tuning low level expressions with atf -- " )
    executedKernels =1         
    #search kernel folders
    for fileName in os.listdir(explorationDir+"/"+expressionLower):
        if os.path.isdir(explorationDir+"/"+expressionLower+"/"+fileName) :
            if(os.path.isfile(explorationDir+"/"+expressionLower+"/"+fileName+"/index")):
                indexFile= open(explorationDir+"/"+expressionLower+"/"+fileName+"/index","r")
                reader=csv.reader(indexFile)
                for row in reader:
                    rowAsString = "".join(row)
                    lowLevelPath = explorationDir+"/"+rowAsString
                    if os.path.isfile(lowLevelPath):
                        lowLevelHash = rowAsString.split("/")[-1]
                        makeAtfScripts(lowLevelPath,lowLevelHash)
                        print("Processing Expression: \""+lowLevelHash+"\"\n")
                        p= subprocess.Popen([ './lowLevelLift' ],cwd=explorationDir+'/atfCcfg')
                        p.wait()
                        
                    else:
                        print("Path was not a file: \""+lowLevelPath+"\"\n")
                #TODO evil hacky code!
                addHeader = "sed -i 1i\""+ csvHeader + "\" " + explorationDir+'/'+expressionCl+'/'+epochTimeCsv
                os.system(addHeader)               
            else: print("index file is missing for "+explorationDir+"/"+expressionLower+"/"+fileName)

                
            """
            for fn in os.listdir(explorationDir+"/"+expressionLower+"/"+fileName):
                if fn =="index":
                    indexFile= open(explorationDir+"/"+expressionLower+"/"+fileName+"/index","r")
                    reader=csv.reader(indexFile)
                    for row in reader:
                        rowAsString = "".join(row)
                        lowLevelPath = explorationDir+"/"+rowAsString
                        if os.path.isfile(lowLevelPath):
                            lowLevelHash = rowAsString.split("/")[-1]
                            makeAtfScripts(lowLevelPath,lowLevelHash)
                            #hier würde dann atf mit den scripts aufgerufen.
                            print("Processing Expression: \""+lowLevelHash+"\"\n")
                            p= subprocess.Popen([ './lowLevelLift' ],cwd=explorationDir+'/atfCcfg',shell=True)
                            p.wait()
                            
                        else:
                            print("Path was not a file: \""+lowLevelPath+"\"\n")
            """
#TODO check if we still need this
def makeAtfScripts(lowLevelExpressionPath, lowLevelHash):
    printBlue("\n[INFO] Generating compile.sh and run.sh for low level expression "+lowLevelHash+" -- " )
    if(not os.path.isdir(lowLevelTuner) or not os.path.isfile(lowLevelTuner+'/lowLevelLift')):
        sys.exit("[ERROR] Low level tuner does not exist at " + lowLevelTuner+'/lowLevelLift')
    #os.chdir(explorationDir)
    silent_mkdir(explorationDir+"/atfCcfg")
    
    #copy the tuner
    shutil.copy2(lowLevelTuner+'/lowLevelLift', explorationDir+'/atfCcfg')
    make_executable(explorationDir+'/atfCcfg')
    
    #create the compile script
    kernelGenerator = scriptsDir+"/KernelGenerator"
    kernelGeneratorArgs ='--ls <$TP:LS0>,1,1 --gs <$TP:GS0>,1,1'
    compileScript = open(explorationDir+'/atfCcfg/compileScript.sh','w')
    compileScript.write('#!/bin/sh\n')
    compileScript.write(kernelGenerator+' '+kernelGeneratorArgs+' '+lowLevelExpressionPath)
    compileScript.close()
    make_executable(explorationDir+'/atfCcfg/compileScript.sh')
    
    #create the run script
    runScript = open(explorationDir+'/atfCcfg/runScript.sh','w')
    runScript.write('#!/bin/sh\n')
    runScript.write(executor+'/scripts/explore.py --atfHarness --atfHarnessDir '+explorationDir+'/'+expressionCl+'/'+lowLevelHash +" "+absoluteConfigPath)
    runScript.close()
    make_executable(explorationDir+'/atfCcfg/runScript.sh')

#TODO move to explore util module
def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)
    

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
    bestKernel="null"
    bestKernelIndex=0
    worstKernelIndex=0
    worstTime=0;
    worstKernel="null"

    for time in times:
        if(isfloat(time)):
            if bestTime > float(time):
                bestKernel=kernels[index]
                bestTime=float(time)
                bestKernelIndex=index
            if worstTime < float(time):
                worstTime=float(time)
                worstKernel=kernels[index]
                worstKernelIndex=index
            index+=1;
        else:
            if bestTime > int(time):
                bestKernel=kernels[index]
                bestTime=int(time)
                bestKernelIndex=index
            if worstTime < int(time):
                worstTime=int(time)
                worstKernel=kernels[index]
                worstKernelIndex=index
            index+=1;   
        

    os.chdir(explorationDir)
        #save best kernel
    command = "mkdir bestkernel; cd bestkernel ;echo \""+str(header)+"\n"+str(rows[bestKernelIndex])+"\" > kernelinfo.csv ;find "+explorationDir+"/"+expressionCl+" -name '"+bestKernel+"*.cl' -exec cp '{}' "+explorationDir+"/bestkernel/kernel.cl \\;" 
    os.system(command)
        #save lowelevel expression
    os.chdir(explorationDir+"/bestkernel")
    command = "find "+explorationDir+"/"+expressionLower+" -name '"+getVariable(explorationDir+"/bestkernel/kernel.cl","Low-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/bestkernel/expression.low \\;" 
    os.system(command)
        #save highlevel expression
    os.chdir(explorationDir+"/bestkernel")
    command = "find "+explorationDir+"/"+expression+" -name '"+getVariable(explorationDir+"/bestkernel/kernel.cl","High-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/bestkernel/expression.high \\;" 
    os.system(command)
    os.chdir(explorationDir)
        #save worst kernel
    command = "mkdir worstkernel; cd worstkernel; echo \""+str(header)+"\n"+str(rows[worstKernelIndex])+"\" > kernelinfo.csv ;find "+explorationDir+"/"+expressionCl+" -name '"+worstKernel+".cl' -exec cp '{}' "+explorationDir+"/worstkernel/kernel.cl \\;" 
    os.system(command)  
        #save lowelevel expression
    os.chdir(explorationDir+"/worstkernel")
    command = "find "+explorationDir+"/"+expressionLower+" -name '"+getVariable(explorationDir+"/worstkernel/kernel.cl","Low-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/worstkernel/expression.low \\;" 
    os.system(command)
            #save highlevel expression
    os.chdir(explorationDir+"/worstkernel")
    command = "find "+explorationDir+"/"+expression+" -name '"+getVariable(explorationDir+"/worstkernel/kernel.cl","High-level hash:")+"' -exec cp -r '{}' "+explorationDir+"/worstkernel/expression.high \\;" 
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
    find = "find . -name \"" + name + "_" + str(inputSize) + ".csv\" | xargs cat | wc -l"
    os.system(find)
    
def saveExplorationMetaInformation():
    global explorationLength
    os.chdir(explorationDir+"/bestkernel")
    kernelNumber = "cd "+explorationDir+"/"+expressionCl+";  ls */*.cl | wc -l"
    validExecutions = "find "+explorationDir+"/"+expressionCl+" -name \"" + timeCsv + "\" | xargs cat | wc -l"
    allExecutions = "find "+explorationDir+"/"+expressionCl+" -name \"exec_" + str(inputSize) + ".csv\" | xargs cat | wc -l"
    liftBranch = "cd "+lift+" ; git branch | grep -e \"^*\" | cut -d' ' -f 2-"
    liftCommit = "cd "+lift+" ; git rev-parse HEAD"
    arithExpBranch = "cd "+lift+"/lib/ArithExpr ;  git branch | grep -e \"^*\" | cut -d' ' -f 2-"
    arithExpCommit = "cd "+lift+"/lib/ArithExpr  ; git rev-parse HEAD"
    harnessBranch = "cd "+executor+" ; git branch | grep -e \"^*\" | cut -d' ' -f 2-"
    harnessCommit = "cd "+executor+" ; git rev-parse HEAD"
    
    
    saveMetadataHeader = "echo \"explorationTime,kernelNumber,allExecutions,validExecutions,liftBramch,currentLiftCommit,arithExprBranch,currentArithExprCommit,harnessBranch,currentHarnessCommit\" >> metadata.csv"
    saveExplorationTime = "echo \""+str(explorationLength)+",$("+kernelNumber+"),$("+allExecutions+"),$("+validExecutions+"),$("+liftBranch+"),$("+liftCommit+"),$("+arithExpBranch+"),$("+arithExpCommit+"),$("+harnessBranch+"),$("+harnessCommit+")\" >> metadata.csv"
    os.system(saveMetadataHeader)
    os.system(saveExplorationTime)
    
def printSummary():
    #print how many executed runs there are
    os.chdir(expressionCl)
    validExecutions = "find . -name \"" + timeCsv + "\" | xargs cat | wc -l"
    allExecutions = "find . -name \"exec_" + str(inputSize) + ".csv\" | xargs cat | wc -l"
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
    command = "find . -name \"" + name + "_" + str(inputSize) + ".csv\" | xargs rm"
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
    if(args.makeTuner):
        executionModule.init(json_envConfig, json_config)
        executionModule.run()
    
#    if(args.atfHarness): atfHarness() 
#    if(args.lowLevelAtf): lowLevelAtf()

os.chdir(currentDir)
