from flask_appbuilder.security.manager import BaseSecurityManager
from flask import redirect, url_for

class CustomLogin(BaseSecurityManager):
    def after_login(self):
        return redirect(url_for('workflows'))
