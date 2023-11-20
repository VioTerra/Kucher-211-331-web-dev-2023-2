from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from mysql_db import MySQL
import mysql.connector

PERMITED_PARAMS = ['login', 'password', 'last_name',
                   'first_name', 'middle_name', 'role_id']

EDIT_PARAMS = ['last_name', 'first_name', 'middle_name', 'role_id']

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

db = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице нужно авторизироваться.'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_id, user_login):
        self.id = user_id
        self.login = user_login

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        remember = request.form.get('remember_me') == 'on'

        query = 'SELECT * FROM users WHERE login = %s and password_hash = SHA2(%s, 256);'

        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (login, password))
            print(cursor.statement)
            user = cursor.fetchone()

        if user:
            login_user(User(user.id, user.login), remember=remember)
            flash('Вы успешно прошли аутентификацию!', 'success')
            param_url = request.args.get('next')
            return redirect(param_url or url_for('index'))
        flash('Введён неправильный логин или пароль.', 'danger')
    return render_template('login.html')

@app.route('/users')
def users():
    query = 'SELECT users.*, roles.name AS role_name FROM users LEFT JOIN roles ON roles.id = users.role_id'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        print(cursor.statement)
        users_list = cursor.fetchall()
    return render_template('users.html', users_list=users_list)

@app.route('/users/new')
@login_required  
def users_new():
    roles_list = load_roles()
    return render_template('users_new.html', roles_list=roles_list, user={})

def load_roles():
    query = 'SELECT * FROM roles'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        print(cursor.statement)
        roles = cursor.fetchall()
        return roles

def extract_params(params_list):
    params_dict = {}
    for param in params_list:
        params_dict[param] = request.form[param] or None
    return params_dict

def check_login_len(login):
    if len(login) < 5:
        message = 'Логин должен иметь длину не менее 5 символов'
    else:
        message = None
    return message

def check_login_latin(login):
    message = None
    latin_symb = 'abcdefghijklmnopqrstuvwxyz'
    login_without_numbers = ''
    for symb in login:
        if (symb.isdigit() == False) and (symb != ' '):
            login_without_numbers = login_without_numbers + symb.lower()
    for symb in login_without_numbers:
        if not (symb in latin_symb):
            message = 'Логин должен состоять только из латинских букв и цифр'
            break
        else:
            message = None
    return message

def all_check_login(login):
    input_class, div_class = '', ''
    bootstrap_class_green = {
        'input_class': 'is-valid', 'div_class': 'valid-feedback'}
    bootstrap_class_red = {'input_class': 'is-invalid',
                           'div_class': 'invalid-feedback'}

    message = None
    while message == None:
        message = check_login_len(login)
        break
    while message == None:
        message = check_login_latin(login)
        break

    if message == None:
        message = 'Логин удовлетворяет всем требованиям'
        input_class = bootstrap_class_green['input_class']
        div_class = bootstrap_class_green['div_class']
    elif message == '':
        input_class = ''
        div_class = ''
    else:
        input_class = bootstrap_class_red['input_class']
        div_class = bootstrap_class_red['div_class']

    return input_class, div_class, message

@app.route('/users/create', methods=['POST'])
@login_required  
def create_user():
    input_class, div_class, message = None, None, None
    password_input_class, password_div_class, password_message = None, None, None
    params = extract_params(PERMITED_PARAMS)
    input_class, div_class, message = all_check_login(params['login'])
    password_input_class, password_div_class, password_message = all_check_password(params['password'])

    if message and password_message is not None:
        if message == 'Логин удовлетворяет всем требованиям' and password_message == 'Пароль удовлетворяет всем требованиям':
            query = 'INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id) VALUES (%(login)s, SHA2(%(password)s, 256), %(last_name)s, %(first_name)s, %(middle_name)s, %(role_id)s);'
            try:
                with db.connection().cursor(named_tuple=True) as cursor:
                    cursor.execute(query, params)
                    db.connection().commit()
                    flash('Обработка данных прошла успешно!', 'success')
            except mysql.connector.errors.DatabaseError:
                db.connection().rollback()  
                flash('При сохранении данных возникла ошибка!', 'danger')
                return render_template('users_new.html', user=params, roles_list=load_roles())
        else:
            return render_template('users_new.html', user=params, roles_list=load_roles(), input_class=input_class, div_class=div_class, message=message, password_input_class=password_input_class, password_div_class=password_div_class, password_message=password_message)
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/update', methods=['POST'])
@login_required  
def update_user(user_id):
    params = extract_params(EDIT_PARAMS)
    params['id'] = user_id
    query = ('UPDATE users SET last_name=%(last_name)s, first_name=%(first_name)s, '
             'middle_name=%(middle_name)s, role_id=%(role_id)s WHERE id=%(id)s;')
    try:
        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(query, params)
            db.connection().commit()
            flash('Обработка данных прошла успешно!', 'success')
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback() 
        flash('При сохранении данных возникла ошибка.', 'danger')
        return render_template('users_edit.html', user=params, roles_list=load_roles())
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/edit')
@login_required 
def edit_user(user_id):
    query = 'SELECT * FROM users WHERE users.id = %s'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (user_id,))
        print(cursor.statement)
        user = cursor.fetchone()
    return render_template('users_edit.html', user=user, roles_list=load_roles())

@app.route('/user/<int:user_id>')
def show_user(user_id):
    query = 'SELECT * FROM users WHERE users.id = %s'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (user_id,))
        print(cursor.statement)
        user = cursor.fetchone()
    return render_template('users_show.html', user=user)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required  
def delete_user(user_id):
    query = 'DELETE FROM users WHERE users.id=%s;'
    try:
        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (user_id,))
            db.connection().commit()
            print(cursor.statement)
        flash('Пользователь успешно удален.', 'success')
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()
        flash('При удалении пользователя возникла ошибка.', 'danger')
    return redirect(url_for('users'))

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    query = 'SELECT * FROM users WHERE users.id = %s;'
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user.id, user.login)
    return None

def check_password_len(password):
    if len(password) < 8 or len(password) > 128:
        message = 'Пароль должен иметь длинну не менее 8 символов и не более 128 символов'
    else:
        message = None
    return message

def check_password_upper_lower(password):
    status_upper = False
    status_lower = False
    for symb in password:
        if symb.isupper():
            status_upper = True
    for symb in password:
        if symb.islower():
            status_lower = True
    if (status_upper == True) and (status_lower == True):
        message = None
    else:
        message = 'В пароле должна присутствовать как минимум одна заглавная и одна строчная буква'
    return message

def check_password_cyrillic_latin_special_symb(password):
    cyrillic_symb = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    latin_symb = 'abcdefghijklmnopqrstuvwxyz'
    special_symb = '''~!?@#$%^&*_-+()[]{}></\|"'.,:;'''
    password_without_numbers = ''
    for symb in password:
        if (symb.isdigit() == False) and (symb != ' '):
            password_without_numbers = password_without_numbers + \
                symb.lower()  
    status_symb = True
    for symb in password_without_numbers:
        if not ((symb in cyrillic_symb) or (symb in latin_symb) or (symb in special_symb)):
            status_symb = False
    if status_symb == False:
        message = 'В пароле должны присутствовать латинские или кириллические буквы'
    else:
        message = None
    return message

def check_password_min_num_of_digit(password):
    status_digit = False
    for symb in password:
        if symb.isdigit():
            status_digit = True
    if status_digit == True:
        message = None
    else:
        message = 'В пароле должна присутствовать как минимум одна цифра'
    return message

def check_password_space(password):
    status_space = False
    for symb in password:
        if symb.isspace():
            status_space = True
        else:
            message = None
    if status_space == True:
        message = 'В пароле не должно быть пробелов'
    return message

def all_check_password(password):
    input_class, div_class = '', ''
    bootstrap_class_green = {
        'input_class': 'is-valid', 'div_class': 'valid-feedback'}
    bootstrap_class_red = {'input_class': 'is-invalid',
                           'div_class': 'invalid-feedback'}

    message = None
    while message == None:
        message = check_password_len(password)
        break
    while message == None:
        message = check_password_min_num_of_digit(password)
        break
    while message == None:
        message = check_password_cyrillic_latin_special_symb(password)
        break
    while message == None:
        message = check_password_upper_lower(password)
        break
    while message == None:
        message = check_password_space(password)
        break

    if message == None:
        message = 'Пароль удовлетворяет всем требованиям'
        input_class = bootstrap_class_green['input_class']
        div_class = bootstrap_class_green['div_class']
    elif message == '':
        input_class = ''
        div_class = ''
    else:
        input_class = bootstrap_class_red['input_class']
        div_class = bootstrap_class_red['div_class']

    return input_class, div_class, message

def password_comparison(new_password, confirm_password, message):
    bootstrap_class_green = {
        'input_class': 'is-valid', 'div_class': 'valid-feedback'}
    bootstrap_class_red = {'input_class': 'is-invalid',
                           'div_class': 'invalid-feedback'}
    confirm_message, confirm_input_class, confirm_div_class = '', '', ''

    if new_password == confirm_password and message == 'Пароль удовлетворяет всем требованиям':
        confirm_message = 'Повтор пароля записан верно'
        confirm_input_class = bootstrap_class_green['input_class']
        confirm_div_class = bootstrap_class_green['div_class']

    elif new_password != confirm_password:
        confirm_message = 'Повтор пароля записан неверно'
        confirm_input_class = bootstrap_class_red['input_class']
        confirm_div_class = bootstrap_class_red['div_class']

    return confirm_input_class, confirm_div_class, confirm_message

@app.route('/id<int:user_id>/changepassword', methods=['GET', 'POST'])
@login_required  
def change_password(user_id):
    message, input_class, div_class = '', '', ''
    confirm_message, confirm_input_class, confirm_div_class = '', '', ''

    old_password = None

    if request.method == 'POST':
        new_password = str(request.form['new_password'])
        input_class, div_class, message = all_check_password(new_password)

        confirm_password = str(request.form['confirm_password'])
        confirm_input_class, confirm_div_class, confirm_message = password_comparison(
            new_password, confirm_password, message)

        old_password = str(request.form['old_password'])

        query = 'SELECT password_hash FROM users WHERE users.id = %s and users.password_hash = SHA2(%s, 256);'
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query, (user_id, old_password))
        user = cursor.fetchone()
        cursor.close()

        if confirm_message == 'Повтор пароля записан верно':
            if user:
                query = 'UPDATE `users` SET `password_hash`= SHA2(%s, 256) WHERE users.id = %s'
                try:
                    with db.connection().cursor(named_tuple=True) as cursor:
                        cursor.execute(query, (new_password, user_id))
                        db.connection().commit()
                        flash('Пароль успешно изменен.', 'success')
                except mysql.connector.errors.DatabaseError:
                    db.connection().rollback()
                    flash('При смене пароля произошел сбой!', 'danger')
                return redirect(url_for('users'))
            else:
                flash('Текущий пароль записан неверно!', 'danger')

    return render_template('change_password.html', user_id=user_id, message=message, input_class=input_class, div_class=div_class, confirm_message=confirm_message, confirm_input_class=confirm_input_class, confirm_div_class=confirm_div_class, old_password=old_password)

@app.route('/test')
def test():
    info = 'info'

    return render_template('test.html', info=info)
