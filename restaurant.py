from config import *
from models import *

app_restaurant = Flask(__name__, static_url_path='/assets', static_folder='static')
app_restaurant.config['CACHE_TYPE'] = 'redis'
app_restaurant.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app_restaurant.config['CACHE_DEFAULT_TIMEOUT'] = 300
app_restaurant.secret_key = 'Secret_key_DevsFlex_1#9$0&2@'

csrf = CSRFProtect()
csrf.init_app(app_restaurant)
cache = Cache(app_restaurant)

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

@app_restaurant.route('/', defaults={'path': ''})
@app_restaurant.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])#@cache.cached(timeout = 300, unless = cache_enabled)
def main_web(path):    
    try:
        v_config_splitList = [config_splitList('/', path, i) for i in range(10)]

        v_requestForm = request.form
        v_requestArgs = request.args
        v_sessionVerify =  main_sessionVerify()
        v_session_id = session.get('session_id')
        v_user_id = session.get('user_id')
        v_action = v_requestForm.get('action')
        v_action_param = v_requestArgs.get('action')
        datetime_utc = datetime.utcnow()
        datetime_now = datetime.now()

        if request.method == 'GET' and path in config_routes_restaurant:
            if v_sessionVerify == 0:
                url_main = f'{config_app["url_main"]}/api/web/data/auth?action=token'
                new_url = config_urlParam(url_main, 'next', f'{config_app["url_restaurant"]}/api/web/data/auth?action=token')
                return redirect(new_url)

            return render_template('/restaurant/index.html')
        
        elif request.method == 'GET' and path == 'auth/logout':
            if v_sessionVerify == 1:
                model_main_user_sessions.delete(action = 'session', session_id = v_session_id)

            session.clear()
            return redirect(f'{config_app["url_main"]}/auth/logout')
        
        if v_sessionVerify == 0:
            if request.method == 'GET' and path == 'api/web/data/auth':
                if v_action_param == 'token':
                    token = request.args.get('token')
                    if token:
                        try:
                            payload = jwt.decode(token, app_restaurant.secret_key, algorithms = ['HS256'])
                            session['session_id'] = payload['session_id']
                            session['user_id'] = payload['user_id']
                        except jwt.ExpiredSignatureError:
                            return jsonify({"msg": "Token expirado"}), 401
                        except jwt.InvalidTokenError:
                            return jsonify({"msg": "Token inválido"}), 401
                        
                    return redirect('/')
        
        elif v_sessionVerify == 1:
            if request.method == 'GET' and path == 'api/web/widget/dashboard':
                return jsonify({'success': True, 'html': render_template('/restaurant/home/dashboard.html')})
            elif request.method == 'POST' and path == 'api/web/data/table':
                start = v_requestForm.get('start')
                if not config_validateForm(form = start, min = 1):
                    start = 0
                
                length = v_requestForm.get('length')
                if not config_validateForm(form = length, min = 1):
                    length = 10
                
                search = v_requestForm.get('search')
                if not config_validateForm(form = search, min = 1):
                    search = ''

                order_column = v_requestForm.get('order_column')
                if not config_validateForm(form = order_column, min = 1):
                    order_column = '_id'

                order_direction = v_requestForm.get('order_direction')
                if not config_validateForm(form = order_direction, min = 1):
                    order_direction = 'asc'

                data = []
                data_count = 0 

                if v_action == 'manage_users':
                    data = model_restaurant_users.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/user/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['user_role']['name'] = f'<span class="badge bg-primary">{item["user_role"]["name"]}</span>'
                        item['regdate'] = f'<span class="badge bg-primary">{config_convertDate(item["regdate"])}</span>'
                        
                    data_count = model_restaurant_users.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                elif v_action == 'manage_order_types':
                    data = model_order_types.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/order/type/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['status'] = '<span class="badge bg-primary-opacity"><i class="fa fa-circle"></i> Visible</span>' if item['status'] else '<span class="badge bg-danger-opacity"><i class="fa fa-circle"></i> Oculto</span>'
                        
                    data_count = model_order_types.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)

                return jsonify({'success': True, 'data': data, 'recordsTotal': data_count, 'recordsFiltered': data_count})
            elif request.method == 'GET' and path == 'api/web/widget/manage/order/types':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/order_types.html')})    
            elif request.method == 'POST' and path == 'api/web/data/manage/order/types':
                if v_action == 'add':
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'}) 
                    
                    insert = model_order_types.insert(action = 'one', name = name)
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    order_type_id = v_requestForm.get('id')
                    item = model_order_types.get(action = 'one', order_type_id = int(order_type_id) if order_type_id and order_type_id.isnumeric() else None)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})
                
                    status = v_requestForm.get('status')
                    if not status:
                        status = 'off'
                    
                    status = True if status == 'on' else False
                    update = model_order_types.update(action = 'one', order_type_id = int(order_type_id), name = name, status = status)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                
            elif request.method == 'GET' and path == 'api/web/widget/manage/order/type/add':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/order_types/add.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/order/type/edit':
                order_type_id = v_requestArgs.get('id')
                item = model_order_types.get(action = 'one', order_type_id = int(order_type_id) if order_type_id and order_type_id.isnumeric() else None)
                if item:
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/order_types/edit.html', item = item)})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/users':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/users.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/user/add':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/users/add.html')})    

        if request.method == 'POST' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'code': 'S404', 'msg': 'Página no encontrada.'}), 404
        elif request.method == 'GET' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'html': render_template('/restaurant/error.html', code = '404', msg = 'Página no encontrada.')}), 404

        return render_template('/error.html', code = '404', msg = 'Página no encontrada.'), 404
    except Exception as e:
        print(e)
        if request.method == 'POST' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'code': f'S500C{sys.exc_info()[-1].tb_lineno}', 'msg': f'[S500C{sys.exc_info()[-1].tb_lineno}] An error occurred! The bug has been successfully reported and we will be working to fix it.'}), 500
        elif request.method == 'GET' and v_config_splitList[0] == 'api':
            return jsonify({'success': True, 'html': render_template('/restaurant/error.html', code = '500', msg = f'[S500C{sys.exc_info()[-1].tb_lineno}] An error occurred! The bug has been successfully reported and we will be working to fix it.')}), 500
        
        return render_template('/error.html', code = '500', msg = f'[S500C{sys.exc_info()[-1].tb_lineno}] An error occurred! The bug has been successfully reported and we will be working to fix it.'), 500

@app_restaurant.before_request
def main_setCookie():
    try:
        if 'theme' not in request.cookies:
            expiration_date = datetime.now() + timedelta(days=36500)

            response = make_response(redirect(request.full_path))
            response.set_cookie('theme', 'white', expires=expiration_date)
            return response
    except Exception as e:
        #api_savefile(os.path.join(app.root_path, 'log', 'web.txt'), f'[C{sys.exc_info()[-1].tb_lineno}] {e}')
        pass
    
@app_restaurant.route('/api/web/token/csrf', methods = ['GET'])
@csrf.exempt
def api_webTokenCSRF():
    return jsonify({'success': True, 'token':  generate_csrf()}), 200

@app_restaurant.errorhandler(400)
def main_error_400(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S400', 'msg': 'Bad request.'}), 400
    
    return render_template('/error.html', code = '400', msg = 'Bad request.'), 400

@app_restaurant.errorhandler(401)
def main_error_401(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S401', 'msg': 'Unauthorized.'}), 401
    
    return render_template('/error.html', code = '404', msg = 'Unauthorized.'), 401

@app_restaurant.errorhandler(403)
def main_error_403(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S403', 'msg': 'Forbidden.'}), 403
    
    return render_template('/error.html', code = '404', msg = 'Forbidden.'), 403

@app_restaurant.errorhandler(404)
def main_error_404(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S404', 'msg': 'Página no encontrada.'}), 404
    
    return render_template('/error.html', code = '404', msg = 'Página no encontrada.'), 404

@app_restaurant.errorhandler(405)
def main_error_405(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S405', 'msg': 'Method not allowed.'}), 405
    
    return render_template('/error.html', code = '404', msg = 'Method not allowed.'), 405

@app_restaurant.errorhandler(500)
def main_error_500(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S500', 'msg': 'An error occurred! The error was reported correctly and we will be working to fix it.'}), 500
    
    return render_template('/error.html', code = '500', msg = f'An error occurred! The bug has been successfully reported and we will be working to fix it.'), 500

@app_restaurant.errorhandler(503)
def main_error_503(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S503', 'msg': 'Service unavailable.'}), 503
    
    return render_template('/error.html', code = '404', msg = 'Service unavailable.'), 503

@app_restaurant.errorhandler(505)
def main_error_505(e):
    if request.method == 'POST':
        return jsonify({'success': False, 'code': 'S505', 'msg': 'HTTP Version not supported.'}), 505
    
    return render_template('/error.html', code = '404', msg = 'HTTP Version not supported.'), 505

if __name__ == '__main__':
    app_restaurant.run(host = '127.0.0.2', debug = config_app['debug'], port = 5001)