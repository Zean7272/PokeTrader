from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from db import user_engine, admin_engine
from security import check_password_requirements, login_required
import pyotp
from io import BytesIO
import qrcode
from base64 import b64encode
from sqlalchemy import text

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == "POST":
        email_or_name = request.form['email']
        password = request.form['ww']
        secure = request.form['secure']

        id = check_exist_user(email_or_name, email_or_name)
        role = check_role(id)
        is_2fa = is_tfa_enabled(id)

        if secure == 'no' and id:
            connection = user_engine.connect()
            error = None
            #sql = "SELECT password FROM users WHERE id = %s;"
            password_hash = connection.execute(text("SELECT password FROM users WHERE id = :id;"), dict(id=id)).fetchone()
            connection.commit()
            connection.close()
            if check_password_hash(password_hash[0], password):
                session.clear()
                session['user_id'] = id
                if role == 'user':
                    return redirect(url_for('user.user_home'))
                if role == 'admin':
                    return redirect(url_for('admin.admin_home'))

        if secure == 'yes' and id and is_2fa:
            connection = user_engine.connect()
            error = None
            #sql = "SELECT password FROM users WHERE id = %s;"

            password_hash = connection.execute(text("SELECT password FROM users WHERE id = :id;"), dict(id=id)).fetchone()
            connection.commit()
            connection.close()
            if check_password_hash(password_hash[0], password):
                return redirect(url_for('auth.verify_otp_login', id=id))

        else:
            error = 'Username, Email or Password is incorrect!'
            flash(error)
    return render_template('auth/login.html')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        pass1 = request.form['pass1']
        pass2 = request.form['pass2']
        secure = request.form['secure']
        if secure == 'no':
            if pass1 == pass2 and not check_exist_user(email, username):
                connection = user_engine.connect()
                #sql = 'INSERT INTO USERS(username, email, password, role_id, balance, is_2fa_enabled, secret_token) VALUES(%s, %s, %s, %s, %s, %s, %s);'
                connection.execute(text('INSERT INTO USERS(username, email, password, role_id, balance, is_2fa_enabled, secret_token) '
                                        'VALUES(:username, :email, :password, :role_id, :balance, :is_2fa_enabled, :secret_token);'),
                                   dict(username=username, email=email, password=generate_password_hash(pass1), role_id=1, balance=0.00, is_2fa_enabled=0, secret_token=pyotp.random_base32()))
                connection.commit()
                connection.close()
                error = 'Your account has been created!'
                flash(error)
                return redirect(url_for('auth.login'))
            elif pass1 != pass2:
                error = 'Passwords do not match!'
                flash(error)
            elif check_exist_user(email, username):
                error = 'Username or Email is already taken, please enter something different!'
                flash(error)
        if secure == 'yes':
            if pass1 == pass2 and check_password_requirements(pass1) and not check_exist_user(email, username):
                connection = user_engine.connect()
                connection.execute(
                    text('INSERT INTO USERS(username, email, password, role_id, balance, is_2fa_enabled, secret_token) '
                         'VALUES(:username, :email, :password, :role_id, :balance, :is_2fa_enabled, :secret_token);'),
                    dict(username=username, email=email, password=generate_password_hash(pass1), role_id=1,
                         balance=0.00, is_2fa_enabled=0, secret_token=pyotp.random_base32()))
                connection.commit()

                #sql2 = 'SELECT LAST_INSERT_ID() FROM users;'

                last_id = connection.execute(text('SELECT LAST_INSERT_ID() FROM users;')).fetchone()
                connection.commit()
                connection.close()
                error = 'Follow the instructions to setup 2fa!'
                flash(error)
                return redirect(url_for('auth.setup_2fa', id=last_id))
            elif not check_password_requirements(pass1):
                error = 'Password does not meet the requirements!'
                flash(error)
            elif pass1 != pass2:
                error = 'Passwords do not match!'
                flash(error)
            elif check_exist_user(email, username):
                error = 'Username or Email is already taken, please enter something different!'
                flash(error)
    return render_template('auth/register.html')


@bp.route('/setup-2fa/<id>', methods=('GET', 'POST'))
def setup_2fa(id):
    user = get_user_data(id)
    secret_token = user[6]
    uri = get_authentication_setup_uri(user[6], user[1])
    qr_image = get_b64encoded_qr_image(uri)
    if request.method == "POST":
        return redirect(url_for('auth.verify_otp', secret_token=secret_token, username=user[1]))
    return render_template('auth/setup_2fa.html', qr_image=qr_image)


@bp.route('/verify-opt/<secret_token>/<username>', methods=('GET', 'POST'))
def verify_otp(secret_token, username):
    if request.method == "POST":
        otp = request.form['otp']
        if is_otp_valid(otp, secret_token, username):
            connection = user_engine.connect()
            #sql = 'UPDATE users SET is_2fa_enabled = 1 WHERE username = %s;'
            connection.execute(text('UPDATE users SET is_2fa_enabled = 1 WHERE username = :username;'), dict(username=username))
            connection.commit()
            connection.close()
            error = 'You have successfully verified your OTP! You can now login'
            flash(error)
            return redirect(url_for('auth.login'))
        else:
            error = 'Something went wrong! Please try again'
            flash(error)
            return redirect(url_for('auth.register'))
    return render_template('auth/otp_verify.html')


@bp.route('/verify-opt-login/<id>/', methods=('GET', 'POST'))
def verify_otp_login(id):
    if request.method == "POST":
        otp = request.form['otp']
        user = get_user_data(id)
        secret_token = user[6]
        username = user[1]
        role = check_role(id)
        if is_otp_valid(otp, secret_token, username):
            session.clear()
            session['user_id'] = id
            if role == 'user':
                return redirect(url_for('user.user_home'))
            if role == 'admin':
                return redirect(url_for('admin.admin_home'))
        else:
            error = 'OTP is invalid or expired! Please try again'
            flash(error)
            return redirect(url_for('auth.login'))
    return render_template('auth/otp_verify.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        # [0=id, 1=username, 2=email, 3=role, 4=balance, 5=is_2fa_enabled, 6=secret_token]
        g.user = get_user_data(user_id)


@bp.route('/logout')
@login_required
def logout():
    try:
        session.clear()
    except:
        pass
    return redirect(url_for('home'))


def check_exist_user(email, username):
    connection = user_engine.connect()
    #sql = 'SELECT id FROM USERS WHERE email = %s OR username = %s;'
    id = connection.execute(text('SELECT id FROM USERS WHERE email = :email OR username = :username;'), dict(email=email, username=username)).fetchone()
    connection.commit()
    connection.close()
    if id:
        return id[0]
    else:
        return None

def check_role(id):
    connection = user_engine.connect()
    #sql = 'SELECT roles.role FROM users INNER JOIN roles ON users.role_id = roles.id WHERE users.id = %s'

    role = connection.execute(text('SELECT roles.role FROM users INNER JOIN roles ON users.role_id = roles.id WHERE users.id = :id'),
                              dict(id=id)).fetchone()
    connection.commit()
    connection.close()
    if role:
        return role[0]
    else:
        return None

def get_user_data(id):
    connection = user_engine.connect()
    #sql = 'SELECT users.id, users.username, users.email, roles.role, users.balance, users.is_2fa_enabled, users.secret_token FROM users INNER JOIN roles ON users.role_id = roles.id WHERE users.id = %s;'
    result = connection.execute(text('SELECT users.id, users.username, users.email, roles.role, users.balance, users.is_2fa_enabled, users.secret_token FROM users INNER JOIN roles ON users.role_id = roles.id WHERE users.id = :id;'), dict(id=id)).fetchone()
    connection.commit()
    connection.close()
    return result

def get_authentication_setup_uri(secret_token, username):
    return pyotp.totp.TOTP(secret_token).provisioning_uri(
        name=username, issuer_name='PokeTrader')

def get_b64encoded_qr_image(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered)
    return b64encode(buffered.getvalue()).decode("utf-8")

def is_otp_valid(otp, secret_token, username):
    totp = pyotp.parse_uri(get_authentication_setup_uri(secret_token, username))
    return totp.verify(otp)

def is_tfa_enabled(id):
    connection = user_engine.connect()
    #sql = 'SELECT is_2fa_enabled FROM users WHERE id = %s'

    bool = connection.execute(text('SELECT is_2fa_enabled FROM users WHERE id = :id;'), dict(id=id)).fetchone()
    connection.commit()
    connection.close()
    print(bool)
    if bool == 1:
        return True
    else:
        return False