from flask import Flask, session
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
def before_request():
    app.jinja_env.cache = {}
app.config['ENV'] = 'development'
if app.config['ENV'] == 'production':
    app.config.from_object("config.ProductionConfig")
if app.config['ENV'] == 'development':
    app.config.from_object("config.DevelopmentConfig")
if app.config['ENV'] == 'testing':
    app.config.from_object("config.TestingConfig")
    
mongo = PyMongo(app)
CORS(app, support_credentials=True)
bcrypt = Bcrypt(app)
io = SocketIO(app, cors_allowed_origins="*", manage_session=False)
Bootstrap(app)
from opghelper.admin.routes import admin
from opghelper.centri.routes import centri
from opghelper.opg.routes import opg
from opghelper.users.routes import users
app.register_blueprint(admin)
app.register_blueprint(centri)
app.register_blueprint(opg)
app.register_blueprint(users)

