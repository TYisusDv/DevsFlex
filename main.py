from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file
from flask_wtf.csrf import CSRFProtect, generate_csrf
from config import *

app = Flask(__name__, static_url_path='/assets', static_folder='static')
app.secret_key = "Secret_key_DevsFlex_1#9$0&2@"
csrf = CSRFProtect()
csrf.init_app(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods = ['GET'])
def main_web(path):    
    try:
        return render_template('index.html')
    except Exception as e:
        #api_savefile(os.path.join(app.root_path, 'log', 'web.txt'), f'[C{sys.exc_info()[-1].tb_lineno}] {e}')
        return json.dumps({'success': False, 'code': f'S500C{sys.exc_info()[-1].tb_lineno}', 'msg': 'An error occurred! The error was reported correctly and we will be working to fix it.'}), 500

@app.errorhandler(400)
def main_error_400(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S400', 'msg': 'Bad request.'}), 400
    
    return 'Error 400'

@app.errorhandler(401)
def main_error_401(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S401', 'msg': 'Unauthorized.'}), 401
    
    return 'Error 401'

@app.errorhandler(403)
def main_error_403(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S403', 'msg': 'Forbidden.'}), 403
    
    return 'Error 403'

@app.errorhandler(404)
def main_error_404(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S404', 'msg': 'Page not found.'}), 404
    
    return 'Error 404'

@app.errorhandler(500)
def main_error_500(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S500', 'msg': 'An error occurred! The error was reported correctly and we will be working to fix it.'}), 500
    
    return 'Error 500'

@app.errorhandler(503)
def main_error_503(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S503', 'msg': 'Service unavailable.'}), 503
    
    return 'Error 503'

@app.errorhandler(505)
def main_error_505(e):
    if request.method == 'POST':
        return json.dumps({'success': False, 'code': 'S505', 'msg': 'HTTP Version not supported.'}), 505
    
    return 'Error 505'

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = config_app['debug'])