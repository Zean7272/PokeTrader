from flask import Flask, render_template, g
import os
from . import auth, admin, user, image
from consts import navItems
from . import auth


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True, template_folder='templates', static_folder='static')
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

        # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.context_processor
    def inject_nav():
        return dict(nav=navItems)


    @app.route('/')
    def home():
        return render_template('home.html')


    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(image.bp)

    return app