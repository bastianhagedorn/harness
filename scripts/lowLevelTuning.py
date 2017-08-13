import subprocess
import os
import sys
import errno
import shutil
import time
import calendar
import csv
import json
import executionUtil as eu
import timeit
#lowLevelTuning is an execution module so we can use it as any other execution module using the executionModule api

### Module attributes ###
#Note: Inside functions We can read these without any problems but if we want to assign them, we need to explicitly tell the function scope that this variable is not local.
#Also note: these can be accessed from the outside of the module but one should not do this.
_ready=False

_envConfPath=None
_confPath=None

#environment
 #Paths
_lift=None
_atf=None
_tuner=None
 #openCL
_clPlattform=None
_clDevice=None

#general
_expression=None
_name=None
_inputSize = None
_cwd=None
_explorationDir=None
_expressionLower=None
_liftScripts=None



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
    global _lift, _atf, _tuner, _clPlattform, _clDevice
    global _expression, _name, _inputSize, _cwd, _explorationDir, _expressionLower, _liftScripts
    global _ready, _envConfPath, _confPath
    if(_ready): return
    #read the environment values required for this module to work
    _lift = os.path.normpath(envConf['Path']['Lift'])
    _atf = os.path.normpath(envConf['Path']['Atf'])
    _tuner = os.path.normpath(envConf['Path']['LowLevelTuner'])
    _clPlattform=envConf['OpenCL']['Platform']
    _clDevice=envConf['OpenCL']['Device']
    
    #read the explore values required for this module to work
    _expression = explorationConf['General']['Expression']
    _name = explorationConf['General']['Name']
    if (_name == ""): _name = str(calendar.timegm(time.gmtime()))
    _inputSize = explorationConf['General']['InputSize']
    
    _cwd = os.getcwd()
    _explorationDir = _cwd + "/" + _name
    _expressionLower = _expression + "Lower"
    _liftScripts = _lift + "/scripts/compiled_scripts"
    
    _envConfPath = envConfPath
    _confPath = explorationConfPath
    
    #module is ready to use now
    _ready=True
    
    
#cleans the files created by the last execution    
def clean():
    _checkState()
    #clean atfCcfg dir
    atfCcfg = _explorationDir+'/atfCcfg'
    if(os.path.isdir(atfCcfg)):
        clearDir(atfCcfg)
    
    #remove *_parameter.json files
    for fileName in os.listdir(_explorationDir+'/'+_expressionLower):
        if os.path.isdir(_explorationDir+'/'+_expressionLower+'/'+fileName):
            #this file contains paths of LowLevel expressions relative to the exploration dir
            indexFile = open(_explorationDir+"/"+_expressionLower+"/"+fileName+"/index","r")
            for llrelPath in indexFile:
                llrelPath=llrelPath.strip('\n') #remove the newline
                silentRemove(_explorationDir+'/'+llrelPath+'.json')
            

#runs the exectution
def run():
    _checkState()
    #timing stuff
    # run time stuff
    statsCsvFile=open(_explorationDir+'/tuningStats.csv','w')
    statsWriter = csv.DictWriter(statsCsvFile, ['expression','analyse expression','tuner code creation','tuner code compile','run script creation','tuning','post-tuning','total'])
    statsWriter.writeheader()
    printBlue("\n[INFO] Tuning low level expressions with atf -- " )


    #create atfCcfg dir
    atfCcfgDir = _explorationDir+'/atfCcfg'
    silentMkdir(atfCcfgDir)
    
    tmpCsvFile = open(atfCcfgDir+'/tmp.csv','w')
    #TODO Why does atf output time+6 values when we just tuned 3 values?
    tmpCsvWriter = csv.writer(tmpCsvFile)
    #TODO This header doesn't always match the contents...
    tmpCsvWriter.writerow(['llExpression','time','glsize0','glsize1','glsize2','lsize0','lsize1','lsize2','N','v1'])
    
    
    for fileName in os.listdir(_explorationDir+'/'+_expressionLower):
        if os.path.isdir(_explorationDir+'/'+_expressionLower+'/'+fileName):
            #this file contains paths of LowLevel expressions relative to the exploration dir
            indexFile = open(_explorationDir+"/"+_expressionLower+"/"+fileName+"/index","r")
            for llrelPath in indexFile:
                llrelPath=llrelPath.strip('\n') #remove the newline
                lowLevelPath=_explorationDir+'/'+llrelPath
                if(os.path.isfile(lowLevelPath)):
                    t0=timeit.default_timer()
                    exploreStatsDict={"expression":llrelPath}
                    printBlue('[INFO] Creating Tunner of '+llrelPath)
                    _prepareTuner(lowLevelPath,exploreStatsDict)
                    exit(0)
                    tStart=timeit.default_timer()
#                   p = subprocess.Popen(['./lowLevelLift'], cwd=atfCcfgDir)
#                   p.wait()
                    tStart=logTime(exploreStatsDict, tStart,'tuning')
#                   
#                   #addLExpression to the csv and move the contents over to the tmpCsv
#                   #TODO we can't simply append the contents. We need to take care of differences in the header.
#                   timesCsvFile = open(atfCcfgDir+'/times.csv','r')
#                   timesCsvReader = csv.reader(timesCsvFile)
#                                       
#                   next(timesCsvReader) # skip header
#                   for line in timesCsvReader:
#                     line.insert(0,llrelPath)
#                     tmpCsvWriter.writerow(line)
#                   timesCsvFile.close()
                    logTime(exploreStatsDict, tStart,'post-tuning')
#                   
                    writeExploreStats(statsWriter,exploreStatsDict,t0)
                    
                else:
                    warn('Not a file: "' + lowLevelPath+'"')
        
    tmpCsvFile.close()
    statsCsvFile.close()
    shutil.move(atfCcfgDir+'/tmp.csv',atfCcfgDir+'/times.csv')

#cleans the execution directories and runs the execution afterwards
#Note: I'm not quite sure if we need a rerun function or if we should just always call clean before running. 
def rerun():
    _checkState()
    clean()
    run()

#collects the times of the last execution
def gatherTimes():
    _checkState()
    shutil.move(_explorationDir+'/atfCcfg/times.csv',_explorationDir+'/times.csv')

#exports the kernels and the tuned parameters of the best and worst kernels
def findKernels():
    _checkState()
    sys.exit('findKernels not yet implemented')

#tells which rewrites are required to run before the execution module can start its work
def requiredRewrites():
    return ('highLevel','memoryMapping')




### private helper functions ###
def _prepareTuner(lowLevelExpressionPath,exploreStatsDict):
    tStart=timeit.default_timer()
    #read json and extract tp informations including dependencies 
    tunerDir = _explorationDir+'/atfCcfg'
    params = _getTuningParameter(lowLevelExpressionPath)
    tStart=logTime(exploreStatsDict, tStart,'analyse expression')
    
    dependencyTree=eu.makeDependencyTree(params)
    
    #create Tuner code
    mainCpp = open(_atf+'/examples/lowLevelLift/src/main.cpp','w')
    
    mainCpp.write('#include <atf.h>\n')
    mainCpp.write('int main(){\n')
    
    eu.writeTps(dependencyTree, mainCpp)
    mainCpp.write('auto cf = atf::cf::ccfg("./runScript.py", "./runScript.py", true, "./costfile.txt");\n')
    mainCpp.write('auto best_config = atf::open_tuner(atf::cond::speedup(1.01,20))(')
    eu.writeGroups(dependencyTree, mainCpp)
    mainCpp.write(')(cf);\n')
    mainCpp.write('}\n')
    mainCpp.close()
    tStart=logTime(exploreStatsDict, tStart,'tuner code creation')
    
    #start compiling atf. We can continue doing other stuff in this thread and wait for the compiler later on.
    print('Hey get back to work! compiling...')
    p = subprocess.Popen([ _atf+'/build.sh' ])
    p.wait()
    tStart=logTime(exploreStatsDict, tStart,'tuner code compile')
    
    #create runScript code
    gsvars=eu.collectGsizes(dependencyTree)
    lsvars=eu.collectLsizes(dependencyTree)
    tpvars=eu.collectTpVars(dependencyTree)
    runScript = open(tunerDir+'/runScript.py','w')
 
    runScript.write(
'''
#!/usr/bin/python3
# generated by lowLevelTuning.py. Don\'t change this file, changes will be lost on the next run anyways.
import subprocess
import timeit
import csv

kernelGenStats=open("{exploreDir}/kernelGenStats.csv","a")
statsWriter = csv.DictWriter(kernelGenStats, ["expression","total"])
tStart=timeit.default_timer()

p = subprocess.Popen([
	"{kernelgenPath}",
	"--env", "{env}",
	"--gs",  "{gsizes}",
	"--ls",  "{lsizes}",
	"--vars","1024,{vars}", #TODO problemsizes hardcoded!
	"{llExpPath}"
])
rc=p.wait()
statsWriter.writerow({{
	"expression":"{llExpPath}",
	"total":timeit.default_timer()-tStart
}})
kernelGenStats.close()
exit(rc)
'''[1:-1].format(
	exploreDir=_explorationDir,
	kernelgenPath=_liftScripts+'/KernelGenerator',
	env=_envConfPath,
	gsizes=','.join([v for v in gsvars]),
	lsizes=','.join([v for v in lsvars]),
	vars=','.join([v for v in tpvars]),
	llExpPath=lowLevelExpressionPath
)
    )
    runScript.close()
    makeExecutable(tunerDir+"/runScript.py")
    logTime(exploreStatsDict, tStart,"run script creation")
    
    #init the times.csv
    timesCsvFile = open(tunerDir+"/times.csv","w") #using w wil override the existing file if there was an existing file. That's exactly what we want.
    #TODO Why does atf output time+6 values when we just tuned 3 values?
    #TODO header should depend on the values used for tuning.
    timesCsvFile.write('time,glsize0,glsize1,glsize2,lsize0,lsize1,lsize2')
    timesCsvFile.close()
    
    
    #move it over
    shutil.copy2(_tuner+'/lowLevelLift',tunerDir)
    makeExecutable(tunerDir+'/lowLevelLift')
    
    
    
def _getTuningParameter(lowLevelExpressionPath):
    #call Analyzer if *parameter.json does not exist
    if(not os.path.isfile(lowLevelExpressionPath+'.json')):
        p = subprocess.Popen([_liftScripts+'/LambdaAnalyser',lowLevelExpressionPath])
        p.wait()
 
#   #copy dummy file for testing without the Analyzer
#   if(not os.path.isfile(lowLevelExpressionPath+'_parameter.json')):
#       scriptsDir = os.path.dirname(os.path.realpath(__file__))
#       shutil.copy2(scriptsDir+'/template.json',lowLevelExpressionPath+'_parameter.json')
    
    
    #read the json
    jsonFile = open(lowLevelExpressionPath+'.json')
    params = json.load(jsonFile)
    jsonFile.close()
    return params

def _checkState():
    if(not _ready):error('lowLevelTuning module was not initialised. Call init before using this module')
    elif(not os.path.isdir(_explorationDir+'/'+_expressionLower)):error('The directory '+_explorationDir+'/'+_expressionLower+' does not exist. Please run the HighLevel and MemoryMapping Rewrites before executing')
    










def logTime(exploreStatsDict, tStart,title):
  exploreStatsDict[title] = timeit.default_timer()-tStart
  return timeit.default_timer()

def writeExploreStats(writer, exploreStatsDict,t0):
	logTime(exploreStatsDict, t0, 'total')
	writer.writerow(exploreStatsDict)


### More helper that should be located in some explorationUtil module
def printBlue( string ):
    print(bcolors.BLUE + string + bcolors.ENDC)
    return
    
def info(string):
    print('[INFO] ' + string )

def warn(string):
    print(bcolors.FAIL+'[WARN] ' + bcolors.ENDC + string )

def error(string):
    sys.exit(bcolors.FAIL+'[ERROR] ' + bcolors.ENDC + string)

class bcolors:
    BLUE= '\033[95m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#use camelCase or under_score or alllower function names but dontMix_them.
def clearDir(dirname):
    for f in os.listdir(dirname):
        silentRemove(f)

def silentRemove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

def silentMkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def makeExecutable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)
