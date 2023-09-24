from main import app_main
from config import config_app

if __name__ == '__main__':
    app_main.run(host = 'localhost', debug = config_app['debug'])