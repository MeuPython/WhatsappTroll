from flask import Flask
from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///projetos.db"
database.init_app(app)

from whatstroll import Routes
