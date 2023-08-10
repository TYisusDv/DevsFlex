
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from urllib.parse import urlencode, urlparse, urlunparse
import json, uuid, requests, re, math, time, sys, random, shutil, os, base64, subprocess, psutil, glob, socket, string, html, secrets, hashlib, jwt

config_hostname = socket.gethostname()
config_debug = False
db_mongo_name =  'devsflex'

if config_hostname == 'jesus-linux':
    config_debug = True
    db_mongo_name =  'devsflex'   

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

def config_genUniqueID():
    datetime_now = datetime.now()
    salt = str(datetime_now.timestamp())
    token = secrets.token_hex(9)
    unique_string = hashlib.sha256((salt + token).encode('utf-8')).hexdigest()[:18]
    return unique_string.upper()

def config_verifyText(text):
    return all(char.isalpha() or char.isspace() for char in text)

def config_isValidURL(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme and parsed_url.netloc