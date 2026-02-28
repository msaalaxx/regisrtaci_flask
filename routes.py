from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, login_required, current_user, logout_user
from models import db, User
from forms import RegistrationForm, LoginForm, ProfileForm
from werkzeug.utils import secure_filename
import os

routes_app = Blueprint('routes_app', __name__)


# Регистрация
@routes_app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes_app.profile'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)

        # Первый пользователь становится админом
        if User.query.count() == 0:
            user.is_admin = True
            flash('Первый пользователь создан как администратор!', 'success')

        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите в систему.', 'success')
        return redirect(url_for('routes_app.login'))
    return render_template('register.html', form=form)


# Вход в систему
@routes_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes_app.profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Вы вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('routes_app.profile'))
        else:
            flash('Неправильный email или пароль', 'danger')
    return render_template('login.html', form=form)


# Профиль пользователя
@routes_app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Профиль обновлён!', 'success')
        return redirect(url_for('routes_app.profile'))

    # Заполняем форму текущими данными
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('profile.html', form=form, user=current_user)


# Выход из системы
@routes_app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('routes_app.login'))


# АДМИН-ПАНЕЛЬ
@routes_app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)  # Доступ запрещен

    page = request.args.get('page', 1, type=int)
    per_page = 5  # Количество пользователей на странице

    # Пагинация
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin.html', users=users)


# Назначить администратора
@routes_app.route('/admin/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash(f'Пользователь {user.username} уже является администратором.', 'warning')
    else:
        user.is_admin = True
        db.session.commit()
        flash(f'Пользователь {user.username} назначен администратором!', 'success')

    return redirect(url_for('routes_app.admin'))


# Снять права администратора
@routes_app.route('/admin/remove_admin/<int:user_id>')
@login_required
def remove_admin(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)

    # Нельзя снять права с самого себя
    if user.id == current_user.id:
        flash('Вы не можете снять права администратора с самого себя!', 'danger')
        return redirect(url_for('routes_app.admin'))

    if user.is_admin:
        user.is_admin = False
        db.session.commit()
        flash(f'У пользователя {user.username} отозваны права администратора.', 'success')
    else:
        flash(f'Пользователь {user.username} не является администратором.', 'warning')

    return redirect(url_for('routes_app.admin'))


# Удалить пользователя
@routes_app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)

    # Нельзя удалить самого себя
    if user.id == current_user.id:
        flash('Вы не можете удалить самого себя!', 'danger')
        return redirect(url_for('routes_app.admin'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {username} удален.', 'success')

    return redirect(url_for('routes_app.admin'))


# Обработчик ошибки 403
@routes_app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403