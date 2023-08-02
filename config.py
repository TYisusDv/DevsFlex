
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