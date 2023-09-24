from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_caching import Cache
from config import *
from models import *

app_main = Flask(__name__, static_url_path='/assets', static_folder='static')
app_main.config['CACHE_TYPE'] = 'redis'
app_main.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app_main.config['CACHE_DEFAULT_TIMEOUT'] = 300
app_main.secret_key = 'Secret_key_DevsFlex_1#9$0&2@'

csrf = CSRFProtect()
csrf.init_app(app_main)
cache = Cache(app_main)

def main_sessionVerify():
    #0 = No Logged
    #1 = Logged
    session_id = session.get('session_id')
    user_id = session.get('user_id')

    if not session_id:
        return 0    
    elif not user_id:
        return 0
    
    session_verify = model_main_user_sessions.get(action = "session_id", session_id = session_id)
    if not session_verify:
        session.clear()
        return 0
    elif user_id != session_verify["user"].id:
        session.clear()
        return 0
    
    return 1

def cache_enabled():
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        if request.path in config_routes_nocache:
            return False
    
    return True

@app_main.route('/', defaults={'path': ''})
@app_main.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])#@cache.cached(timeout = 300, unless = cache_enabled)
def main_web(path):    
    try:
        v_config_splitList = [config_splitList('/', path, i) for i in range(10)]

        v_requestForm = request.form
        v_sessionVerify =  main_sessionVerify()
        v_session_id = session.get('session_id')
        v_user_id = session.get('user_id')
        v_action = v_requestForm.get('action')
        v_action_param = request.args.get('action')
        datetime_utc = datetime.utcnow()
        datetime_now = datetime.now()

        if request.method == 'GET' and path == '':
            return render_template('/index.html')
        
        elif request.method == 'GET' and path in ['auth', 'auth/', 'auth/sign-in', 'auth/sign-up']:
            if v_sessionVerify == 1:
                if request.args.get('next') and config_isValidURL(request.args.get('next')):
                    return redirect(request.args.get('next'))
                
                return redirect('/')
            
            theme = request.cookies.get('theme')
            return render_template('/auth/index.html', theme = theme)

        elif request.method == 'GET' and path == 'auth/logout':
            if v_sessionVerify == 1:
                model_main_user_sessions.delete(action = 'session', session_id = v_session_id)

            session.clear()
            return redirect('/auth')
    
        elif request.method == 'GET' and path in ['panel']:
            return render_template('/panel/index.html')
        
        if v_sessionVerify == 0:
            if request.method == 'GET' and path == 'api/web/widget/auth/sign-in':
                return jsonify({'success': True, 'html': render_template('/auth/sign-in.html')})
            elif request.method == 'GET' and path == 'api/web/widget/auth/sign-up':
                return jsonify({'success': True, 'html': render_template('/auth/sign-up.html')})
            elif request.method == 'POST' and path == 'api/web/data/auth':
                if v_action == 'sign-up':
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1) or not config_verifyText(name):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un nombre válido e inténtelo de nuevo.'})
                    
                    name = html.escape(name.strip().capitalize())

                    surname = v_requestForm.get('surname')
                    if not config_validateForm(form = surname, min = 1) or not config_verifyText(surname):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un apellido válido e inténtelo de nuevo.'})
                    
                    surname = html.escape(surname.strip().capitalize())

                    email = v_requestForm.get('email')
                    if not config_validateForm(form = email, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                    
                    email = email.strip().lower()

                    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})                           
                                            
                    email_verify = model_main_users.get(action = 'email', email = email)
                    if email_verify:
                        return jsonify({'success': False, 'msg': 'El correo ya está en uso. Por favor, proporcione un correo válido e inténtelo de nuevo.'})

                    password = v_requestForm.get('password')
                    if not config_validateForm(form = password, min = 8):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una contraseña válida con al menos 8 caracteres e inténtelo de nuevo.'})
                    elif not re.search(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!])(?!.*\s).{8,}$', password):
                        return jsonify({'success': False, 'msg': 'La contraseña debe contener al menos una letra mayúscula, una letra minúscula, un número, un carácter especial y tener al menos 8 caracteres. Por favor, inténtelo de nuevo.'})
                    
                    cpassword = v_requestForm.get('cpassword')
                    if not config_validateForm(form = cpassword, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione la confirmacion de la contraseña válida e inténtelo de nuevo.'})
                    
                    if password != cpassword:
                        return jsonify({'success': False, 'msg': 'Por favor, verifique ambas contraseñas e inténtelo de nuevo.'})                            
                    
                    user_id = config_genUniqueID()
                    passw = bcrypt.hash(password)

                    signup = model_main_users.insert(action = 'client', user_id = user_id, name = name, surname = surname, email = email, password = passw)
                    if not signup:
                        return jsonify({'success': False, 'msg': 'No se pudo completar el registro. Por favor, inténtelo de nuevo. Si el problema persiste, no dude en ponerse en contacto con nosotros para obtener ayuda.'})
                    
                    return jsonify({'success': True, 'msg': 'Registro correcto, ahora puedes iniciar sesión. Redireccionando...'})
                elif v_action == 'sign-in':
                    email = v_requestForm.get('email')
                    if not config_validateForm(form = email, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                    
                    password = v_requestForm.get('password')
                    if not config_validateForm(form = password, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una contraseña válida e inténtelo de nuevo.'})

                    email_verify = model_main_users.get(action = 'email', email = email)
                    if not email_verify:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo o contraseña válidos e inténtelo de nuevo.'})
                    
                    if not bcrypt.verify(password, email_verify['password']):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo o contraseña válidos e inténtelo de nuevo.'})
                    
                    session_id = str(uuid.uuid4())
                    user_agent = request.headers.get('User-Agent')

                    signin = model_main_user_sessions.insert(action = 'client', session_id = session_id, useragent = user_agent, user_id = email_verify['_id'])
                    if not signin:
                        return jsonify({'success': False, 'msg': 'No se pudo iniciar sesión. Por favor, inténtelo de nuevo. Si el problema persiste, no dude en ponerse en contacto con nosotros para obtener ayuda.'})
                    
                    session["user_id"] = email_verify['_id']
                    session["session_id"] = session_id
                    return jsonify({'success': True, 'msg': 'Inicio de sesión correcto. ¡Bienvenido/a! Redireccionando...'})
            elif request.method == 'GET' and path == 'api/web/data/auth' and v_action_param == 'token':
                url_next = config_app['url_main'] + '/auth/sign-in'

                if request.args.get('next') and config_isValidURL(request.args.get('next')):
                    url_next = config_urlParam(url_next, 'next', request.url)

                return redirect(url_next)
        
        elif v_sessionVerify == 1:
           if request.method == 'GET' and path == 'api/web/data/auth' and v_action_param == 'token':
                if not request.args.get('next') or not config_isValidURL(request.args.get('next')):
                    return redirect('/')
                        
                expiration_time = datetime_utc + timedelta(minutes=1)
                payload = {'session_id': v_session_id, 'user_id': v_user_id, 'exp': expiration_time}
                token = jwt.encode(payload, app_main.secret_key, algorithm = 'HS256')                                                          

                url_next = config_urlParam(request.args.get('next'), 'token', token)
                
                return redirect(url_next)

        if request.method == 'POST' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'code': 'S404', 'msg': 'Page not found.'}), 404
        elif request.method == 'GET' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'html': render_template('/error.html', code = '404', msg = 'Page not found.')}), 404

        return render_template('/error.html', code = '404', msg = 'Page not found.'), 404
    except Exception as e:
        if request.method == 'POST' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'code': f'S500C{sys.exc_info()[-1].tb_lineno}', 'msg': f'[S500C{sys.exc_info()[-1].tb_lineno}] An error occurred! The bug has been successfully reported and we will be working to fix it.'}), 500
        elif request.method == 'GET' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'html': render_template('/error.html', code = '500', msg = f'[S500C{sys.exc_info()[-1].tb_lineno}] An error occurred! The bug has been successfully reported and we will be working to fix it.')}), 500
        
        #api_savefile(os.path.join(app.root_path, 'log', 'web.txt'), f'[C{sys.exc_info()[-1].tb_lineno}] {e}')
        return render_template('/error.html', code = '500', msg = f'[S500C{sys.exc_info()[-1].tb_lineno}] An error occurred! The bug has been successfully reported and we will be working to fix it.'), 500

@app_main.before_request
def main_setCookie():
    try:
        if 'theme' not in request.cookies:
            expiration_date = datetime.now() + timedelta(days=36500)

            response = make_response(redirect(request.path))
            response.set_cookie('theme', 'white', expires=expiration_date)
            return response
    except Exception as e:
        #api_savefile(os.path.join(app.root_path, 'log', 'web.txt'), f'[C{sys.exc_info()[-1].tb_lineno}] {e}')
        pass
    
@app_main.route('/api/web/token/csrf', methods = ['GET'])
@csrf.exempt
def api_webTokenCSRF():
    return jsonify({'success': True, 'token':  generate_csrf()}), 200

@app_main.errorhandler(400)
def main_error_400(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S400', 'msg': 'Bad request.'}), 400
    
    return render_template('/error.html', code = '400', msg = 'Bad request.'), 400

@app_main.errorhandler(401)
def main_error_401(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S401', 'msg': 'Unauthorized.'}), 401
    
    return render_template('/error.html', code = '404', msg = 'Unauthorized.'), 401

@app_main.errorhandler(403)
def main_error_403(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S403', 'msg': 'Forbidden.'}), 403
    
    return render_template('/error.html', code = '404', msg = 'Forbidden.'), 403

@app_main.errorhandler(404)
def main_error_404(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S404', 'msg': 'Page not found.'}), 404
    
    return render_template('/error.html', code = '404', msg = 'Page not found.'), 404

@app_main.errorhandler(405)
def main_error_405(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S405', 'msg': 'Method not allowed.'}), 405
    
    return render_template('/error.html', code = '404', msg = 'Method not allowed.'), 405

@app_main.errorhandler(500)
def main_error_500(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S500', 'msg': 'An error occurred! The error was reported correctly and we will be working to fix it.'}), 500
    
    return render_template('/error.html', code = '500', msg = f'An error occurred! The bug has been successfully reported and we will be working to fix it.'), 500

@app_main.errorhandler(503)
def main_error_503(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S503', 'msg': 'Service unavailable.'}), 503
    
    return render_template('/error.html', code = '404', msg = 'Service unavailable.'), 503

@app_main.errorhandler(505)
def main_error_505(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S505', 'msg': 'HTTP Version not supported.'}), 505
    
    return render_template('/error.html', code = '404', msg = 'HTTP Version not supported.'), 505