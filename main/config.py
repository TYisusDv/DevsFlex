
from datetime import datetime, timedelta
from passlib.hash import bcrypt
import json, uuid, requests, re, math, time, sys, random, shutil, os, base64, subprocess, psutil, glob, socket, string, html

config_hostname = socket.gethostname()
config_debug = False
db_mongo_name =  'flicksflex'

if config_hostname == 'jesus-linux':
    config_debug = True
    db_mongo_name =  'flicksflex'   

config_app = {
    'debug': config_debug,
    'db_mongo': {
        'name': db_mongo_name
    }
}

def config_splitList(s, text, n):
    try:
        return text.split(s)[n] if len(text.split(s)) > n else None
    except:
        return None

def config_validateForm(empty = False, form = None, min = None, max = None):
    if not empty:
        if not form:
            return False

        if not min is None:
            if len(form) < min:
                return False
            
        if not max is None:
            if len(form) > max:
                return False
                
    return True