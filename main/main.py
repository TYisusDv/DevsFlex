from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_caching import Cache
from config import *

app = Flask(__name__, static_url_path='/assets', static_folder='static')
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
app.secret_key = 'Secret_key_DevsFlex_1#9$0&2@'

csrf = CSRFProtect()
csrf.init_app(app)
cache = Cache(app)

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

        #MAIN
        if request.method == 'GET' and path in ['']:
            return 'MAIN'
        
        #AUTH
        elif request.method == 'GET' and path in ['auth', 'auth/', 'auth/sign-in', 'auth/sign-up']:
            theme = request.cookies.get('theme')
            return render_template('/auth/index.html', theme = theme)
        
        #PANEL
        elif request.method == 'GET' and path in ['panel']:
            return render_template('/panel/index.html')
        
        #API
        elif v_config_splitList[0] == 'api':             
            #API WEB
            if v_config_splitList[1] == 'web':
                #WIDGETS
                if request.method == 'GET' and v_config_splitList[2] == 'widget':
                    #AUTH
                    if v_config_splitList[3] == 'auth':
                        if v_config_splitList[4] == 'sign-in' and not v_config_splitList[5]:
                            return jsonify({'success': True, 'html': render_template('/auth/sign-in.html')})
                        elif v_config_splitList[4] == 'sign-up' and not v_config_splitList[5]:
                            return jsonify({'success': True, 'html': render_template('/auth/sign-up.html')})
                    
                #DATA
                elif v_config_splitList[2] == 'data':
                    if v_config_splitList[3] == 'auth' and not v_config_splitList[4]:
                        action = v_requestForm.get('action')
                        if request.method == 'POST' and action == 'sign-up':
                            name = v_requestForm.get('name')
                            if not config_validateForm(form = name, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un nombre válido e inténtelo de nuevo.'})

                            surname = v_requestForm.get('surname')
                            if not config_validateForm(form = surname, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un apellido válido e inténtelo de nuevo.'})
                            
                            email = v_requestForm.get('email')
                            if not config_validateForm(form = email, min = 1) or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                            
                            password = v_requestForm.get('password')
                            if not config_validateForm(form = password, min = 8):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione una contraseña válida con al menos 8 caracteres e inténtelo de nuevo.'})
                            elif not re.search(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!])(?!.*\s).{8,}$', password):
                                return jsonify({'success': False, 'msg': 'La contraseña debe contener al menos una letra mayúscula, una letra minúscula, un número, un carácter especial y tener al menos 8 caracteres. Por favor, inténtelo de nuevo.'})
                            
                            cpassword = v_requestForm.get('cpassword')
                            if not config_validateForm(form = cpassword, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione la confirmacion de la contraseña válida e inténtelo de nuevo.'})

                            return jsonify({'success': True, 'msg': 'Registro correcto, ahora puedes iniciar sesión. Redireccionando...'})
                        elif request.method == 'POST' and action == 'sign-in':
                            email = v_requestForm.get('email')
                            if not config_validateForm(form = email, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                            
                            password = v_requestForm.get('password')
                            if not config_validateForm(form = password, min = 1):
                                return jsonify({'success': False, 'msg': 'Por favor, proporcione una contraseña válida e inténtelo de nuevo.'})

                            return jsonify({'success': True, 'msg': 'Inicio de sesión correcto. ¡Bienvenido/a! Redireccionando...'})
            
            return jsonify({'success': False, 'code': 'S404', 'msg': '¡Página no encontrada! Verifique la ruta.'}), 404

        return 'ERROR 404' 
    except Exception as e:
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