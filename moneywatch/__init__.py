from flask import Flask
from config import config
from . import moneywatchengine, moneywatchconfig, views


def create_app(config_name="default"):
    moneywatch = Flask(__name__)
    moneywatch.config.from_object(config[config_name])
    config[config_name].init_app(moneywatch)

    from . views import relay as main_blueprint
    moneywatch.register_blueprint(main_blueprint)

    return moneywatch
