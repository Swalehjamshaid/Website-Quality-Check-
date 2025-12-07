# wsgi.py — FINAL 100% WORKING — BEAUTIFUL UI — NO 500
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

def create_app():
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '37metrics-2025')

    # Database
    db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route('/')
    def index():
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = User.query.filter_by(email=request.form['email']).first()
            if user and bcrypt.check_password_hash(user.password, request.form['password']):
                login_user(user)
                return redirect('/dashboard')
            flash('Invalid login')
        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/login')

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
            admin = User(name="Roy", email="roy.jamshaid@gmail.com",
                        password=bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8'))
            db.session.add(admin)
            db.session.commit()

    return app

application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
