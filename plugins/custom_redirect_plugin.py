from airflow.plugins_manager import AirflowPlugin
from flask import redirect, Blueprint, url_for
from airflow.www.app import csrf


# Define the blueprint for custom routes
custom_routes_blueprint = Blueprint(
    "custom_routes", __name__,
    template_folder='templates',  # Omit if not using templates
    static_folder='static'  # Omit if not using static files
)

# Define the route for /register
@csrf.exempt
@custom_routes_blueprint.route('/register/form')
# Disable CSRF protection if needed for this route
def register_redirect():
    # Replace 'correct_registration_page' with the actual URL or path
    return redirect('https://strivenn.com/strivenn.ai-beta', code=301)
    
@custom_routes_blueprint.route('/test')
def test_route():
    return "Test route is working!"
# Define the plugin class to register the blueprint
class CustomRedirectPlugin(AirflowPlugin):
    name = "custom_redirect_plugin"
    flask_blueprints = [custom_routes_blueprint]
