from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_caching import Cache
from config import *
from models import *

app = Flask(__name__, static_url_path='/assets', static_folder='static')
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
app.secret_key = 'Secret_key_DevsFlex_1#9$0&2@'

csrf = CSRFProtect()
csrf.init_app(app)
cache = Cache(app)

def main_sessionVerify():
    #0 = No Logged
    #1 = Logged
    session_id = session.get('session_id', None)
    user_id = session.get('user_id', None)

    if not session_id:
        return 0    
    elif not user_id:
        return 0
    
    session_verify = model_user_sessions.get(action = "session_id", session_id = session_id)
    if not session_verify:
        session.clear()
        return 0
    elif user_id != session_verify["user"].id:
        session.clear()
        return 0
    
    return 1


def cache_enabled():
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        return False
    
    return True

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']) #@cache.cached(timeout = 300, unless = cache_enabled)
def main_web(path):    
    try:
        v_config_splitList = [config_splitList('/', path, i) for i in range(10)]
        v_requestForm = request.form
        v_sessionVerify =  main_sessionVerify()
        v_session_id = session.get('session_id', None)
        v_user_id = session.get('user_id', None)
        datetime_utc = datetime.utcnow()
        datetime_now = datetime.now()

        #MAIN
        if request.method == 'GET' and path in ['']:
            return 'MAIN'
        
        #AUTH
        elif request.method == 'GET' and path in ['auth', 'auth/', 'auth/sign-in', 'auth/sign-up']:
            if v_sessionVerify == 1:
                next_param = request.args.get('next')
                if next_param and config_isValidURL(next_param):
                    return redirect(next_param)
                
                return redirect('/')
            
            theme = request.cookies.get('theme')
            return render_template('/auth/index.html', theme = theme)

        #AUTH LOGOUT
        elif request.method == 'GET' and path == 'auth/logout':
            if v_sessionVerify == 1:
                model_user_sessions.delete(v_session_id)

            session.clear()
            return redirect('/auth')
        
        #PANEL
        elif request.method == 'GET' and path in ['panel']:
            return render_template('/panel/index.html')
        
        #API
        elif v_config_splitList[0] == 'api':             
            #API WEB
            if v_config_splitList[1] == 'web':
                action_param = request.args.get('action')                     
                action = v_requestForm.get('action')
                
                #WIDGETS
                if request.method == 'GET' and v_config_splitList[2] == 'widget':
                    #AUTH
                    if v_sessionVerify == 0 and v_config_splitList[3] == 'auth':
                        if v_config_splitList[4] == 'sign-in' and not v_config_splitList[5]:
                            return jsonify({'success': True, 'html': render_template('/auth/sign-in.html')})
                        elif v_config_splitList[4] == 'sign-up' and not v_config_splitList[5]:
                            return jsonify({'success': True, 'html': render_template('/auth/sign-up.html')})
                    
                #DATA
                elif v_config_splitList[2] == 'data':
                    if v_config_splitList[3] == 'auth' and not v_config_splitList[4]:                    
                        if v_sessionVerify == 0 and request.method == 'POST' and action == 'sign-up':
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
                                                  
                            email_verify = model_users.get(action = 'email', email = email)
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
                            signup = model_users.insert(user_id, name, surname, email, passw)
                            if not signup:
                                return jsonify({'success': False, 'msg': 'No se pudo completar el registro. Por favor, inténtelo de nuevo. Si el problema persiste, no dude en ponerse en contacto con nosotros para obtener ayuda.'})
                            
                            return jsonify({'success': True, 'msg': 'Registro correcto, ahora puedes iniciar sesión. Redireccionando...'})
                        elif v_sessionVerify == 0 and request.method == 'POST' and action == 'sign-in':
                            email = v_requestForm.get('email')
                            if not config_validateForm(form = email, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                            
                            password = v_requestForm.get('password')
                            if not config_validateForm(form = password, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione una contraseña válida e inténtelo de nuevo.'})

                            email_verify = model_users.get(action = 'email', email = email)
                            if not email_verify:
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo o contraseña válidos e inténtelo de nuevo.'})
                            
                            if not bcrypt.verify(password, email_verify['password']):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo o contraseña válidos e inténtelo de nuevo.'})
                            
                            session_id = str(uuid.uuid4())
                            user_agent = request.headers.get('User-Agent', None)

                            signin = model_user_sessions.insert(session_id, user_agent, email_verify['_id'])
                            if not signin:
                                return jsonify({'success': False, 'msg': 'No se pudo iniciar sesión. Por favor, inténtelo de nuevo. Si el problema persiste, no dude en ponerse en contacto con nosotros para obtener ayuda.'})
                            
                            session["user_id"] = email_verify['_id']
                            session["session_id"] = session_id
                            return jsonify({'success': True, 'msg': 'Inicio de sesión correcto. ¡Bienvenido/a! Redireccionando...'})
                        elif v_sessionVerify == 1 and request.method == 'GET' and action_param == 'token':
                            expiration_time = datetime_utc + timedelta(minutes=1)
                            payload = {'session_id': v_session_id, 'exp': expiration_time}
                            access_token = jwt.encode(payload, app.secret_key, algorithm = 'HS256')
                            next_param = request.args.get('next')   
                            if next_param and config_isValidURL(next_param):
                                token_param = urlencode({'token': access_token})
                                parsed_url = urlparse(next_param)
                                new_query = token_param if not parsed_url.query else f'{parsed_url.query}&{token_param}'
                                new_url = urlunparse(parsed_url._replace(query=new_query))
                                return redirect(new_url)
                                                
                            return redirect('/')

            return jsonify({'success': False, 'code': 'S404', 'msg': '¡Página no encontrada! Verifique la ruta.'}), 404

        return 'ERROR 404' 
    except Exception as e:
        print(e)
        #api_savefile(os.path.join(app.root_path, 'log', 'web.txt'), f'[C{sys.exc_info()[-1].tb_lineno}] {e}')
        return jsonify({'success': False, 'code': f'S500C{sys.exc_info()[-1].tb_lineno}', 'msg': '¡Ocurrió un error! El error se informó correctamente y estaremos trabajando para solucionarlo.'}), 500

@app.route('/api/web/token/csrf', methods = ['GET'])
@csrf.exempt
def api_webTokenCSRF():
    return jsonify({'success': True, 'token':  generate_csrf()}), 200

@app.errorhandler(400)
def main_error_400(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S400', 'msg': 'Bad request.'}), 400
    
    return 'Error 400'

@app.errorhandler(401)
def main_error_401(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S401', 'msg': 'Unauthorized.'}), 401
    
    return 'Error 401'

@app.errorhandler(403)
def main_error_403(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S403', 'msg': 'Forbidden.'}), 403
    
    return 'Error 403'

@app.errorhandler(404)
def main_error_404(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S404', 'msg': 'Page not found.'}), 404
    
    return 'Error 404'

@app.errorhandler(405)
def main_error_405(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S405', 'msg': 'Method not allowed.'}), 404
    
    return 'Error 405'

@app.errorhandler(500)
def main_error_500(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S500', 'msg': 'An error occurred! The error was reported correctly and we will be working to fix it.'}), 500
    
    return 'Error 500'

@app.errorhandler(503)
def main_error_503(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S503', 'msg': 'Service unavailable.'}), 503
    
    return 'Error 503'

@app.errorhandler(505)
def main_error_505(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S505', 'msg': 'HTTP Version not supported.'}), 505
    
    return 'Error 505'

@app.before_request
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

if __name__ == '__main__':
    app.run(host = 'localhost', debug = config_app['debug'])