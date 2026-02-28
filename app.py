from flask import Flask
from flask_login import LoginManager
from models import db, User
import config
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['WTF_CSRF_SECRET_KEY'] = config.WTF_CSRF_SECRET_KEY

# Добавляем фильтр для Gravatar
@app.template_filter('md5')
def md5_filter(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'routes_app.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from routes import routes_app
app.register_blueprint(routes_app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ База данных создана!")
    print("🚀 Сервер запущен на http://localhost:5004")
    app.run(debug=True, port=config.PORT)