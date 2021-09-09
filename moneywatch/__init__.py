from flask import Flask
from flask_executor import Executor
from config import config
from . import moneywatchengine, moneywatchconfig, views

executor = Executor()

def create_app(config_name="default"):
    moneywatch = Flask(__name__)
    moneywatch.config.from_object(config[config_name])
    config[config_name].init_app(moneywatch)

    from . views import relay as main_blueprint
    moneywatch.register_blueprint(main_blueprint)
    executor.init_app(app)

    return moneywatch
