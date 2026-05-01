from __future__ import annotations
from contextlib import _RedirectStream, redirect_stderr, redirect_stdout
from multiprocessing import current_process
from airflow.plugins_manager import AirflowPlugin
from workflow.views import WorkFlows, workflow_builder, gpt_type, Assistants
from user_management.views import user_management
from chat.views import Chat
from flask import Blueprint, redirect, url_for
from  clientAdmin.views import ClientAdmin
bp = Blueprint(
    "Chat",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/main",
)

# Creating a flask blueprint
gptBuilderBluePrint = Blueprint(
    "Gpt Builder",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/workflows",
)

chat_bp = Blueprint(
    "Chat_BP",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/main",
)
# gptTypeBluePrint = Blueprint(
#     "Gpt Type",
#     __name__,
#     template_folder="templates",
#     static_folder="static",
#     static_url_path="/static/workflow",
# )
AssistantViewBluePrint = Blueprint(
    "Assistants GPT",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/workflows",
)
usersBluePrint = Blueprint(
    "users",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/workflows",
)

UserManagementBluePrint = Blueprint(
    "User Management",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/user_management",
)
ClientManagementBluePrint = Blueprint(
    "Client Management",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/clientAdmin",
)
# class Gpt_type(AirflowPlugin):
#     """
#     Main class for the plugin.

#     This class defines the plugin for Apache Airflow.
#     It includes the name, flask_blueprints, and appbuilder_views attributes.
#     """

#     name = "gptTypeBluePrint"
#     flask_blueprints = [gptTypeBluePrint]
#     appbuilder_views = [{"name": "Gpt Type",
#                          "category": "", "view": gpt_type()}]
class AssistantsView(AirflowPlugin):
    """
    Main class for the plugin.

    This class defines the plugin for Apache Airflow.
    It includes the name, flask_blueprints, and appbuilder_views attributes.
    """

    name = "AssistantViewBluePrint"
    flask_blueprints = [AssistantViewBluePrint]
    appbuilder_views = [{"name": "Assistants",
                         "category": "", "view": Assistants()}]
    
class Main(AirflowPlugin):
    """
    Main class for the plugin.

    This class defines the plugin for Apache Airflow.
    It includes the name, flask_blueprints, and appbuilder_views attributes.
    """

    name = "Chat"
    flask_blueprints = [bp]
    appbuilder_views = [{"name": "Workflows",
                         "category": "", "view": WorkFlows()}]


class Gpt_builder(AirflowPlugin):
    """
    Main class for the plugin.

    This class defines the plugin for Apache Airflow.
    It includes the name, flask_blueprints, and appbuilder_views attributes.
    """

    name = "gptBuilderBluePrint"
    flask_blueprints = [gptBuilderBluePrint]
    appbuilder_views = [{"name": "Workflow Builder",
                         "category": "", "view": workflow_builder()}]


class Chat(AirflowPlugin):
    """
    Main class for the plugin.

    This class defines the plugin for Apache Airflow.
    It includes the name, flask_blueprints, and appbuilder_views attributes.
    """

    name = "ChatBluePrint"
    flask_blueprints = [chat_bp]


# class CustomMenu(AirflowPlugin):
#     name = "User Management"
#     flask_blueprints = [UserManagementBluePrint]
#     appbuilder_menu_items = [
#     {
#         "name": "List Roles",
#         "category": "User Management",
#         "href": "/roles/list/",
#     },
#     {
#         "name": "User Statistics",
#         "category": "User Management",
#         "href": "/userstatschartview/chart/",
#     },
#     {
#         "name": "User Registrations",
#         "category": "User Management",
#         "href": "/registeruser/list/",
#     },
#     {
#         "name": "Actions",
#         "category": "User Management",
#         "href": "/actions/list/",
#     },
#     {
#         "name": "Resources",
#         "category": "User Management",
#         "href": "/resources/list/",
#     },
#     {
#         "name": "Permissions",
#         "category": "User Management",
#         "href": "/permissions/list/",
#     }
#     ]
class User_management(AirflowPlugin):
    """
    Main class for the plugin.

    This class defines the plugin for Apache Airflow.
    It includes the name, flask_blueprints, and appbuilder_views attributes.
    """

    name = "UserManagementBluePrint"
    flask_blueprints = [UserManagementBluePrint]
    appbuilder_views = [{"name": "User Management",
                         "category": "", "view": user_management()}]
    appbuilder_menu_items = [
        {
            "name": "List Roles",
            "category": "User Management",
            "href": "/roles/list/",
        },
         {
            "name": "List Users",
            "category": "User Management",
            "href": "/user_management/",
        }
    ]
    
class ClientManagement(AirflowPlugin):
    """
    Main class for the plugin.

    This class defines the plugin for Apache Airflow.
    It includes the name, flask_blueprints, and appbuilder_views attributes.
    """

    name = "ClientManagementBluePrint"
    flask_blueprints = [ClientManagementBluePrint]
    appbuilder_views = [{"name": "Client Management",
                         "category": "", "view": ClientAdmin()}]

