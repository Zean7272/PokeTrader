import functools
import re
from flask import (
    g, redirect, url_for
)

def check_password_requirements(password):
    if len(password) > 15:
        return False

    if not re.search(r'[A-Z]', password):
        return False

    if not re.search(r'[a-z]', password):
        return False

    if not re.search(r'\d', password):
        return False

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user:
            return view(**kwargs)
        return redirect(url_for('auth.login'))
    return wrapped_view