from flask import Blueprint, render_template

main = Blueprint('main', __name__)

# 首页路由
@main.route('/')
def index():
    return render_template('index.html')

# 数据库管理页面路由
@main.route('/admin')
def admin():
    return render_template('admin.html')