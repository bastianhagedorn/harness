#!/usr/bin/python3

import json
import pprint

#some stuff that could be useful to implement an execution module.

#Eine dependency is wat wo nen tp und children haben tut
def _recursiveWriteTps(tpMap, dependency, mainCpp):
  tp=dependency['tp']
  mainCpp.write('auto '+tp['name']+' = atf::tp( "'+tp['name']+'"')
  if('interval' in tp):
    interval=tp['interval']
    mainCpp.write(', atf::interval<'+interval['type']+'>('+str(interval['from'])+','+str(interval['to'])+')')
  if('divides' in tp):
    mainCpp.write(', atf::divides('+tp['divides']+')')
  mainCpp.write(');\n')
  
  for childKey in dependency['children']:
    _recursiveWriteTps(tpMap,tpMap[childKey],mainCpp)

def _recursiveCollectGroups(tpMap, groupList, dep):
  groupList.append(dep['tp']['name'])
  for childKey in dep['children']:
    _recursiveCollectGroups(tpMap, groupList, tpMap[childKey])
  return groupList

def writeTps(tpMap, mainCpp):
  for dep in tpMap['root']['children']:
    _recursiveWriteTps(tpMap,tpMap[dep],mainCpp)
    
    
#returns a list of lists of strings, where these mysterious strings are the names of tuning parameters, the inner list is a tp group and the outer list is a list of these groups.
def collectGroups(tpMap):
  groups=[]
  for dep in tpMap['root']['children']:
    groups.append(_recursiveCollectGroups(tpMap,[],tpMap[dep]))  
  return groups

def writeGroups(tpMap,mainCpp):
  groups=collectGroups(tpMap)
  
  if(len(groups)==0):
    return # yay we got nothing to do, party!
  
  # we have to work on it :(
  #just do some pythonic stuff that nobody ever wants to maintain.
  mainCpp.write(', '.join(['G(' + (', '.join([ v for v in g]))+')' for g in groups ]))
  
  #the following code does the same and is imho more readable but less pythonic so I didn't use it.
  #mainCpp.write('G(')
  #mainCpp.write('), G('.join([', '.join(group) for group in groups]))
  #mainCpp.write(')')  
  
def collectGsizes(tpMap):
  return sorted([var for var in tpMap if var.startswith('gs')])

def collectLsizes(tpMap):
  return sorted([var for var in tpMap if var.startswith('ls')])

def collectTpVars(tpMap):
  return sorted([var for var in tpMap if not var.startswith('gs') and not var.startswith('ls') and var!='root'])

def makeDependencyTree(json):
  dependencies={} # that guy will be something like a linked tree based on a dictionary so we can access our tps quickly.
  
  for param in json:
    name=param['name']
    
    # make sure our key is in the map/tree.
    if(name not in dependencies): #add key to dependencies tree if not yet existent.
      dependencies[name]={'tp':param, 'children':[]}
    else:#otherwise simply update its value.
      dependencies[name]['tp']=param
    
    # get our parent
    if('divides' in param and not param['divides'].isdecimal()): #hey there we got a dependency and it's not a constant!
      parentName=param['divides']
    else:
      parentName='root'
    
    #make sure our parent exists in the map/tree
    if(parentName not in dependencies):
      dependencies[parentName]={'children':[]}
      
    #now we can add us to our parents child list.
    dependencies[parentName]['children'].append(name)
  
  if('root' not in dependencies):
    raise ValueError('Ill eagle argument. Circular dependencies. Srsly there is not even a single parameter without a dependency and I already ignored dependencies to constants.')
  
  return dependencies # all right, we can return the tree to you!


# uhm yeah a main for testing purposes...
def main():
  #read the json
  jsonFile = open('/mnt/share/intelliJ-projects/exploration/lowReduceSeq/convolution2DLower/590e6ed439eb1e8f8210943600faf08af1d58a2f1149f134db71f5d88887775f/0/9/092e9a84b288bc4c05db0815adc1a7e8a028b0ba0e0439ec19a354114cc3933e.json')
  params = json.load(jsonFile)
  jsonFile.close()
  dependencies=makeDependencyTree(params)
  pprint.pprint(dependencies)
  mainCpp=open('./out.cpp','w')
  writeTps(dependencies,mainCpp)
  mainCpp.write('\n\n')
  writeGroups(dependencies,mainCpp)
  pprint.pprint(collectGroups(dependencies))
