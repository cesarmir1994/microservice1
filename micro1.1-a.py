# ------------------------------------------------------------------
#	                    LIBRARIES IMPORT
# ------------------------------------------------------------------
import os
import configparser
import multiprocessing
import subprocess
import random
import sys
import json
# --------------------------------------------------
#                   GLOBAL VARIABLES
# --------------------------------------------------
last_badging_apk = None
last_badging = None
aapt = None
result_dir = 'result/'
# ------------------------------------------------------------------
#                     LOG CONFIGURATION				  #
# ------------------------------------------------------------------
import logging as log
from pythonjsonlogger import jsonlogger
# log agent initialization
def init_logger(file):
    global handler, logger
    handler = log.FileHandler(file)
    format_str = '%(levelname)s%(asctime)s%(filename)s%(funcName)s%(lineno)d%(message)'
    formatter = jsonlogger.JsonFormatter(format_str)
    handler.setFormatter(formatter)
    logger = log.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(log.DEBUG)
    return logger
# log agent termination
def stop_logger():
    logger.removeHandler(handler)
    handler.close()
# log agent definition
logger = init_logger('logs.privapp.log')
##########################################################
#                         AAPT WRAPPERS                 #
##########################################################
# This function verify the dependences to execute functins which use aapt
def parse_config(config_file):
    try:
        # Verify the path of the config_file
        logger.debug("The comprobation of config_file has been started")
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
    except Exception as e:
        reason = 'parse_config unavailable'
        logger.error('parse_config failed',
                     extra={'exception_message': str(e), 'reason': reason})
# This function asecure the arguments of the command aapt
def aapt_call(command, args):
    global aapt
    result = None
    try:
        logger.debug("aapt_call function has been started")
        # Verify the variable aapt had been initialized
        assert aapt is not None, 'SDK configuration not yet initialized, need to init() first'
        aapt_cmd = [aapt, command]
        aapt_cmd.extend(args)
        result = subprocess.check_output(aapt_cmd, stderr=subprocess.STDOUT).decode('UTF-8', 'backslashreplace')
    except Exception as e:
        reason = 'aapt_call unavailable'
        logger.error('aapt_call failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug("aapt_call function has been successful")
        return result
# This functions can display all lines in AndroidManifest of specyfic path apk
def aapt_badging(apk_file):
    global last_badging_apk, last_badging
    try:
        logger.debug("aapt_badging function has been started")
        if last_badging_apk is None or apk_file != last_badging_apk:
            last_badging = aapt_call('d', ['badging', apk_file])
            last_badging_apk = apk_file
    except Exception as e:
        reason = 'aapt_badging unavailable'
        logger.error('aapt_badging failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug("aapt_badging functiton has been successful")
        return last_badging
# This function can extract the permission
def aapt_permissions(apk_file):
    try:
        assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
        logger.debug('aapt_permissions function has been started')
        output = aapt_badging(apk_file)
        permissions = []
        if output is not None:
            lines = output.split('\n')
            permissions = [x.split('name=')[1].strip("'") for x in lines
                           if x.startswith('uses-permission:')]
    except Exception as e:
        reason = 'aapt_permissions unavailable'
        logger.error('aapt_permissions failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug('aapt_permissions function has been successful')
        return permissions
# This function extract the metadata of APK
def aapt_metadata(apk_file):
    package_name = None
    code_version = None
    try:
        assert os.path.isfile(apk_file), '%s is not a valid APK path' % apk_file
        logger.debug('aapt_metadata function has been started')
        output = aapt_badging(apk_file)
        if output is not None:
            lines = output.split('\n')
            aux = [x for x in lines if x.startswith('package:')]
            assert len(aux) == 1, 'More than one aapt'
            package_name = aux[0].split(' ')[1].split('=')[1].strip("'")
            code_version = aux[0].split(' ')[3].split('=')[1].strip("'")
    except Exception as e:
        reason = 'aapt_Name unavailable'
        logger.error('aapt_Name failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug('aapt_metadata function has been successful')
        return [package_name, code_version]
# ---------------------------------------------------------------------------------------
#                     FUNTIONS FOR MICROSERVICE 1
# ---------------------------------------------------------------------------------------
# This function upload from permissions list
def load_lstPermission(path_json):
    try:
        assert os.path.isfile(path_json), '%s is not a valid path of json file' % path_json
        logger.debug('load_lstPermission function has been started')
        lstCheck = []
        opc = 'r'
        with open(path_json, opc) as lstOutput:
            lstCheck = json.load(lstOutput)
    except Exception as e:
        reason = 'load_lstPermission unavailable'
        logger.error('load_lstPermission failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug('load_lstPermission function has been successful')
        return lstCheck
# This funcion comparate the app's permissions and list permissions
def comparationLst(Permissions, Check):
    try:
        assert Permissions is not None, 'We need initiate a Permissions list'
        assert Check is not None, 'We need initiate a Checking list'
        flag = False
        dangerous = []
        logger.debug('The function comparationLst has been started')
        for element in Permissions:
            for aux_element in Check:
                if (element == aux_element['description']):
                    dangerous.append(element)
                    flag = True
    except Exception as e:
        reason = 'comparationLst unavailable'
        logger.error('comparationLst failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug('comparationLst function has been successful')
        return [flag, dangerous]
# This funcition permit to obtain specific string about permissions
def depurePermissions(Permissions):
    result = []
    try:
        assert Permissions is not None, 'We need initiatea Permissions list'
        logger.debug('depurePermissions function has been started')
        for element in Permissions:
            permission = element.split('.')[element.count('.')].split(" ")[0].split("'")[0]
            result.append(permission)
    except Exception as e:
        reason = 'depurePermissions unavailable'
        logger.error('depurePermissions failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug('depurePermissions function has been successful')
        return result
# this function writes the results of microservice 1
def writeJson(lstResult, lstDangerous, version, name, flag):
    lstWrite = []
    lstApp = []
    try:
        logger.debug('writeJson function has been started')
        lstApp.append({'packagename': name,'version': version,
                       'privacyPolicy': flag})
        for aux in range(0, len(lstResult), 1):
            lstWrite.append({'id': aux,'name': lstResult[aux],
                             'description': 'NA'})
        for aux2 in range(0, len(lstDangerous), 1):
            lstWrite.append({'id': aux2,'name': lstDangerous[aux2],
                             'description': 'Sensitive'})
        with open(result_dir+'results.json', '+a') as fp:
            fp.write(',\n'.join(json.dumps(aux3) for aux3 in lstApp)+'\n')
            fp.write(',\n'.join(json.dumps(aux4) for aux4 in lstWrite)+'\n')
    except Exception as e:
        reason = 'writeJson unavailable'
        logger.error('writeJson failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        logger.debug('writeJson function has been successful')
# Function to list each element in a vector
def apk_list(path):
    data = []
    try:
        with open(path) as fname:
            lines = fname.readlines()
            for line in lines:
                data.append(line.strip('\n'))
    except Exception as error:
        reason = 'apk_list unavailable'
        logger.error('apk_list failed',
                     extra={'exception_message': str(e), 'reason': reason})
    else:
        return data
# #---------------------------------------------------------------
#                       MAIN CODE
# ----------------------------------------------------------------
def Service1():
    print('Entering the microserice 1')
    path = input()
    elements = apk_list(path)
    print()
    print('------------------------------------------------------')
    for element in elements:
        print('Executing microservice 1 in the APP '+element)
        print('------------------------------------------------------')
        logger.info('Executing the microservice 1')
        try:
            parse_config("config_file")
            print('Extracting permissions from manifest file')
            lstPermissions = aapt_permissions(element)
            lstResult = depurePermissions(lstPermissions)
            dir_PermissionsDangerous = 'listaSensible.json'
            lstCheck = load_lstPermission(dir_PermissionsDangerous)
            print('Comparing APK permissions with sensitive permissions list')
            [flag, lstDangerous] = comparationLst(lstResult, lstCheck)
            if flag:
                logger.info('APP must have a privacy policy')
                print('**** APP must have a privacy policy ****')
            [name, version] = aapt_metadata(element)
            print('Generating results')
            writeJson(lstResult, lstDangerous, version, name, flag)
            print('------------------------------------------------------')
            logger.info("Microservice was sucessfull")
        except Exception as error:
            logger.error(error)
    logger.info('Leaving Microservice 1')
    print()
    os.system("cat result/results.json")
    print()
###
# Excute
##
Service1()
# stopping agent log
logger = stop_logger()
