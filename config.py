
from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_caching import Cache
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
import json, uuid, requests, re, math, time, sys, random, shutil, os, base64, subprocess, psutil, glob, socket, string, html, secrets, hashlib, jwt

config_hostname = socket.gethostname()

config_app = {
    'debug': True,
    'db_mongo': {
        'main': {
            'name': 'devsflex'
        },
        'restaurant': {
            'name': 'devsflex_restaurant'
        }
    },
    'url_main': 'http://127.0.0.1:5000',
    'url_restaurant': 'http://127.0.0.2:5001'
}

if config_hostname == 'jesus-linux':
    config_app['db_mongo']['main']['name'] = 'devsflex'
    config_app['db_mongo']['restaurant']['name'] = 'devsflex_restaurant'

config_routes_nocache = [
    '/auth/sign-in',
    '/auth/sign-up',
    '/auth/logout'
]

config_routes_restaurant = [
    '',
    'dashboard',
    'manage/orders',
    'manage/order/types',
    'manage/order/type/add',
    'manage/order/type/edit',
    'manage/customers',
    'manage/products',
    'manage/product/categories',
    'manage/tables',
    'manage/table/reservations',
    'manage/users',
    'manage/user/add',
    'manage/user/edit',
]

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

def config_urlParam(url, param, value):
    parsed_url = urlparse(url)
    query_params = parse_qsl(parsed_url.query)
    query_params.append((param, value))
    new_query = urlencode(query_params)
    new_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment)
    )
    return new_url

def config_searchRegex(search = None):
    if search:
        words = search.split()
        query_regex = ".*" + ".*".join(words) + ".*"
        return query_regex
    else:
        return ''

def config_convertDate(date):
    format_entry = "%Y-%m-%d %H:%M:%S.%f"
    format_fin = "%m/%d/%Y %H:%M:%S"
    
    date_object = datetime.strptime(str(date), format_entry)
    date_converted = date_object.strftime(format_fin)
    
    return date_converted