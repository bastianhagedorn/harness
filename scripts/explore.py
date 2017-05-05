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

### README ###########################################################
# Script to start exploration run for a Lift high-level expression
#
# Requirements:
#       * ParameterRewrite settings need to be in LIFT/highLevel/
#
######################################################################

### ARGPARSER ########################################################
parser = argparse.ArgumentParser( description='Lift exploration utility')
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
parser.add_argument('--fullAtf', dest='fullAtf', action='store_true',
        help='run atf recursively')
args = parser.parse_args()

# CONFIG (PARSER) ##################################################
# check if config exists
if not os.path.exists(args.config): sys.exit("[ERROR] config file not found!")
configParser = configparser.RawConfigParser()
configParser.read(args.config)

### GENERAL
lift = configParser.get('General', 'Lift')
executor = configParser.get('General', 'Executor')
tuner = configParser.get('General', 'Tuner')
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
parameterRewriteArgs = " --file " + lift + "highLevel/" + settings 
if(sequential == "true"): parameterRewriteArgs += " --sequential"
if(disableNDRangeInjection == "true"): parameterRewriteArgs += " --disableNDRangeInjection"
if(exploreNDRange == "true"): parameterRewriteArgs += " --exploreNDRange"
if (exploreNDRange == "true")and not (sampleNDRange == ""): parameterRewriteArgs += " --sampleNDRange " + sampleNDRange

### HARNESSS
harness = configParser.get('Harness', 'Name')
harnessArgs = " " + configParser.get('Harness', 'Args')

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
Rscript = configParser.get('R', 'Script')
output = expression + "_" + inputSize +  "_" + name + ".pdf"
RscriptArgs = " --file " + epochTimeCsv + " --out " + output

### DIRECTORIES
currentDir = os.getcwd() #current working directory
explorationDir = currentDir + "/" + name
expressionLower = expression + "Lower"
expressionCl = expression + "Cl"
plotsDir = "plots"
scriptsDir = lift + "scripts/compiled_scripts/"

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
    args = highLevelRewriteArgs + " " + lift + "highLevel/" + expression
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
    os.chdir(expressionCl)
    # recursively access every subdirectory and execute atf with kernels
    command = "for d in ./*/ ; do (cp " + tunerName + " \"$d\" && cd \"$d\" && for i in *.cl ; do (./"+ tunerName + " \"$i\"" + "); done); done"
    os.system(command)
    os.chdir(explorationDir)

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
    os.chdir(expressionCl)
    command = "find . -name \""  +"results.csv"+ "\" | xargs cat >> " + epochTimeCsv
    os.system(command)
    # add header
    addHeader = "sed -i 1i\""+ atfCsvHeader + "\" " + epochTimeCsv
    os.system(addHeader)
    os.chdir(explorationDir)

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

def exploreAtf():
    printBlue("[INFO] Starting exploration -- " + expression)
    start = time.time()
    rewrite()
    executeAtf()
    end = time.time()
    elapsed = (end-start)/60
    printBlue("[INFO] Finished exploration! Took " + str(elapsed) + " minutes to execute")
    printSummary()

def explore():
    printBlue("[INFO] Starting exploration -- " + expression)
    start = time.time()
    rewrite()
    execute()
    end = time.time()
    elapsed = (end-start)/60
    printBlue("[INFO] Finished exploration! Took " + str(elapsed) + " minutes to execute")
    printSummary()

def printOccurences(name):
    print(bcolors.BLUE + "[INFO] " + name + ": " + bcolors.ENDC, end='', flush=True)
    find = "find . -name \"" + name + "_" + inputSize + ".csv\" | xargs cat | wc -l"
    os.system(find)
    
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
    if(args.fullAtf): exploreAtf()

os.chdir(currentDir)
