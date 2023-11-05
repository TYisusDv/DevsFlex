from config import *
from models import *

app_restaurant = Flask(__name__, static_url_path='/assets', static_folder='static')
app_restaurant.config['CACHE_TYPE'] = 'redis'
app_restaurant.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app_restaurant.config['CACHE_DEFAULT_TIMEOUT'] = 300
app_restaurant.secret_key = 'Secret_key_DevsFlex_1#9$0&2@'
serializer = URLSafeSerializer(app_restaurant.secret_key)

csrf = CSRFProtect()
csrf.init_app(app_restaurant)
CORS(app_restaurant)
socketio = SocketIO(app_restaurant)
#cache = Cache(app_restaurant)

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

def restaurant_get_cart():
    try:
        with open('cart.json', 'r') as cart_file:
            return json.load(cart_file)
    except FileNotFoundError:
        return []

def restaurant_save_cart(cart):
    with open('cart.json', 'w') as cart_file:
        json.dump(cart, cart_file)

def restaurant_get_order_details(data):
    table_id = data.get('table_id')
    order_details = model_restaurant_order_details.get(action = 'all_table', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
    for item in order_details:
        item['regdate'] = config_convertDate(item['regdate'])
    
    return order_details

def restaurant_get_order_details_status(status):
    order_details = model_restaurant_order_details.get(action = 'all_status', status = status)
    for item in order_details:
        item['regdate'] = config_convertDate(item['regdate'])
    
    return order_details


@socketio.on('get_cart')
def get_cart():
    cart = restaurant_get_cart() 
    emit('update_cart', cart)

@socketio.on('get_order_details')
def get_order_details(data):
    order_details = restaurant_get_order_details(data)
    emit('update_order_details', order_details)

@socketio.on('get_order_details_pending')
def get_order_details_pending():
    orders = restaurant_get_order_details_status(0) 
    emit('update_order_details_pending', orders)

@socketio.on('get_order_details_inprogress')
def get_order_details_inprogress():
    orders = restaurant_get_order_details_status(1) 
    emit('update_order_details_inprogress', orders)

@app_restaurant.route('/app/table/ticket', methods=['GET'])
def app_table_ticket():
    v_requestArgs = request.args
    v_id = v_requestArgs.get('id')
    order = model_restaurant_orders.get(action = 'one', order_id = v_id)
    if order:
        order_id = order['_id']
        order_regdate = config_convertDate(order['regdate'])

        order_details = model_restaurant_order_details.get(action = 'all_order', order_id = order_id)
        
        num_lines = len(order_details)
        page_height = 110 + (num_lines * 7)

        options = {
            'encoding': 'UTF-8',
            'page-width': '57.5mm',
            'page-height': f'{page_height}mm',
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
            'enable-local-file-access': ''
        }

        pdf_bytes = pdfkit.from_string(render_template('/restaurant/app/table/ticket.html', config_app = config_app, order = order, order_id = order_id, order_regdate = order_regdate, order_details = order_details), False, options = options)

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Ticket-{order_id}.pdf'

        #return render_template('/restaurant/app/table/ticket.html', config_app = config_app, order = order, order_id = order_id, order_regdate = order_regdate, order_details = order_details)
        return response
    
    return render_template('/error.html', code = '404', msg = 'Página no encontrada.'), 404

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
            #DASHBOARD
            if request.method == 'GET' and path == 'api/web/widget/dashboard':
                return jsonify({'success': True, 'html': render_template('/restaurant/home/dashboard.html')})
            
            #TABLE
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

                if v_action == 'manage_order_types':
                    data = model_restaurant_order_types.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/order/type/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['status'] = '<span class="badge bg-primary-opacity"><i class="fa fa-circle"></i> Visible</span>' if item.get('status') else '<span class="badge bg-danger-opacity"><i class="fa fa-circle"></i> Oculto</span>'
                        
                    data_count = model_restaurant_order_types.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                elif v_action == 'manage_product_categories':
                    data = model_restaurant_product_categories.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/product/category/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['status'] = '<span class="badge bg-primary-opacity"><i class="fa fa-circle"></i> Visible</span>' if item.get('status') else '<span class="badge bg-danger-opacity"><i class="fa fa-circle"></i> Oculto</span>'
                        
                    data_count = model_restaurant_product_categories.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                elif v_action == 'manage_users':
                    data = model_main_users.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/user/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['email'] = f'<span class="badge bg-primary">{item["email"]}</span>'
                        item['status'] = '<span class="badge bg-primary-opacity"><i class="fa fa-circle"></i> Activo/a</span>' if item.get('status') else '<span class="badge bg-danger-opacity"><i class="fa fa-circle"></i> Baneado/a</span>'
                        item['regdate'] = f'<span class="badge bg-primary">{config_convertDate(item["regdate"])}</span>'
                        
                    data_count = model_main_users.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                elif v_action == 'manage_customers':
                    data = model_restaurant_customers.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/customer/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['email'] = f'<span class="badge bg-primary">{item["email"]}</span>'
                        item['regdate'] = f'<span class="badge bg-primary">{config_convertDate(item["regdate"])}</span>'
                        
                    data_count = model_restaurant_customers.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                elif v_action == 'manage_tables':
                    data = model_restaurant_tables.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/table/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['table_status']['name'] = f'<span class="badge bg-primary">{item["table_status"]["name"]}</span>'

                    data_count = model_restaurant_tables.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                elif v_action == 'manage_products':
                    data = model_restaurant_products.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        item['actions'] = f'<div class="table-actions"><a href="/manage/product/edit?id={item["_id"]}" class="btn-sm bg-outline-primary"><i class="fa-solid fa-pen-to-square"></i></a></div>'
                        item['product_category']['name'] = f'<span class="badge bg-primary">{item["product_category"]["name"]}</span>'
                        item['price'] = f'<span class="badge bg-primary">${item["price"]}</span>'
                        item['status'] = '<span class="badge bg-primary-opacity"><i class="fa fa-circle"></i> Visible</span>' if item.get('status') else '<span class="badge bg-danger-opacity"><i class="fa fa-circle"></i> Oculto</span>'

                    data_count = model_restaurant_products.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)              
                elif v_action == 'manage_orders':
                    data = model_restaurant_orders.get(action = 'all_table', start = int(start), length = int(length), search = search, order_column = order_column, order_direction = order_direction)
                    for item in data:
                        user = model_main_users.get(action = 'one', user_id = item['user'])

                        item['actions'] = f'<div class="table-actions"><a href="/app/table/ticket?id={item["_id"]}" type="_blank" class="btn-sm bg-outline-primary"><i class="fa-solid fa-receipt"></i></a></div>'
                        item['no'] = f'<span class="badge bg-primary">{item["no"]}</span>'
                        item['total'] = f'<span class="badge bg-primary">${item["total"]}</span>'
                        item['user'] = f'{user["person"]["name"]} {user["person"]["surname"]}'
                        item['regdate'] = f'<span class="badge bg-primary">{config_convertDate(item["regdate"])}</span>'
                        
                    data_count = model_restaurant_orders.get(action = 'all_table_count', search = search, order_column = order_column, order_direction = order_direction)
                
                return jsonify({'success': True, 'data': data, 'recordsTotal': data_count, 'recordsFiltered': data_count})
            
            #APP ORDERS
            elif request.method == 'GET' and path == 'api/web/widget/app/orders':
                html_id = str(uuid.uuid4())
                tables = model_restaurant_tables.get(action = 'all')
                return jsonify({'success': True, 'html': render_template('/restaurant/app/orders.html', tables = tables, html_id = html_id)})    
            elif request.method == 'POST' and path == 'api/web/data/app/orders':
                if v_action == 'one_ready':
                    order_detail_id = v_requestForm.get('order_detail_id')
                    order_detail = model_restaurant_order_details.get(action = 'one', order_detail_id = int(order_detail_id) if order_detail_id and str(order_detail_id).isnumeric() else None)
                    if not order_detail:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una orden válida e inténtelo de nuevo.'})

                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id)
                    order_detail_id = int(order_detail_id)

                    update = model_restaurant_order_details.update(action = 'one_status', order_detail_id = order_detail_id, table_id = table_id, status_search = 0, status_update = 1)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al actualizar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    orders = restaurant_get_order_details_status(1) 
                    socketio.emit('update_order_details_inprogress', orders)
                    return jsonify({'success': True, 'msg': 'Se actualizó correctamente.'})            
                elif v_action == 'ready':
                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id)

                    update = model_restaurant_order_details.update(action = 'all_status', table_id = table_id, status_search = 0, status_update = 1)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al actualizar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    orders = restaurant_get_order_details_status(1) 
                    socketio.emit('update_order_details_inprogress', orders)
                    return jsonify({'success': True, 'msg': 'Se actualizó correctamente.'})            
                elif v_action == 'one_finish':
                    order_detail_id = v_requestForm.get('order_detail_id')
                    order_detail = model_restaurant_order_details.get(action = 'one', order_detail_id = int(order_detail_id) if order_detail_id and str(order_detail_id).isnumeric() else None)
                    if not order_detail:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una orden válida e inténtelo de nuevo.'})

                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id)
                    order_detail_id = int(order_detail_id)

                    update = model_restaurant_order_details.update(action = 'one_status', order_detail_id = order_detail_id, table_id = table_id, status_search = 1, status_update = 2)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al actualizar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    orders = restaurant_get_order_details_status(1) 
                    socketio.emit('update_order_details_inprogress', orders)
                    return jsonify({'success': True, 'msg': 'Se actualizó correctamente.'})            
                elif v_action == 'finish':
                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id)

                    update = model_restaurant_order_details.update(action = 'all_status', table_id = table_id, status_search = 1, status_update = 2)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al actualizar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    orders = restaurant_get_order_details_status(1) 
                    socketio.emit('update_order_details_inprogress', orders)
                    return jsonify({'success': True, 'msg': 'Se actualizó correctamente.'}) 
                elif v_action == 'one_delete':
                    order_detail_id = v_requestForm.get('order_detail_id')
                    order_detail = model_restaurant_order_details.get(action = 'one', order_detail_id = int(order_detail_id) if order_detail_id and str(order_detail_id).isnumeric() else None)
                    if not order_detail:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una orden válida e inténtelo de nuevo.'})
                    
                    if order_detail['status'] == 0 or order_detail['status'] == 2:
                        return jsonify({'success': False, 'msg': 'No se pudo eliminar, el motivo es que ya fue preparado o esta en proceso.'})

                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id)
                    order_detail_id = int(order_detail_id)

                    delete = model_restaurant_order_details.delete(action = 'one', order_detail_id = order_detail_id)
                    if not delete:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al eliminar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    orders = restaurant_get_order_details_status(1) 
                    socketio.emit('update_order_details_inprogress', orders)
                    order_details = restaurant_get_order_details({'table_id': table_id})
                    socketio.emit('update_order_details', order_details)
                    return jsonify({'success': True, 'msg': 'Se eliminó correctamente.'})  
                
            #APP TABLES
            elif request.method == 'GET' and path == 'api/web/widget/app/tables':
                tables = model_restaurant_tables.get(action = 'all')
                return jsonify({'success': True, 'html': render_template('/restaurant/app/tables.html', tables = tables)})    
            elif request.method == 'GET' and path == 'api/web/widget/app/table':
                param_id = v_requestArgs.get('id')
                item = model_restaurant_tables.get(action = 'one', table_id = int(param_id) if param_id and param_id.isnumeric() else None)
                if item:
                    html_id = str(uuid.uuid4())
                    product_categories = model_restaurant_product_categories.get(action = 'all_status', status = True)
                    return jsonify({'success': True, 'html': render_template('/restaurant/app/table.html', item = item, html_id = html_id, product_categories = product_categories)})    
            elif request.method == 'POST' and path == 'api/web/data/app/table':
                if v_action == 'get_products':
                    product_category_id = v_requestForm.get('product_category_id')
                    if product_category_id != 'all':
                        item = model_restaurant_product_categories.get(action = 'one', product_category_id = int(product_category_id) if product_category_id and str(product_category_id).isnumeric() else None)
                        if not item:
                            return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 
                        
                        products = model_restaurant_products.get(action = 'all_category_status', status = True, product_category_id = int(product_category_id))
                    else:
                        products = model_restaurant_products.get(action = 'all_status', status = True)

                    if not products:
                        return jsonify({'success': True, 'msg': 'Consulta correcta.', 'html': '<h4>No se encontraron productos</h4>'})
                    
                    return jsonify({'success': True, 'msg': 'Consulta correcta.', 'html': render_template('/restaurant/app/widget/table_products.html', products = products)})
                elif v_action == 'add':
                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})

                    product_id = v_requestForm.get('product_id')
                    product = model_restaurant_products.get(action = 'one', product_id = int(product_id) if product_id and str(product_id).isnumeric() else None)
                    if not product:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un producto válido e inténtelo de nuevo.'})
                    
                    quantity = v_requestForm.get('quantity')
                    if not quantity or not config_isFloat(quantity) or float(quantity) <= 0:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una cantidad válida e inténtelo de nuevo.'})
                    
                    note = v_requestForm.get('note')
                    if not quantity or note == '' or note == 'None' or note == 'null':
                        note = 'N/A'

                    table_id = int(table_id)
                    product_id = int(product_id)
                    product_name = product['name']
                    product_price = float(product['price'])
                    product_category = product['product_category']['name']
                    quantity = float(quantity)
                    cart_id = str(uuid.uuid4())

                    cart = restaurant_get_cart()

                    table_found = False
                    for table_entry in cart:
                        if table_entry['table_id'] == table_id:
                            product_found = False
                            # for product_entry in table_entry['products']:
                            #     if product_entry['product_id'] == product_id:
                            #         product_entry['quantity'] += quantity
                            #         product_entry['total'] = product_entry['quantity'] * product_entry['product_price']
                            #         product_found = True
                            #         break

                            if not product_found:
                                table_entry['products'].append({'cart_id': cart_id, 'product_id': product_id, 'product_name': product_name, 'product_price': product_price, 'quantity': quantity, 'total': quantity * product_price, 'product_category': product_category, 'note': note})

                            table_found = True
                            break

                    if not table_found:
                        cart.append({'table_id': table_id, 'products': [{'cart_id': cart_id, 'product_id': product_id, 'product_name': product_name, 'product_price': product_price, 'quantity': quantity, 'total': quantity * product_price, 'product_category': product_category, 'note': note}]})


                    response = make_response(jsonify({'success': True, 'msg': 'Se agregó correctamente.'}))
                    restaurant_save_cart(cart)
                    socketio.emit('update_cart', cart)
                 
                    return response
                elif v_action == 'edit':
                    cart_id = v_requestForm.get('cart_id')
                    if not cart_id:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    quantity = v_requestForm.get('quantity')
                    if not quantity or not config_isFloat(quantity) or float(quantity) < 0:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una cantidad válida e inténtelo de nuevo.'})

                    note = v_requestForm.get('note')
                    if not quantity or note == '' or note == 'None' or note == 'null':
                        note = 'N/A'
                    
                    quantity = float(quantity)

                    cart = restaurant_get_cart()
                    
                    for table_entry in cart:
                        for product_entry in table_entry['products']:
                            if product_entry['cart_id'] == cart_id:
                                if quantity == 0:
                                    table_entry['products'].remove(product_entry)
                                else:
                                    product_entry['quantity'] = quantity
                                    product_entry['note'] = note
                                    product_entry['total'] = product_entry['quantity'] * product_entry['product_price']

                    response = make_response(jsonify({'success': True, 'msg': 'Se editó correctamente.'}))
                    restaurant_save_cart(cart)

                    socketio.emit('update_cart', cart)
                    return response
                elif v_action == 'send':
                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id)

                    cart = restaurant_get_cart()
                    if not cart:
                        return jsonify({'success': False, 'msg': 'Por favor, agregue al menos un producto válido e inténtelo de nuevo.'})
                    
                    for table_entry in cart:
                        if table_entry['table_id'] == table_id:
                            if not table_entry['products']:
                                return jsonify({'success': False, 'msg': 'Por favor, agregue al menos un producto válido e inténtelo de nuevo.'})
                    
                            for product_entry in table_entry['products']:
                                model_restaurant_order_details.insert(action = 'one', price = product_entry['product_price'], quantity = product_entry['quantity'], note = product_entry['note'], total = product_entry['total'], product_id = product_entry['product_id'], table_id = table_id, user_id = v_user_id, status = 0)

                            cart.remove(table_entry)

                    response = make_response(jsonify({'success': True, 'msg': 'Se envió correctamente.'}))
                    restaurant_save_cart(cart)

                    socketio.emit('update_cart', cart)
                    order_details = restaurant_get_order_details({'table_id': table_id})
                    socketio.emit('update_order_details', order_details)
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    return response
                elif v_action == 'delete':
                    order_detail_id = v_requestForm.get('order_detail_id')
                    order_detail = model_restaurant_order_details.get(action = 'one', order_detail_id = int(order_detail_id) if order_detail_id and str(order_detail_id).isnumeric() else None)
                    if not order_detail:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una orden válida e inténtelo de nuevo.'})

                    if order_detail['status'] == 1 or order_detail['status'] == 2:
                        return jsonify({'success': False, 'msg': 'No se pudo eliminar, el motivo es que ya fue preparado o esta en proceso.'})
                    
                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id) 
                    order_detail_id = int(order_detail_id) 

                    delete = model_restaurant_order_details.delete(action = 'one', order_detail_id = order_detail_id)
                    if not delete:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al eliminar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    order_details = restaurant_get_order_details({'table_id': table_id})
                    socketio.emit('update_order_details', order_details)
                    orders = restaurant_get_order_details_status(0) 
                    socketio.emit('update_order_details_pending', orders)
                    return jsonify({'success': True, 'msg': 'Se eliminó correctamente.'})   
                elif v_action == 'finish':
                    table_id = v_requestForm.get('table_id')
                    table = model_restaurant_tables.get(action = 'one', table_id = int(table_id) if table_id and str(table_id).isnumeric() else None)
                    if not table:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una mesa válida e inténtelo de nuevo.'})
                    
                    table_id = int(table_id) 

                    total = 0
                    order_details = restaurant_get_order_details({'table_id': table_id})
                    for item in order_details:
                        print(item['status'])
                        if item['status'] == 0 or item['status'] == 1:
                            return jsonify({'success': False, 'msg': 'No se pudo finalizar, el motivo es que aun hay pedidos pendientes o en proceso.'})

                        total += item['total']                    

                    if not order_details:
                        return jsonify({'success': False, 'msg': 'Por favor, agregue al menos un producto válido e inténtelo de nuevo.'})
                    
                    order_id = str(uuid.uuid4())
                    update = model_restaurant_order_details.update(action = 'all_order', order_id = order_id, table_id = table_id, total = total, user_id = v_user_id)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al finalizar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    order_details = restaurant_get_order_details({'table_id': table_id})
                    socketio.emit('update_order_details', order_details)
                    return jsonify({'success': True, 'msg': 'Se finalizó correctamente.', 'ticket': order_id})     
           
            #ORDER TYPES
            elif request.method == 'GET' and path == 'api/web/widget/manage/order/types':
                visible = model_restaurant_order_types.get(action = 'count_status', status = True)
                hidden = model_restaurant_order_types.get(action = 'count_status', status = False)
                total = visible + hidden

                return jsonify({'success': True, 'html': render_template('/restaurant/manage/order_types.html', total = total, visible = visible, hidden = hidden)})    
            elif request.method == 'POST' and path == 'api/web/data/manage/order/types':
                if v_action == 'add':
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'}) 
                    
                    insert = model_restaurant_order_types.insert(action = 'one', name = html.escape(name))
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    param_id = v_requestForm.get('id')
                    item = model_restaurant_order_types.get(action = 'one', order_type_id = int(param_id) if param_id and param_id.isnumeric() else None)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})
                
                    status = v_requestForm.get('status')
                    if not status:
                        status = 'off'
                    
                    status = True if status == 'on' else False
                    update = model_restaurant_order_types.update(action = 'one', order_type_id = int(param_id), name = html.escape(name), status = status)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                
            #ORDER TYPE ADD/EDIT
            elif request.method == 'GET' and path == 'api/web/widget/manage/order/type/add':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/order_type/add.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/order/type/edit':
                param_id = v_requestArgs.get('id')
                item = model_restaurant_order_types.get(action = 'one', order_type_id = int(param_id) if param_id and param_id.isnumeric() else None)
                if item:
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/order_type/edit.html', item = item)})    
            
            #PRODUCT CATEGORIES
            elif request.method == 'GET' and path == 'api/web/widget/manage/product/categories':
                visible = model_restaurant_product_categories.get(action = 'count_status', status = True)
                hidden = model_restaurant_product_categories.get(action = 'count_status', status = False)
                total = visible + hidden
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/product_categories.html', total = total, visible = visible, hidden = hidden)})    
            elif request.method == 'POST' and path == 'api/web/data/manage/product/categories':
                if v_action == 'add':
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'}) 
                    
                    insert = model_restaurant_product_categories.insert(action = 'one', name = html.escape(name))
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    param_id = v_requestForm.get('id')
                    item = model_restaurant_product_categories.get(action = 'one', product_category_id = int(param_id) if param_id and param_id.isnumeric() else None)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})
                
                    status = v_requestForm.get('status')
                    if not status:
                        status = 'off'
                    
                    status = True if status == 'on' else False
                    update = model_restaurant_product_categories.update(action = 'one', product_category_id = int(param_id), name = html.escape(name), status = status)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                
            #PRODUCT CATEGORY ADD/EDIT
            elif request.method == 'GET' and path == 'api/web/widget/manage/product/category/add':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/product_category/add.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/product/category/edit':
                param_id = v_requestArgs.get('id')
                item = model_restaurant_product_categories.get(action = 'one', product_category_id = int(param_id) if param_id and param_id.isnumeric() else None)
                if item:
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/product_category/edit.html', item = item)})    
            
            #USERS
            elif request.method == 'GET' and path == 'api/web/widget/manage/users':
                actives = model_main_users.get(action = 'count_status', status = True)
                banned = model_main_users.get(action = 'count_status', status = False)
                total = actives + banned
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/users.html', total = total, actives = actives, banned = banned)})    
            elif request.method == 'POST' and path == 'api/web/data/manage/users':
                if v_action == 'add':                    
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1) or not config_verifyText(name):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un nombre válido e inténtelo de nuevo.'})

                    surname = v_requestForm.get('surname')
                    if not config_validateForm(form = surname, min = 1) or not config_verifyText(surname):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un apellido válido e inténtelo de nuevo.'})

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
                    
                    name = name.strip().capitalize()
                    surname = surname.strip().capitalize()                    

                    user_id = config_genUniqueID()
                    passw = bcrypt.hash(password)

                    insert = model_main_users.insert(action = 'one_register', user_id = user_id, name = html.escape(name), surname = html.escape(surname), email = html.escape(email), password = passw)
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    param_id = v_requestForm.get('id')
                    item = model_main_users.get(action = 'one', user_id = param_id)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1) or not config_verifyText(name):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un nombre válido e inténtelo de nuevo.'})

                    surname = v_requestForm.get('surname')
                    if not config_validateForm(form = surname, min = 1) or not config_verifyText(surname):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un apellido válido e inténtelo de nuevo.'})
    
                    email = v_requestForm.get('email')
                    if not config_validateForm(form = email, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                    
                    email = email.strip().lower()
                    if item['email'] != email:
                        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                            return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})                           
                                                
                        email_verify = model_main_users.get(action = 'email', email = email)
                        if email_verify:
                            return jsonify({'success': False, 'msg': 'El correo ya está en uso. Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                    
                    password = v_requestForm.get('password')
                    if not password:
                        passw = item['password']
                    else:
                        if not config_validateForm(form = password, min = 8):
                            return jsonify({'success': False, 'msg': 'Por favor, proporcione una contraseña válida con al menos 8 caracteres e inténtelo de nuevo.'})
                        elif not re.search(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!])(?!.*\s).{8,}$', password):
                            return jsonify({'success': False, 'msg': 'La contraseña debe contener al menos una letra mayúscula, una letra minúscula, un número, un carácter especial y tener al menos 8 caracteres. Por favor, inténtelo de nuevo.'})

                        passw = bcrypt.hash(password)

                    status = v_requestForm.get('status')
                    if not status:
                        status = 'off'
                    
                    status = True if status == 'on' else False
                    name = name.strip().capitalize()
                    surname = surname.strip().capitalize()                    

                    update = model_main_users.update(action = 'one', user_id = param_id, email = email, password = passw, status = status)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                
            #USERS ADD/EDIT
            elif request.method == 'GET' and path == 'api/web/widget/manage/user/add':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/user/add.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/user/edit':
                param_id = v_requestArgs.get('id')
                item = model_main_users.get(action = 'one', user_id = param_id)
                if item:
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/user/edit.html', item = item)})    
            
            #CUSTOMERS
            elif request.method == 'GET' and path == 'api/web/widget/manage/customers':
                total = model_restaurant_customers.get(action = 'all_count')
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/customers.html', total = total)})    
            elif request.method == 'POST' and path == 'api/web/data/manage/customers':
                if v_action == 'add':                    
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1) or not config_verifyText(name):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un nombre válido e inténtelo de nuevo.'})

                    surname = v_requestForm.get('surname')
                    if not config_validateForm(form = surname, min = 1) or not config_verifyText(surname):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un apellido válido e inténtelo de nuevo.'})

                    phone = v_requestForm.get('phone')
                    if not config_validateForm(form = phone, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un numero de telefono válido e inténtelo de nuevo.'})

                    email = v_requestForm.get('email')
                    if not config_validateForm(form = email, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})

                    email = email.strip().lower()
                    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})                           
                                            
                    email_verify = model_restaurant_customers.get(action = 'email', email = email)
                    if email_verify:
                        return jsonify({'success': False, 'msg': 'El correo ya está en uso. Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                    
                    name = name.strip().capitalize()
                    surname = surname.strip().capitalize()                    

                    person_id = config_genUniqueID()

                    insert = model_restaurant_customers.insert(action = 'one_register', person_id = person_id, name = html.escape(name), surname = html.escape(surname), email = html.escape(email), phone = phone)
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    param_id = v_requestForm.get('id')
                    item = model_restaurant_customers.get(action = 'one', customer_id = param_id)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1) or not config_verifyText(name):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un nombre válido e inténtelo de nuevo.'})

                    surname = v_requestForm.get('surname')
                    if not config_validateForm(form = surname, min = 1) or not config_verifyText(surname):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione al menos un apellido válido e inténtelo de nuevo.'})

                    phone = v_requestForm.get('phone')
                    if not config_validateForm(form = phone, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un numero telefono válido e inténtelo de nuevo.'})
    
                    email = v_requestForm.get('email')
                    if not config_validateForm(form = email, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})
                    
                    email = email.strip().lower()
                    if item['email'] != email:
                        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                            return jsonify({'success': False, 'msg': 'Por favor, proporcione un correo válido e inténtelo de nuevo.'})                           
                                                
                        email_verify = model_restaurant_customers.get(action = 'email', email = email)
                        if email_verify:
                            return jsonify({'success': False, 'msg': 'El correo ya está en uso. Por favor, proporcione un correo válido e inténtelo de nuevo.'})                 
                    
                    name = name.strip().capitalize()
                    surname = surname.strip().capitalize()                    

                    update = model_restaurant_customers.update(action = 'one', customer_id = param_id, person_id = item['person']['_id'], email = email, name = name, surname = surname, phone = phone)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                         
            #CUSTOMERS ADD/EDIT
            elif request.method == 'GET' and path == 'api/web/widget/manage/customer/add':
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/customer/add.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/customer/edit':
                param_id = v_requestArgs.get('id')
                item = model_restaurant_customers.get(action = 'one', customer_id = param_id)
                if item:
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/customer/edit.html', item = item)})    
            
            #TABLES
            elif request.method == 'GET' and path == 'api/web/widget/manage/tables':
                total = model_restaurant_tables.get(action = 'all_count')

                return jsonify({'success': True, 'html': render_template('/restaurant/manage/tables.html', total = total)})    
            elif request.method == 'POST' and path == 'api/web/data/manage/tables':
                if v_action == 'add':
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})

                    insert = model_restaurant_tables.insert(action = 'one', name = html.escape(name), table_status_id = 1)
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    param_id = v_requestForm.get('id')
                    item = model_restaurant_tables.get(action = 'one', table_id = int(param_id) if param_id and param_id.isnumeric() else None)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})
                
                    table_status_id = v_requestForm.get('table_status_id')
                    table_status = model_restaurant_table_states.get(action = 'one', table_status_id = int(table_status_id) if table_status_id and str(table_status_id).isnumeric() else None)
                    if not table_status:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el estatus válido e inténtelo de nuevo.'}) 
                    
                    update = model_restaurant_tables.update(action = 'one', table_id = int(param_id), name = html.escape(name), table_status_id = int(table_status_id))
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                
            #TABLES ADD/EDIT
            elif request.method == 'GET' and path == 'api/web/widget/manage/table/add':                
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/table/add.html')})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/table/edit':
                param_id = v_requestArgs.get('id')
                item = model_restaurant_tables.get(action = 'one', table_id = int(param_id) if param_id and param_id.isnumeric() else None)
                if item:
                    table_states = model_restaurant_table_states.get(action = 'all')
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/table/edit.html', item = item, table_states = table_states)})    
            
            #PRODUCTS
            elif request.method == 'GET' and path == 'api/web/widget/manage/products':
                visible = model_restaurant_products.get(action = 'all_count_status', status = True)
                hidden = model_restaurant_products.get(action = 'all_count_status', status = False)
                total = visible + hidden

                return jsonify({'success': True, 'html': render_template('/restaurant/manage/products.html', total = total, visible = visible, hidden = hidden)})    
            elif request.method == 'POST' and path == 'api/web/data/manage/products':
                if v_action == 'add':
                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})
                    
                    description = v_requestForm.get('description')
                    if not config_validateForm(form = description, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una descripcion válida e inténtelo de nuevo.'})
                    
                    price = v_requestForm.get('price')
                    if not config_validateForm(form = name, min = 1) or not config_isFloat(price):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un precio válido e inténtelo de nuevo.'})                        

                    product_category_id = v_requestForm.get('product_category_id')
                    product_category = model_restaurant_product_categories.get(action = 'one', product_category_id = int(product_category_id) if product_category_id and str(product_category_id).isnumeric() else None)
                    if not product_category:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una categoria válida e inténtelo de nuevo.'}) 

                    insert = model_restaurant_products.insert(action = 'one', name = html.escape(name), description = html.escape(description), price = float(price), product_category_id = int(product_category_id))
                    if not insert:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se agregó correctamente. Redireccionando...'})     
                elif v_action == 'edit':
                    param_id = v_requestForm.get('id')
                    item = model_restaurant_products.get(action = 'one', product_id = int(param_id) if param_id and param_id.isnumeric() else None)
                    if not item:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione el id válido e inténtelo de nuevo.'}) 

                    name = v_requestForm.get('name')
                    if not config_validateForm(form = name, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un nombre válido e inténtelo de nuevo.'})
                    
                    description = v_requestForm.get('description')
                    if not config_validateForm(form = description, min = 1):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una descripcion válida e inténtelo de nuevo.'})
                    
                    price = v_requestForm.get('price')
                    if not config_validateForm(form = name, min = 1) or not config_isFloat(price):
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione un precio válido e inténtelo de nuevo.'})   

                    product_category_id = v_requestForm.get('product_category_id')
                    product_category = model_restaurant_product_categories.get(action = 'one', product_category_id = int(product_category_id) if product_category_id and str(product_category_id).isnumeric() else None)
                    if not product_category:
                        return jsonify({'success': False, 'msg': 'Por favor, proporcione una categoria válida e inténtelo de nuevo.'}) 

                    status = v_requestForm.get('status')
                    if not status:
                        status = 'off'
                    
                    status = True if status == 'on' else False

                    update = model_restaurant_products.update(action = 'one', product_id = int(param_id), name = html.escape(name), description = html.escape(description), price = float(price), product_category_id = int(product_category_id), status = status)
                    if not update:
                        return jsonify({'success': False, 'msg': 'Algo salió mal al agregar. Inténtalo de nuevo. Si el problema persiste, no dude en contactarnos para obtener ayuda.'}) 
                    
                    return jsonify({'success': True, 'msg': 'Se editó correctamente. Redireccionando...'})                
            #PRODUCTS ADD/EDIT
            elif request.method == 'GET' and path == 'api/web/widget/manage/product/add':          
                product_categories = model_restaurant_product_categories.get(action = 'all')      
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/product/add.html', product_categories = product_categories)})    
            elif request.method == 'GET' and path == 'api/web/widget/manage/product/edit':
                param_id = v_requestArgs.get('id')
                item = model_restaurant_products.get(action = 'one', product_id = int(param_id) if param_id and param_id.isnumeric() else None)
                if item:
                    product_categories = model_restaurant_product_categories.get(action = 'all')
                    return jsonify({'success': True, 'html': render_template('/restaurant/manage/product/edit.html', item = item, product_categories = product_categories)})    
            
            #ORDERS
            elif request.method == 'GET' and path == 'api/web/widget/manage/orders':
                total = model_restaurant_orders.get(action = 'all_count')
                total_gen = model_restaurant_orders.get(action = 'all_sum_total')
                return jsonify({'success': True, 'html': render_template('/restaurant/manage/orders.html', total = total, total_gen = total_gen)})    
           
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

@app_restaurant.template_filter('get_user_name')
def main_get_user_name(value):
    user = model_main_users.get(action = 'one', user_id = value)
    return f'{user["person"]["name"]} {user["person"]["surname"]}'
 
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
    #app_restaurant.run(host = '127.0.0.2', debug = config_app['debug'], port = 5001)
    socketio.run(app_restaurant, host = '127.0.0.2', port = 5001, debug = config_app['debug'])