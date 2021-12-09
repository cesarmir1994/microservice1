#---------------------------------
#	LIBRARIES IMPORT
#---------------------------------
import os
import configparser
import multiprocessing
import time
from datetime import datetime, timedelta
import subprocess
import random
import sys
import json

aapt = None
global flag

##########################################################
#                         AAPT WRAPPERS                 #
##########################################################
# This function print a message with the time when it-s called
def log(tag, message):
    utc_time = datetime.utcnow()
    utc_str = utc_time.strftime('%Y-%m-%d-%H:%M:%S')

    print('(%s) %s -- %s' % (tag, utc_str, message))


# This function verify the dependences to execute functins which use aapt
def parse_config(config_file):
    #Verify the path of the config_file
    assert os.path.isfile(config_file), '%s is not a valid file or path to file' % config_file

    config = configparser.ConfigParser()
    config.read(config_file)
    #Verify the sdk was in the config_file
    assert 'sdk' in config.sections(), 'Config file %s does not contain an sdk section' % config_file
    
    assert 'AAPTPath' in config[
        'sdk'], 'Config file %s does not have an AAPTPath value in the sdk seciton' % config_file
    #Declarate the path por the function aapt comand
    aapt_path = config['sdk']['AAPTPath']

    assert os.path.isfile(aapt_path), 'aapt binary not found in %s' % aapt_path

    global aapt
    #Delarate a global variable, it can use in anywhere of the code
    aapt = aapt_path
# This function asecure the arguments of the command aapt
def aapt_call(command, args):
    global aapt
    #Verify the variable aapt had been initialized
    assert aapt is not None, 'SDK configuration not yet initialized, need to init() first'
    aapt_cmd = [aapt, command]
    aapt_cmd.extend(args)
    log('AAPT', aapt_cmd)
    result = None
    try:
        result =  subprocess.check_output(aapt_cmd, stderr=subprocess.STDOUT).decode('UTF-8', 'backslashreplace')
    except Exception as e:
        log('AAPT-ERROR', str(e))
    finally:
        return result

last_badging_apk = None
last_badging = None

#This functions can display all lines in AndroidManifest of specyfic path apk
def aapt_badging(apk_file):
    global last_badging_apk, last_badging
    if last_badging_apk is None or apk_file != last_badging_apk:
        last_badging = aapt_call('d', ['badging', apk_file])
        last_badging_apk = apk_file
        
    return last_badging

#This function can extract the permission
def aapt_permissions(apk_file):
    assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
    output = aapt_badging(apk_file)
    permissions = []
    if output is not None:
        lines = output.split('\n')
        permissions = [x.split('name=')[1].strip("'") for x in lines if x.startswith('uses-permission:')]
        
    return permissions

#This function display the
def aapt_package(apk_file):
    assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
    output = aapt_badging(apk_file)
    package = None
    if output is not None:
        lines = output.split('\n')
        package = [x for x in lines if x.startswith('package: name=')]
        assert len(package) == 1, 'More than one aapt d badging line starts with "package: name="'
        package = package[0].split('name=')[1].split(' versionCode=')[0].strip("'")

    return package

#This function display the version of the app's code
def aapt_versionName(apk_file):
    assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
    output = aapt_badging(apk_file)
    package = None
    if output is not None:
        lines = output.split('\n')
        package = [x for x in lines if x.startswith('package: name=')]
        assert len(package) == 1, 'More than one aapt d badging line starts with "package: name="'
        package = package[0].split('name=')[1].split(' versionName=')[1].strip("'")

    return package

#This function can display the app's version
def aapt_version_code(apk_file):
    assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
    output = aapt_badging(apk_file)
    version_code = None
    if output is not None:
        lines = output.split('\n')
        package = [x for x in lines if x.startswith('package: name=')]
        assert len(package) == 1, 'More than one aapt d badging line starts with "package: name="'
        version_code = package[0].split('versionCode=')[1].split(' versionName=')[0].strip("'")

    return version_code

def load_lstPermission(path_json):
    assert os.path.isfile(path_json), '%s is not a valid path of json file' % path_json
    opc = 'r'
    with open(path_json, opc) as lstOutput:
        lstCheck = json.load(lstOutput)
    return lstCheck

def comparationLst(lstPerm, lstChec):
    flag = False
    for x in lstPermissions:
        for y in lstCheck:
            if (x.split(".")[2] == y['description']):
                flag = True
    return flag

#--------------------------------
#	MAIN CODE
#--------------------------------

#Comprobation of input arguments for the execute
if len(sys.argv) == 2:
    path = sys.argv[1]
else:
    print ("ERROR: You should insert 1 argument")
    print ("Example: script.py /dir/miapp.apk")
    exit(0)
#hola_python()
#print("the path of apk is : ", path)
#This comprobation was fixed on the code
parse_config("/home/cesar/Desktop/Microservicio1/config_file")
# We obtain the permissions of the app
lstPermissions = aapt_permissions(path)
for x in lstPermissions:
    print(x.split('.')[x.count('.')])
#abc = [x.split('permission')[1].strip(".") for x in lstPermissions if x.startswith('android')]
#for i in abc:
#    print(i)
version = aapt_versionName(path)
#print(version)
lstCheck = load_lstPermission('lstDangerous.json')

flag = comparationLst(lstPermissions, lstCheck)
print("El resultado de la bandera es : ",flag)
packet = aapt_package(path)
print("El nombre de la app es ", packet)
ver = version.split("'")[0]
print("La version de la aplicacion es : ",ver)
