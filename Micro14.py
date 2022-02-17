#------------------------------------------------------------------
#	                    LIBRARIES IMPORT
#------------------------------------------------------------------
import os
import configparser
import multiprocessing
import time
from datetime import datetime, timedelta
import subprocess
import random
import sys
import json
import logging
from pythonjsonlogger import jsonlogger
import fnmatch
handler = None
logger = None

aapt = None
global flag
#------------------------------------------------------------------
#                     LOG CONFIGURATION
#------------------------------------------------------------------
import logging as log
from pythonjsonlogger import jsonlogger

handler = None
logger = None


def init_logger(file):
    global handler, logger
    handler = log.FileHandler(file)
    format_str = '%(levelname)s%(asctime)s%(filename)s%(funcName)s%(lineno)d%(message)'
    formatter = jsonlogger.JsonFormatter(format_str)
    handler.setFormatter(formatter)
    logger = log.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(log.INFO)
    return logger


def stop_logger():
    logger.removeHandler(handler)
    handler.close()

logger = init_logger('logs.privapp.log')
##########################################################
#                         AAPT WRAPPERS                 #
##########################################################
#This function print a message with the time when it-s called
def log(tag, message):
    try:
        utc_time = datetime.utcnow()
    #Format of Representation of the date *(YEAR-MONTH-DAY-HOUR-MINUT-SECOND)
        utc_str = utc_time.strftime('%Y-%m-%d-%H:%M:%S')
    #Print the format date by console
        print('(%s) %s -- %s' % (tag, utc_str, message))
    except Exception as error:
        logging.error(error)


# This function verify the dependences to execute functins which use aapt
def parse_config(config_file):
    try:
        # Verify the path of the config_file
        logging.debug("The comprobation of config_file begging")
        assert os.path.isfile(config_file), '%s is not a valid file or path to file' % config_file
        config = configparser.ConfigParser()
        config.read(config_file)
        # Verify the sdk was in the config_file
        assert 'sdk' in config.sections(), 'Config file %s does not contain an sdk section' % config_file
        assert 'AAPTPath' in config[
            'sdk'], 'Config file %s does not have an AAPTPath value in the sdk seciton' % config_file
        # Declarate the path por the function aapt comand
        aapt_path = config['sdk']['AAPTPath']
        assert os.path.isfile(aapt_path), 'aapt binary not found in %s' % aapt_path
        global aapt
        # Delarate a global variable, it can use in anywhere of the code
        aapt = aapt_path

    except Exception as error:
        logging.error(error)


# This function asecure the arguments of the command aapt
def aapt_call(command, args):
    try:
        global aapt
        # Verify the variable aapt had been initialized
        assert aapt is not None, 'SDK configuration not yet initialized, need to init() first'
        aapt_cmd = [aapt, command]
        aapt_cmd.extend(args)
        log('AAPT', aapt_cmd)
        result = None
        result =  subprocess.check_output(aapt_cmd, stderr=subprocess.STDOUT).decode('UTF-8', 'backslashreplace')
    except Exception as e:
        logger.error(e)
    else:
        return result

last_badging_apk = None
last_badging = None

#This functions can display all lines in AndroidManifest of specyfic path apk
def aapt_badging(apk_file):
    global last_badging_apk, last_badging
    try:
        if last_badging_apk is None or apk_file != last_badging_apk:
            last_badging = aapt_call('d', ['badging', apk_file])
            last_badging_apk = apk_file

    except Exception as e:
        logger.error(e)
    else:
        return last_badging

#This function can extract the permission
def aapt_permissions(apk_file):
    try:
        assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
        logger.debug('The function aapt_permissions was initiate')
        output = aapt_badging(apk_file)
        permissions = []
        if output is not None:
            lines = output.split('\n')
            permissions = [x.split('name=')[1].strip("'") for x in lines if x.startswith('uses-permission:')]
    except Exception as e:
        logger.error(e)
        return permissions
    else:
        return permissions

#This function display the lines of Android Manifest
def aapt_package(apk_file):
    try:
        assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
        logger.debug('This function was initiate')
        output = aapt_badging(apk_file)
        package = None
        if output is not None:
            lines = output.split('\n')
            package = [x for x in lines if x.startswith('package: name=')]
            assert len(package) == 1, 'More than one aapt d badging line starts with "package: name="'
            package = package[0].split('name=')[1].split(' versionCode=')[0].strip("'")
    except Exception as e:
        logger.error(e)
    else:
        return package

#This function display the version of the app's code
def aapt_versionName(apk_file):
    try:
        assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
        logger.debug('This function was initiate')
        output = aapt_badging(apk_file)
        package = None
        if output is not None:
            lines = output.split('\n')
            package = [x for x in lines if x.startswith('package: name=')]
            assert len(package) == 1, 'More than one aapt d badging line starts with "package: name="'
            package = package[0].split('name=')[1].split(' versionName=')[1].strip("'")
            return package
    except Exception as e:
        logger.error(e)
        #return package
    else:
        return package

#This function can display the app's version
def aapt_version_code(apk_file):
    try:
        assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
        output = aapt_badging(apk_file)
        version_code = None
        if output is not None:
            lines = output.split('\n')
            package = [x for x in lines if x.startswith('package: name=')]
            assert len(package) == 1, 'More than one aapt d badging line starts with "package: name="'
            version_code = package[0].split('versionCode=')[1].split(' versionName=')[0].strip("'")

    except Exception as e:
        logger.error(e)
    else:
        return version_code

#---------------------------------------------------------------------------------------
#                     FUNTIONS FOR MICROSERVICE 1
#---------------------------------------------------------------------------------------
#This function upload from permissions list
def load_lstPermission(path_json):
    try:
        assert os.path.isfile(path_json), '%s is not a valid path of json file' % path_json
        logger.debug('This function was initiate')
        lstCheck = []
        opc = 'r'
        with open(path_json, opc) as lstOutput:
            lstCheck = json.load(lstOutput)
    except Exception as e:
        logger.error(e)
    else:
        return lstCheck
#This funcion comparate the app's permissions and list permissions
def comparationLst(Permissions, Check):
    try:
        assert Permissions is not None, 'We need initiate a Permissions list'
        assert Check is not None, 'We need initiate a Checking list'
        logger.debug('This function was initiate')
        flag = False
        dangerous = []
        logger.debug('The function comparationLst was initiate')
        for x in Permissions:
            for y in Check:
                if (x == y['description']):
                    dangerous.append(x)
                    flag = True
    except Exception as e:
        logger.error(e)
    else:
        return [flag, dangerous]
#This funcition permit to obtain specific string about permissions
def depurePermissions(Permissions):
    try:
        assert Permissions is not None, 'We need initiatea Permissions list'
        logger.debug('The function was initiate')
        result = []
        for x in Permissions:
            z = x.split('.')[x.count('.')].split(" ")[0].split("'")[0]
            result.append(z)
    except Exception as e:
        logger.error(e)
    else:
        return result
#This function permit write logs of the script
def writeJson(lstResult, lstDangerous):
    lstWrite = []
    try:
        assert lstResult is not None, 'We need initiate a Permissions list'
        assert lstDangerous is not None, 'We need initiate a Dangerous Permissions list'
        logger.debug('The function was initiate')
        for i in range(0, len(lstResult), 1):
            lstWrite.append({
                'id': i,
                'name': lstResult[i],
                'description': 'NA'
            })
        for j in range(0, len(lstDangerous), 1):
            lstWrite.append({
                'id': j,
                'name': lstDangerous[j],
                'description': 'Dangerous'
            })
        #assert os.path.isfile(path), '%s is not a valid path of json file' % path
        with open('result/permisos'+str(datetime.utcnow())+'.json', 'w') as fp:
            fp.write(
                ',\n'.join(json.dumps(i) for i in lstWrite) +
                '\n')
    except Exception as e:
        logger.error(e)

#This function comprobate the input arguments
# def InputArgs():
#     logger.debug("Comprobate the input arguments")
#     try:
#         assert len(sys.argv) == 2, 'ERROR: You do not ingress 1 arguments'
#     except Exception as error:
#         logger.error(error)
#         log('InputArgs', error)
#         return False
#     else:
#         True
def apk_list(path):
    try:
        datos = []
        with open(path) as fname:
            lineas = fname.readlines()
            for linea in lineas:
                datos.append(linea.strip('\n'))
                
    except Exception as error:
        logger.error(error)
    else:
        return datos
# #----------------------------------------------------------------
#                       MAIN CODE
#----------------------------------------------------------------
#Comprobation of input arguments for the execute

logger.info("The Script was initiate")

def Service1():
    print('Enter to the Microserice 1')
    path = input()
    elements  = apk_list(path)
    for i in elements:
        print(i)
        print('Executing the microservice')
        try:
            parse_config("config_file")
            lstPermissions = aapt_permissions(i)
            lstResult = depurePermissions(lstPermissions)
            dir_PermissionsDangerous = 'lstPermissionsDangerous.json'
            lstCheck = load_lstPermission(dir_PermissionsDangerous)
            [flag, lstDangerous] = comparationLst(lstResult, lstCheck)
            if flag == True:
                print('This app need a privacy policy')
            writeJson(lstResult, lstDangerous)
            logger.info("The microservice was sucessfull")

        except Exception as error:
            logger.error(e)
            
    print('Exit to the microservice')
####
##Excute
###

Service1()
   
logger = stop_logger()





