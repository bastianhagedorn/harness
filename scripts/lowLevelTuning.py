import subprocess
import os
import sys
import errno
import shutil
import time
import calendar
import json
#lowLevelTuning is an execution module so we can use it as any other execution module using the executionModule api


### Module attributes ###
#Note: Inside functions We can read these without any problems but if we want to assign them, we need to explicitly tell the function scope that this variable is not local.
#Also note: these can be accessed from the outside of the module but one should not do this.
_ready=False
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
#void init(ConfigParser envConf, ConfigParser explorationConf)
#void clean()
#void run()
#void rerun()
#void gatherTimes()
#void findKernels()
#void requiredRewrites()

#Initializes the module
def init(envConf, explorationConf):
    global _lift, _atf, _tuner, _clPlattform, _clDevice
    global _expression, _name, _inputSize, _cwd, _explorationDir, _expressionLower, _liftScripts
    global _ready
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
    
    #module is ready to use now
    _ready=True
    
    
#cleans the files created by the last execution    
def clean():
    _checkState()
    sys.exit('not yet implemented')

#runs the exectution
def run():
    _checkState()
    printBlue("\n[INFO] Tuning low level expressions with atf -- " )
    
    silentMkdir(_explorationDir+'/atfCcfg')
    
    for fileName in os.listdir(_explorationDir+'/'+_expressionLower):
        if os.path.isdir(_explorationDir+'/'+_expressionLower+'/'+fileName):
            #this file contains paths of LowLevel expressions relative to the exploration dir
            indexFile = open(_explorationDir+"/"+_expressionLower+"/"+fileName+"/index","r")
            for llrelPath in indexFile:
                llrelPath=llrelPath.strip('\n') #remove the newline
                lowLevelPath=_explorationDir+'/'+llrelPath
                if(os.path.isfile(lowLevelPath)):
                    printBlue('[INFO] Creating Tunner of '+llrelPath)
                    _prepareTuner(lowLevelPath)
                    p = subprocess.Popen(['./lowLevelLift'], cwd=_explorationDir+'/atfCcfg')
                    p.wait()
                    
                else:
                    warn('Not a file: "' + lowLevelPath+'"')

#cleans the execution directories and runs the execution afterwards
#Note: I'm not quite sure if we need a rerun function or if we should just always prepare 
def rerun():
    _checkState()
    sys.exit('not yet implemented')

#collects the times of the last execution
def gatherTimes():
    _checkState()
    sys.exit('not yet implemented')

#exports the kernels and the tuned parameters of the best and worst kernels
def findKernels():
    _checkState()
    sys.exit('not yet implemented')

#tells which rewrites are required to run before the execution module can start its work
def requiredRewrites():
    _checkState()
    return ("highLevel","memoryMapping")




### private helper functions ###
def _prepareTuner(lowLevelExpressionPath):
    tunerDir = _explorationDir+'/atfCcfg'
    params = _getTuningParameter(lowLevelExpressionPath)
    
    #create Tuner code
    mainCpp = open(_atf+'/examples/lowLevelLift/src/main.cpp','w')
    #and runScript code
    runScript = open(tunerDir+'/runScript.py','w')
    
    mainCpp.write('#include <atf.h>\n')
    mainCpp.write('int main(){\n')
    
    runScript.write('#!/usr/bin/python3\n')
    runScript.write('import subprocess\n')    
    
    gsvars=[]
    lsvars=[]
    tpvars=[]
    for param in params:
        name=param['name']
        if(name.startswith('gs')):   gsvars.append(name)
        elif(name.startswith('ls')): lsvars.append(name)
        else: tpvars.append(name)
        
        mainCpp.write('auto '+name+' = atf::tp( "'+name+'"')
        if('interval' in param):
            interval=param['interval']
            mainCpp.write(', atf::interval<'+interval['type']+'>('+interval['from']+','+interval['to']+')')
        
        if('divides' in param):
            mainCpp.write(', atf::divides('+param['divides']+')')
                
        mainCpp.write(');\n')
    
    runScript.write('p = subprocess.Popen(["'+_liftScripts+'/KernelGenerator", ')
    runScript.write(  '"--gs", "'+','.join(['<$TP:'+v+'>' for v in gsvars])+'", ')
    runScript.write(  '"--ls", "'+','.join(['<$TP:'+v+'>' for v in lsvars])+'", ')
    runScript.write('"--vars", "1024,'+','.join(['<$TP:'+v+'>' for v in tpvars])+'", ')
    runScript.write('"'+lowLevelExpressionPath+'"])\n')
    runScript.write('p.wait()\n')
    mainCpp.write('auto cf = atf::cf::ccfg("./runScript.py", "./runScript.py", true, "./costfile.txt");\n')
    gsvars.extend(lsvars)
    gsvars.extend(tpvars)
    mainCpp.write('auto best_config = atf::annealing(atf::cond::duration<std::chrono::seconds>(60))('+', '.join(gsvars)+')(cf);\n')
    mainCpp.write('}\n')
    
    mainCpp.close()
    runScript.close()
    
    #compile it
    p = subprocess.Popen([ _atf+'/build.sh' ])
    p.wait()
    
    #move it over
    shutil.copy2(_tuner+'/lowLevelLift', _explorationDir+'/atfCcfg')
    makeExecutable(tunerDir+'/lowLevelLift')
    makeExecutable(tunerDir+'/runScript.py')   
    
def _getTuningParameter(lowLevelExpressionPath):
    #TODO call Analyzer if parameter.json does not exist
    
    #copy dummy file for testing without the Analyzer
    if(not os.path.isfile(lowLevelExpressionPath+'_parameter.json')):
        scriptsDir = os.path.dirname(os.path.realpath(__file__))
        shutil.copy2(scriptsDir+'/template.json',lowLevelExpressionPath+'_parameter.json')
    
    
    #read the json
    jsonFile = open(lowLevelExpressionPath+'_parameter.json')
    params = json.load(jsonFile)
    jsonFile.close()
    return params

def _checkState():
    if(not _ready):error('lowLevelTuning module was not initialised. Call init before using this module')
    elif(not os.path.isdir(_explorationDir+'/'+_expressionLower)):error('The directory '+_explorationDir+'/'+_expressionLower+' does not exist. Please run the HighLevel and MemoryMapping Rewrites before executing')















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
        silentremove(f)

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
