import os
import glob
from lxml import etree as ET
import csv
import json
import random 
import itertools
import copy

"""
data={
    "gitURL":{
        "sha":"dasdasd",
        "module1":{
            "methods":["m1","m2"]-set(),
            "victims":["m1","m2"]-set()
            "brittles":[]-set()
            "polluters":{
                "victim1":["polluter1","polluter2"]-set(),
                "victim2":["polluter1","polluter2"]-set()
            },
            "cleaners":{
                "victim1":{
                    "polluter":["cleaner1","cleaner2"]-set()
                }
            },
            "statesetters":{
                "brittle":["statesetter1","statesetter2"]-set()
            }
            "codes":{
                "m1":"code"
            },
            "polluterCount":34,
            "cleanerCount":543,
            "statesetterCount":132
        }
    }
}
"""

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path) 

def readCSV(input_file, headers=False):
    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        csv_data = [row for row in reader]
        if headers:
            csv_data.pop(0)
    return csv_data

def getProjName(url):
    parts = url.split('/')
    project_name = parts[-1].split('.')[0]
    return project_name

def createCSV(csv_file,data):
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)

def writeFile(fileName,content):
    with open(fileName, 'w', encoding='utf-8') as f:
        f.write(content)

def appendFile(fileName,content):
    with open(fileName, 'a', encoding='utf-8') as f:
        f.write(content+"\n")

def readFile(fileName):
    with open(fileName, 'r') as file:
        contents = file.read()
    return contents

def printJSON(data):
    data=json.dumps(data,indent=4)
    print(data)
    return data

def createData(csv_data,saveCodes):
    data={}
    i=1
    for row in csv_data:
        print("Processing row: "+str(i))
        git=row[0]
        if not git.endswith(".git"):
            git=git+".git"
        if git not in data.keys():
            data[git]={}
        sha=row[1]
        data[git]["sha"]=sha
        module=row[2]
        if module.startswith("."):
            module=module[1:]
        if module.startswith("/"):
            module=module[1:]
        if module == "":
            module="NA"
        if module not in data[git].keys():
            data[git][module]={}
            data[git][module]["methods"]=set()
            data[git][module]["polluters"]={}
            data[git][module]["cleaners"]={}
            if saveCodes:
                data[git][module]["codes"]={}
            data[git][module]["victims"]=set()
            data[git][module]["brittles"]=set()
            data[git][module]["statesetters"]={}
        if row[6]=="victim":        
            victim=row[3]
            polluter=row[4]
            cleaner=row[5]
            victimCode=row[7]
            polluterCode=row[8]
            cleanerCode=row[9]
            if victim != "":
                data[git][module]["methods"].add(victim)
                if saveCodes:
                    if victim not in data[git][module]["codes"].keys():
                        data[git][module]["codes"][victim]=victimCode
                data[git][module]["victims"].add(victim)
            if polluter != "":
                data[git][module]["methods"].add(polluter)
                if saveCodes:
                    if polluter not in data[git][module]["codes"].keys():
                        data[git][module]["codes"][polluter]=polluterCode
                if victim not in data[git][module]["polluters"].keys():
                    data[git][module]["polluters"][victim]=set()
                data[git][module]["polluters"][victim].add(polluter)
            if cleaner != "":
                data[git][module]["methods"].add(cleaner)
                if saveCodes:
                    if cleaner not in data[git][module]["codes"].keys():
                        data[git][module]["codes"][cleaner]=cleanerCode
                if victim not in data[git][module]["cleaners"].keys():
                    data[git][module]["cleaners"][victim]={}
                if polluter not in data[git][module]["cleaners"][victim].keys():
                    data[git][module]["cleaners"][victim][polluter]=set()
                data[git][module]["cleaners"][victim][polluter].add(cleaner)
        elif row[6]=="brittle":
            brittle=row[3]
            statesetter=row[4]
            brittleCode=row[7]
            statesetterCode=row[8]
            if brittle!="":
                data[git][module]["methods"].add(brittle)
                data[git][module]["brittles"].add(brittle)
                if saveCodes:
                    if brittle not in data[git][module]["codes"].keys():
                        data[git][module]["codes"][brittle]=brittleCode
            if statesetter!="":
                data[git][module]["methods"].add(statesetter)
                if saveCodes:
                    if statesetter not in data[git][module]["codes"].keys():
                        data[git][module]["codes"][statesetter]=statesetterCode
                if brittle not in data[git][module]["statesetters"].keys():
                    data[git][module]["statesetters"][brittle]=set()
                data[git][module]["statesetters"][brittle].add(statesetter)
        else:
            appendFile("log.txt","Failed to process row: "+str(i))
        print("Completed processing row: "+str(i))
        i=i+1
    return data

def generateVPCombinationsCsv(csv_data, fileName):
    csv_data = [["gitURL","sha","module","victim","P/NP","isVictimPolluterPair","victim_code","P/NP_code"]] + csv_data
    fileName = os.path.join("output",fileName)
    createCSV(fileName,csv_data)

def generateCombinations(l,n):
    data = list(itertools.permutations(l, n))
    return data

def populateCombinations_seperate(data,saveCodes,balanced=False):
    newDataP=[]
    newDataC=[]
    newDataSS=[]
    for git in data.keys():
        sha=data[git]["sha"]
        for module in data[git].keys():
            if module != "sha":
                methods=list(data[git][module]["methods"])
                victims=list(data[git][module]["victims"])
                for victim in victims:
                    for method in methods:
                        if victim!=method:
                            try:
                                if method in data[git][module]["polluters"][victim]:
                                    isVictimPolluterPair = 1
                                else:
                                    isVictimPolluterPair = 0
                            except:
                                isVictimPolluterPair = 0
                            if saveCodes:
                                vCode = data[git][module]["codes"][victim]
                                mCode = data[git][module]["codes"][method]
                            else:
                                vCode = ""
                                mCode = ""
                            if module == "NA":
                                newMod=""
                            else:
                                newMod=module
                            newDataP.append([git,sha,newMod,victim,method,isVictimPolluterPair,vCode,mCode])
    for git in data.keys():
        sha=data[git]["sha"]
        for module in data[git].keys():
            if module!="sha":
                victims=list(data[git][module]["victims"])
                methods=list(data[git][module]["methods"])
                for victim in victims:
                    polluters=data[git][module]["polluters"][victim]
                    for polluter in polluters:
                        for method in methods:
                            if victim!=method and polluter!=method:
                                try:
                                    if method in data[git][module]["cleaners"][victim][polluter]:
                                        isVPCTripplet=1
                                    else:
                                        isVPCTripplet=0
                                except:
                                    isVPCTripplet=0
                                if saveCodes:
                                    vCode = data[git][module]["codes"][victim]
                                    pCode = data[git][module]["codes"][polluter]
                                    mCode = data[git][module]["codes"][method]
                                else:
                                    vCode = ""
                                    pCode = ""
                                    mCode = ""
                                if module == "NA":
                                    newMod=""
                                else:
                                    newMod=module
                                newDataC.append([git,sha,newMod,victim,polluter,method,isVPCTripplet,vCode,pCode,mCode])
    for git in data.keys():
        sha=data[git]["sha"]
        for module in data[git].keys():
            if module!="sha":
                brittles=data[git][module]["brittles"]
                methods=data[git][module]["methods"]
                for brittle in brittles:
                    for method in methods:
                        if brittle!=method:
                            try:
                                if method in data[git][module]["statesetters"][brittle]:
                                    isBSSPair=1
                                else:
                                    isBSSPair=0
                            except:
                                isBSSPair=0
                            if saveCodes:
                                bCode=data[git][module]["codes"][brittle]
                                mCode=data[git][module]["codes"][method]
                            else:
                                bCode=""
                                mCode=""
                            if module=="NA":
                                newMod=""
                            else:
                                newMod=module
                            newDataSS.append([git,sha,module,brittle,method,isBSSPair,bCode,mCode])
    return newDataP,newDataC,newDataSS

def generateVCCombinationsCsv(csv_data, fileName):
    csv_data = [["gitURL","sha","module","victim","polluter","C/NC","isVictimPolluterCleanerPair","victim_code","polluter_code","C/NC_code"]] + csv_data
    fileName = os.path.join("output",fileName)
    createCSV(fileName,csv_data)

def populateCombinations(data, saveCodes):
    newData=[]
    for git in data.keys():
        sha=data[git]["sha"]
        for module in data[git].keys():
            if module != "sha":
                methods=list(data[git][module]["methods"])
                combinations = generateCombinations(methods,3)
                for combi in combinations:
                    print("Processing: "+git+", Module: "+module+", Methods: "+str(combi))
                    possibleVictim = combi[0]
                    possiblePolluter = combi[1]
                    possibleCleaner = combi[2]
                    try:
                        if possiblePolluter in data[git][module]["polluters"][possibleVictim]:
                            isVictimPolluterPair = 1
                        else:
                            isVictimPolluterPair = 0
                    except:
                        isVictimPolluterPair = 0
                    try:
                        if possibleCleaner in data[git][module]["cleaners"][possibleVictim]:
                            isVictimCleanerPair = 1
                        else:
                            isVictimCleanerPair = 0
                    except:
                        isVictimCleanerPair = 0
                    if module == "NA":
                        newMod=""
                    else:
                        newMod=module
                    if saveCodes:
                        vCode = data[git][module]["codes"][possibleVictim]
                        pCode = data[git][module]["codes"][possiblePolluter]
                        cCode = data[git][module]["codes"][possibleCleaner]
                    else:
                        vCode = ""
                        pCode = ""
                        cCode = ""
                    newData.append([git,sha,newMod,possibleVictim,possiblePolluter,possibleCleaner,isVictimPolluterPair,isVictimCleanerPair,vCode,pCode,cCode])
    return newData    

def populateCounts(csv_data):
    for git in csv_data.keys():
        for module in csv_data[git].keys():
            p=set()
            c=set()
            if module != "sha":
                for victim in csv_data[git][module]["polluters"].keys():
                    p=p.union(csv_data[git][module]["polluters"][victim])
                for victim in csv_data[git][module]["cleaners"].keys():
                    for polluter in csv_data[git][module]["cleaners"][victim].keys():
                        c=c.union(csv_data[git][module]["cleaners"][victim][polluter])
                csv_data[git][module]["polluterCount"]=len(p)
                csv_data[git][module]["cleanerCount"]=len(c)
    return csv_data

def countPosNeg(data,isCleaner=False):
    pos=0
    neg=0
    for row in data:
        if not isCleaner:
            if row[5]==1 or row[5]=="1":
                pos=pos+1
            else:
                neg=neg+1
        else:
            if row[6]==1 or row[6]=="1":
                pos=pos+1
            else:
                neg=neg+1
    return pos,neg

def validateBalanceBrittle(BSS,bBSS):
    oldPosBSS,oldNegBSS=countPosNeg(BSS)
    newPosBSS,newNegBSS=countPosNeg(bBSS)
    print("Unbalanced BSS -> Positive : "+str(oldPosBSS)+" Negative : "+str(oldNegBSS))
    print("Balanced BSS -> Positive : "+str(newPosBSS)+" Negative : "+str(newNegBSS))
    if oldPosBSS == newPosBSS and newNegBSS<=oldPosBSS:
        print("Unbalanced BSS and Balanced BSS are valid")
    else:
        print("Unbalanced BSS and Balanced BSS are not valid")

def validateBalance(VC,VP,bVC,bVP):
    oldPosVC,oldNegVC=countPosNeg(VC,True)
    newPosVC,newNegVC=countPosNeg(bVC,True)
    oldPosVP,oldNegVP=countPosNeg(VP)
    newPosVP,newNegVP=countPosNeg(bVP)
    print("Unbalanced VPC -> Positive : "+str(oldPosVC)+" Negative : "+str(oldNegVC))
    print("Balanced VPC -> Positive : "+str(newPosVC)+" Negative : "+str(newNegVC))
    print("Unbalanced VP -> Positive : "+str(oldPosVP)+" Negative : "+str(oldNegVP))
    print("Balanced VP -> Positive : "+str(newPosVP)+" Negative : "+str(newNegVP))
    if oldPosVC == newPosVC and newNegVC<=oldPosVC:
        print("Unbalanced VPC and Balanced VPC are valid")
    else:
        print("Unbalanced VPC and Balanced VPC are not valid")
    if oldPosVP == newPosVP and newNegVP<=oldPosVP:
        print("Unbalanced VP and Balanced VP are valid")
    else:
        print("Unbalanced VP and Balanced VP are not valid")

def separateCSV(data,isCleaner):
    """
    separate = {
        "git":{
            "module":{
                positiveList:[]
                negativeList:[]
            }
        }
    }
    """
    separate={}
    for row in data:
        git=row[0]
        module=row[2]
        if module=="":
            module="NA"
        if isCleaner:
            isPair=row[6]
        else:
            isPair=row[5]
        if git not in separate.keys():
            separate[git]={}
        if module not in separate[git].keys():
            separate[git][module]={
                "positiveList":[],
                "negativeList":[]
            }
        if isPair == "1" or isPair == 1:
            separate[git][module]["positiveList"].append(row)
        else:
            separate[git][module]["negativeList"].append(row)
    return separate

def createBalance(data,methods_data,vpc_data,isPolluter,isCleaner,isBrittle):
    separate=separateCSV(data,isCleaner)
    newData=[]
    for git in separate.keys():
        for module in separate[git].keys():
            newData=newData+separate[git][module]["positiveList"]
            pLen = len(separate[git][module]["positiveList"])
            nLen = len(separate[git][module]["negativeList"])
            if nLen==pLen:
                newData=newData+separate[git][module]["negativeList"]
            elif nLen<pLen:
                newData=newData+separate[git][module]["negativeList"]
                diff = pLen-nLen
                additionalData = getAdditionalData4VPCB(git,module,methods_data,vpc_data,diff,isPolluter,isCleaner,isBrittle)
                newData=newData+additionalData
            else:
                newData=newData+separate[git][module]["negativeList"][:pLen]
    return newData

def getAdditionalData4VPCB(git,module,methods_data,vpc_data,diff,isPolluter,isCleaner,isBrittle):
    print("Add -> Module: "+module+" Git:"+git)
    if module=="NA":
        newMod=""
    else:
        newMod=module            
    additionalData=[]
    noNeedMethods=vpc_data[git][module]["methods"]
    victims=vpc_data[git][module]["victims"]
    brittles=vpc_data[git][module]["brittles"]
    try:
        for file in methods_data[git][module].keys():
            for method in methods_data[git][module][file].keys():
                if method not in noNeedMethods:
                    if isPolluter:
                        for victim in victims:
                            additionalData.append([git,vpc_data[git]["sha"],newMod,victim,method,0,vpc_data[git][module]["codes"][victim],methods_data[git][module][file][method]])
                            if len(additionalData)==diff:
                                break
                    elif isBrittle:
                        for brittle in brittles:
                            additionalData.append([git,vpc_data[git]["sha"],newMod,brittle,method,0,vpc_data[git][module]["codes"][brittle],methods_data[git][module][file][method]])
                            if len(additionalData)==diff:
                                break
                    elif isCleaner:
                        for victim in victims:
                            for polluter in vpc_data[git][module]["polluters"][victim]:
                                additionalData.append([git,vpc_data[git]["sha"],newMod,victim,polluter,method,0,vpc_data[git][module]["codes"][victim],vpc_data[git][module]["codes"][polluter],methods_data[git][module][file][method]])
                                if len(additionalData)==diff:
                                    break
                            if len(additionalData)==diff:
                                break
                if len(additionalData)==diff:
                    break
            if len(additionalData)==diff:
                break
    except:
        print("Failed to add extra negatives for :"+",".join(["Git: "+git,"Module: "+module,"diff: "+str(diff),"isPolluter: "+str(isPolluter),"isCleaner: "+str(isCleaner),"isBrittle: "+str(isBrittle)]))
        appendFile("Log.txt","Failed to add extra negatives for :"+",".join(["Git: "+git,"Module: "+module,"diff: "+str(diff),"isPolluter: "+str(isPolluter),"isCleaner: "+str(isCleaner),"isBrittle: "+str(isBrittle)]))
        additionalData=[]
    return additionalData

def processData(csv_data):
    """
    data={
        "git":{
            "sha":"",
            "module":{
                "filePath":{
                    "method":"code"
                }
            }
        }
    }
    """
    data={}
    for row in csv_data:
        git=row[1]
        sha=row[2]
        module=row[3]
        filePath=row[4]
        projectName=getProjName(git)
        if module !="":
            filePath=filePath.replace(projectName+"/"+module+"/src/test/java/","")
        else:
            filePath=filePath.replace(projectName+"/src/test/java/","")
        filePath=filePath.replace(".java","")
        filePath=filePath.replace("/",".")
        method=row[6]
        methodCode=row[7]
        if git not in data.keys():
            data[git]={}
        data[git]["sha"]=sha
        if module =="":
            module="NA"
        if module not in data[git].keys():
            data[git][module]={}
        if filePath not in data[git][module].keys():
            data[git][module][filePath]={}
        data[git][module][filePath][method]=methodCode
        #data[git][module][filePath][method]="code"
    return data

def beautifyCSV(csv_data):
    newData=[]
    for row in csv_data:

        if not row[0].endswith(".git"):
            print("changed : "+str(row))
            row[0]=row[0]+".git"
        if row[2].startswith("."):
            row[2]=row[2][1:]
        if row[2].startswith("/"):
            row[2]=row[2][1:]
        if not row[7].startswith("\""):
            row[7]="\""+row[7]
        if not row[7].endswith("\""):
            row[7]=row[7]+"\""
        if not row[8].startswith("\""):
            row[8]="\""+row[8]
        if not row[8].endswith("\""):
            row[8]=row[8]+"\""
        if not row[9].startswith("\""):
            row[9]="\""+row[9]
        if not row[9].endswith("\""):
            row[9]=row[9]+"\""
        newData.append(row)
    return newData

def generateBSSCombinationsCsv(csv_data, fileName):
    csv_data = [["gitURL","sha","module","brittle","SS/NSS","isBSSPair","brittle_code","SS/NSS_code"]] + csv_data
    fileName = os.path.join("output",fileName)
    createCSV(fileName,csv_data)

def main(fileName, headers,methodsFile):
    printFiles=True
    balanced=False
    saveCodes=True
    csv_data = readCSV(fileName, headers)
    csv_data = beautifyCSV(csv_data)
    data = createData(csv_data,saveCodes)
    #data = populateCounts(data)
    writeFile("sampleOrg.txt",str(data))
    dataP,dataC,dataSS = populateCombinations_seperate(data,saveCodes,balanced)      
    if printFiles:
        generateVPCombinationsCsv(dataP,"vpCombis_unbalanced.csv")
        generateVCCombinationsCsv(dataC,"vcCombis_unbalanced.csv")
        generateBSSCombinationsCsv(dataSS,"bssCombis_unbalanced.csv")
    allMethodsData=readCSV(methodsFile,True)    
    methods_data=processData(allMethodsData)
    writeFile("sampleAllMeth.txt",str(methods_data))
    balancedVC=createBalance(dataC,methods_data,data,False,True,False)
    balancedVP=createBalance(dataP,methods_data,data,True,False,False)
    balancedBSS=createBalance(dataSS,methods_data,data,False,False,True)
    if printFiles:
        generateVPCombinationsCsv(balancedVP,"vpCombis_balanced.csv")
        generateVCCombinationsCsv(balancedVC,"vcCombis_balanced.csv")
        generateBSSCombinationsCsv(balancedBSS,"bssCombis_balanced.csv")
    validateBalance(dataC,dataP,balancedVC,balancedVP)
    validateBalanceBrittle(dataSS,balancedBSS)

if __name__ == "__main__":
    mkdir("output")
    inputFile = "data.csv"
    methodsFile="allMethodsData.csv"
    headers=True
    main(inputFile,headers,methodsFile)