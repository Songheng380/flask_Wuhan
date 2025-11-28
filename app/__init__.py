from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

import os

# 初始化数据库
db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__, root_path=os.path.abspath('.'))
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)

    # 注册蓝图
    from app.routes.main import main as main_bp
    from app.routes.api import api as api_bp
    from app.routes.admin import admin as admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app