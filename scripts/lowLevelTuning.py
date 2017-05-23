#lowLevelTuning is an execution module so it provides the following methods:
#void init(ConfigParser envConf, ConfigParser explorationConf)
#void clean()
#void run()
#void rerun()
#void gatherTimes()
#void findKernels()
#void requiredRewrites()


#define all wanna be private module variables
_args=None
_envConf=None
_explorationConf=None


#Initializes the module
def init(envConf, explorationConf):
    error('not yet implemented')
    
#cleans the files created by the last execution    
def clean():
    error('not yet implemented')

#runs the exectution
def run():
    printBlue("\n[INFO] Tuning low level expressions with atf -- " )
    for fileName in os.listdir(explorationDir+'/'+expressionLower):
        if os.path.isdir(explorationDir+'/'+expressionLower+'/'+fileName):
            #this file contains paths of LowLevel expressions relative to the exploration dir
            indexFile = open(explorationDir+"/"+expressionLower+"/"+fileName+"/index","r")
            for llrelPath in indexFile:
                llrelPath=llrelPath.strip('\n') #remove the newline
                lowLevelPath=explorationDir+'/'+llrelPath
                if(os.path.isfile(lowLevelPath)):
                    lowLevelHash=os.path.basename(llrelPath)
                    _makeLowLevelTuner(lowLevelPath)
                else:
                    warn('Not a file: "' + lowLevelPath+'"')

#cleans the execution directories and runs the execution afterwards
#Note: I'm not quite sure if we need a rerun function or if we should just always prepare 
def rerun():
    error('not yet implemented')

#collects the times of the last execution
def gatherTimes():
    error('not yet implemented')

#exports the kernels and the tuned parameters of the best and worst kernels
def findKernels():
    error('not yet implemented')

#tells which rewrites are required to run before the execution module can start its work
def requiredRewrites():
    return ("highLevel","memoryMapping")




#pseudo private helper functions              
def _makeLowLevelTuner(lowLevelExpressionPath):
    #create Tuner code
    params = getTuningParameter(lowLevelExpressionPath)
    mainCpp = open(atf+'/examples/lowLevelLift/src/main.cpp','w')
    mainCpp.write('#include <atf.h>\n')
    mainCpp.write('int main(){\n')
    
    tps=[]
    for param in params:
        tps.append(param['name'])
        mainCpp.write('auto '+param['name']+' = atf::tp( "'+param['name']+'"')
        if('interval' in param):
            interval=param['interval']
            mainCpp.write(', atf::interval<'+interval['type']+'>('+interval['from']+','+interval['to']+')')
        
        if('divides' in param):
            mainCpp.write(', atf::divides('+param[divides]+')')
                
        mainCpp.write(');\n')
    
    mainCpp.write('auto cf = atf::cf::ccfg("./lowLevelExpression", "./runScript.sh", true, "./costfile.txt");\n')
    mainCpp.write('auto best_config = atf::annealing(atf::cond::duration<std::chrono::seconds>(2))('+', '.join(tps)+')(cf);\n')
    mainCpp.write('}\n')
    mainCpp.close()
    
    #compile it
    p = subprocess.Popen([ atf+'/build.sh' ])
    p.wait()
    
    #move it over
    shutil.copy2(lowLevelTuner+'/lowLevelLift', explorationDir+'/atfCcfg')
    make_executable(explorationDir+'/atfCcfg')

def _prepareLowLevelExpression(lowLevelExpressionPath):
    return None
    
    
def _getTuningParameter(lowLevelExpressionPath):
    #returns the tuning parameters object of the given file
    jsonFile = open(lowLevelExpressionPath+'_parameter.json')
    params = json.load(jsonFile)
    jsonFile.close()
    return params
