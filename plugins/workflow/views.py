
from flask import  jsonify, request, g,Flask, url_for,flash,redirect
from flask_appbuilder import BaseView, expose
from airflow.security import permissions
from airflow.www.auth import has_access
from openai import OpenAI, OpenAIError
from classes.title_gpt import TitleGpt
import json
import os
from workflow.params import *
from workflow.models import AirflowGptTypes, AirflowWorkflow, AirflowChat, AirflowChatDetails, GptUserAccess, Role,User, UserRole, UserWorkflowAccess
from sqlalchemy import asc, desc, func,cast, JSON, text, and_
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import requests
from PIL import Image
from io import BytesIO
from time import sleep
load_dotenv()
logger = logging.getLogger(__name__)
app = Flask(__name__)
import concurrent.futures
csrf = CSRFProtect(app)
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
import urllib.parse
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from workflow.quotes_spider import QuotesSpider
from scrapy.signalmanager import dispatcher
from scrapy import signals
import numpy as np
import re
from sqlalchemy import or_, exists
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from minify_html import minify
from urllib.parse import urljoin
from sqlalchemy.orm.exc import NoResultFound
import stat
from twisted.internet import reactor, defer, task
import logging
import threading
from threading import Event
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
# Database Session Helper Function
# def get_session():
#     return current_app.appbuilder.get_session
# print("OPENAI_API_KEY",os.getenv("OPENAI_API_KEY"))
# Utility function for date formatting
def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

# Moved repeated code patterns to utility functions
def query_workflows(session):
    return (
        session.query(AirflowWorkflow)
        .filter_by(deleted=DELETED_STATUS, record_status=RECORD_STATUS)
        .all()
    )

class WorkFlows(BaseView):

    """Creating a Flask-AppBuilder View"""

    default_view = "index"

    @expose("/")
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def index(self):
        """
        This method is the index page for the workflow views.
        It renders the "workflow.html" template with the name "Chat".
        """
        session = self.appbuilder.get_session()
        current_user_id = g.user.id if g.user else None
        try:
            # Fetch user role details
            user_role_details = session.query(Role.is_superadmin, Role.name) \
                .select_from(UserRole) \
                .join(Role, UserRole.role_id == Role.id) \
                .filter(UserRole.user_id == current_user_id) \
                .first()

            workflow_base_query = session.query(AirflowWorkflow)

            # Fetch workflows based on the user's role
            role_name = ''
            is_superadmin = 0
            if user_role_details:
                role_name = user_role_details.name
                if user_role_details.is_superadmin:
                    is_superadmin = 1
                    # If the user is a superadmin, fetch all workflows
                    workflows = workflow_base_query \
                        .filter(AirflowWorkflow.deleted == DELETED_STATUS,
                                AirflowWorkflow.record_status == RECORD_STATUS) \
                        .order_by(desc(AirflowWorkflow.id)).all()
                else:
                    # For non-superadmin users, apply filters to get relevant workflows
                    workflows = workflow_base_query \
                        .outerjoin(UserWorkflowAccess, AirflowWorkflow.id == UserWorkflowAccess.workflow_id) \
                        .filter(
                            AirflowWorkflow.deleted == DELETED_STATUS,
                            AirflowWorkflow.record_status == RECORD_STATUS,
                            or_(
                                AirflowWorkflow.created_by_id == current_user_id,
                                and_(
                                    UserWorkflowAccess.user_id == current_user_id,
                                    UserWorkflowAccess.is_enabled == ENABLED_STATUS,
                                    UserWorkflowAccess.deleted == DELETED_STATUS,
                                    UserWorkflowAccess.record_status == RECORD_STATUS,
                                )
                            )
                        ) \
                        .order_by(desc(AirflowWorkflow.id)).all()

                # Convert the results to a list of dictionaries
                workflow_info = [
                    {
                        'id': workflow.id,
                        'name': workflow.name,
                        'created_by_id': workflow.created_by_id,
                        'updated_by_id': workflow.updated_by_id,
                        'created_at': format_datetime(workflow.created_at),
                        'updated_at': format_datetime(workflow.updated_at),
                        'deleted': workflow.deleted,
                        'record_status': workflow.record_status,
                        'task': workflow.gpt_ids
                    }
                    for workflow in workflows
                ]
            else:
                workflow_info = []

            return self.render_template("/workflow.html", name="Chat", workflow_info=workflow_info, role_name=role_name, is_superadmin=is_superadmin)

        except Exception as e:
            return jsonify(success=False, message=str(e))
        finally:
            session.close()

    # Work Flow List

    @expose("/list")
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def workflow_list(self):
        """
        The function `workflow_list` retrieves a list of workflows from a database and converts them into
        a list of dictionaries, which is then passed to a template for rendering.
        :return: the rendered template "/workflow_list.html" with the variables "name" set to "List
        Workflow" and "workflow_info" set to the list of dictionaries generated from the query.
        """
        """Create default view"""
        session = self.appbuilder.get_session
        #To update or insert assistant GPT
        gpt_type.update_or_insert_assistant_gpt(self)
        workflows = (
            session.query(AirflowWorkflow)
            .filter_by(deleted=DELETED_STATUS, record_status=RECORD_STATUS)
            .all()
        )
        # Convert the results to a list of dictionaries
        workflow_info = [
            {
                'id': workflow.id,
                'name': workflow.name,
                'created_by_id': workflow.created_by_id,
                # 'updated_by_id': workflow.updated_by_id,
                'created_at': format_datetime(workflow.created_at),
                'updated_at': format_datetime(workflow.updated_at),
                'deleted': workflow.deleted,
                'record_status': workflow.record_status,
                'task': [
                    {
                        'gpt_id': gpt_info['gpt_id'],
                        'gpt_name': session.query(AirflowGptTypes).filter_by(id=gpt_info['gpt_id']).first().name,
                        'sort_order': gpt_info['sort_order']
                    }
                    for gpt_info in workflow.gpt_ids
                ] if isinstance(workflow.gpt_ids, list) else []
            }
            for workflow in workflows
        ]

        return self.render_template("/workflow_list.html", name="List Workflow", workflow_info=workflow_info)
    # Add Work Flow
    @expose('/delete_workflow/<int:workflow_id>', methods=['POST'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def delete_workflow(self, workflow_id):
        session = self.appbuilder.get_session
        try:
            workflow = (
            session.query(AirflowWorkflow)
            .filter_by(deleted=DELETED_STATUS, record_status=RECORD_STATUS, id=workflow_id)
            .first()
        )

            if not workflow:
                return jsonify({"success": False, "message": "Workflow not found."})
            
            # Soft delete the user record
            workflow.deleted = 1
            
            session.commit()
            session.close()

            return jsonify({"success": True, "message": "Workflow deleted successfully."})
        except Exception as e:
            logger.error(f"Error deleting User: {e}")
            return jsonify({"success": False, "message": "Workflow deletion  Failed."})
    
    @expose('/add_workflow', methods=['GET', 'POST'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def add_workflow(self):
        """
        The `add_workflow` function adds a new workflow to the database, validating the input and
        checking for duplicate names.
        :return: The code is returning a JSON response. If the request method is POST and all the
        necessary data is provided and valid, it will return a JSON response with the keys "success" and
        "message" set to True and a success message respectively. If there are any errors or exceptions,
        it will return a JSON response with the keys "success" and "message" set to False and an error
        message
        """
        session = self.appbuilder.get_session
        try:
            if request.method == 'POST':
                workflow_id = request.json.get("workflow_id")
                workflow_name = request.json.get("workflow_name")
                workflow_task = request.json.get("workflow_task")
                workflow_type = request.json.get("workflow_type")
                if workflow_type == "parallel":
                    root_gpt_id = request.json.get("root_gpt_id")
                elif workflow_type == "series-parallel":
                    root_gpt_id = request.json.get("root_gpt_id")
                else:
                    root_gpt_id = 0 
                # Validate that workflow_task is a non-empty JSON string
                try:
                    workflow_task_json = json.loads(workflow_task)
                    if not isinstance(workflow_task_json, list):
                        return jsonify({"success": False, "message": INVALID_TASK})
                except Exception as e:
                    return jsonify({"success": False, "message": INVALID_TASK})

                # Assuming g.user is available and contains user information
                created_by_id = g.user.id if g.user else None

                # Check for duplicate workflow name
                duplicate_workflow = (
                    session.query(AirflowWorkflow)
                    .filter(
                        (func.lower(AirflowWorkflow.name) == func.lower(workflow_name)) &
                        # (AirflowWorkflow.created_by_id == created_by_id) &
                        (AirflowWorkflow.deleted == DELETED_STATUS) &
                        (AirflowWorkflow.record_status == RECORD_STATUS)
                    )
                    .first()
                )

                if duplicate_workflow and workflow_id != duplicate_workflow.id:
                    return jsonify({"success": False, "message": WORK_FLOW_ALREADY_EXIST})
                if workflow_id:
                     # Update existing workflow
                    old_workflow = (
                        session.query(AirflowWorkflow)
                        .filter(
                            (AirflowWorkflow.id == workflow_id) &
                            (AirflowWorkflow.deleted == DELETED_STATUS) &
                            (AirflowWorkflow.record_status == RECORD_STATUS)
                        )
                        .first()
                    )
                    
                    if not old_workflow:
                        return jsonify({"success": False, "message": WORK_FLOW_NOT_FOUND})
                    
                    # Update the workflow with new data
                    old_workflow.name = workflow_name
                    old_workflow.gpt_ids = workflow_task_json
                    old_workflow.gpts = WorkFlows.get_Gpt_ids_list(workflow_task_json, session, root_gpt_id)
                    old_workflow.workflow_type = workflow_type
                    old_workflow.updated_by_id = created_by_id
                    session.commit()

                    # Mark existing records as deleted
                    session.query(AirflowChat).filter_by(workflow_id=workflow_id).update({"deleted": 1})
                    
                    
                else:
                    # Save data to the database
                    new_workflow = AirflowWorkflow(
                        name=workflow_name,
                        gpt_ids=workflow_task_json,
                        gpts = WorkFlows.get_Gpt_ids_list(workflow_task_json, session,root_gpt_id),
                        created_by_id=created_by_id,
                        workflow_type = workflow_type,
                        # Add other fields as needed
                    )
                    session.add(new_workflow)
                    session.commit()

                    new_workflow_user_access = UserWorkflowAccess(
                                    workflow_id=new_workflow.id,
                                    user_id=created_by_id,
                                    is_enabled=1,
                                    created_by_id=created_by_id
                                )
                    session.add(new_workflow_user_access)
                    session.commit()

                session.close()
                return jsonify({"success": True, "message": WORK_FLOW_CREATE_SUCCESS_MESSAGE})
        except OpenAIError as e:
            logger.info(f"error{e}")
            return jsonify(e.error)

    # List GPT
    def get_gptlist(session):
        """
        Retrieve a list of GPTs from the database.

        Args:
            session: The database session object.

        Returns:
            A list of dictionaries containing information about each GPT.
            Each dictionary contains the following keys:
            - id: The ID of the GPT.
            - name: The name of the GPT.
            - description: The description of the GPT.
            - created_by_id: The ID of the user who created the GPT.
            - updated_by_id: The ID of the user who last updated the GPT.
            - created_at: The creation timestamp of the GPT in the format 'YYYY-MM-DD HH:MM:SS'.
            - updated_at: The last update timestamp of the GPT in the format 'YYYY-MM-DD HH:MM:SS'.
            - deleted: A boolean indicating whether the GPT is deleted or not.
            - record_status: The status of the GPT record.

        """
        user_id = g.user.id if g.user else None
        # Fetch the user's role details
        try:
            user_role_details = (
                session.query(Role.is_superadmin)
                .select_from(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .filter(UserRole.user_id == user_id)
                .first()
            )
        except NoResultFound:
            user_role_details = None

        # Determine the role to be assigned
        base_query = session.query(AirflowGptTypes).filter(
            AirflowGptTypes.deleted == DELETED_STATUS,
            AirflowGptTypes.record_status == RECORD_STATUS,
        )

        if user_role_details and user_role_details.is_superadmin:
            gpts = base_query.order_by(asc(AirflowGptTypes.id)).all()
        else:
            gpts = (
                base_query.join(GptUserAccess, GptUserAccess.gpt_id == AirflowGptTypes.id)
                .filter(
                    GptUserAccess.is_enabled == ENABLED_STATUS,
                    GptUserAccess.user_id == user_id,
                    GptUserAccess.deleted == DELETED_STATUS,
                    GptUserAccess.record_status == RECORD_STATUS,
                )
                .order_by(asc(AirflowGptTypes.id))
                .all()
            )

        # Convert the results to a list of dictionaries
        gpt_info = [
            {
                'id': gpt.id,
                'name': gpt.name,
                'description': gpt.description,
                'type': gpt.type,
                'created_by_id': gpt.created_by_id,
                'updated_by_id': gpt.updated_by_id,
                'created_at': format_datetime(gpt.created_at),
                'updated_at': format_datetime(gpt.updated_at),
                'deleted': gpt.deleted,
                'record_status': gpt.record_status
            }
            for gpt in gpts
        ]

        return gpt_info

    def get_Gpt_ids_list(Gpt_ids_json, session,root_gpt_id):
        """
        The function `get_Gpt_ids_list` takes a JSON object `Gpt_ids_json` and a session object
        `session`, and returns a transformed JSON object with additional details fetched from a
        database.
        
        :param Gpt_ids_json: Gpt_ids_json is a JSON object that contains a list of GPT IDs. Each GPT ID
        is represented as a dictionary with keys "id" and "name"
        :param session: The `session` parameter is an instance of a SQLAlchemy session. It is used to
        query the database and fetch additional details for each GPT ID
        :return: a list of dictionaries. Each dictionary represents a GPT ID and contains the following
        keys: "id", "name", "sort_order", "description", and "type". The "description" and "type" values
        are fetched from the database using the provided session.
        """
        # Define a mapping from the old keys to the new keys
        key_mapping = {"id": "id", "name": "name"}

        # Transform the input JSON
        # output_json = [
        #     {
        #         "id": node["data"]["id"],
        #         "name": node[key_mapping["name"]],
        #         "sort_order": i + 1,
        #         "description": None,
        #         "type": None,
        #         "parent": None,
        #         "is_next_level":"yes",
        #     }
        #     for i, node in enumerate(Gpt_ids_json)
        # ]
        output_json = []
        parent_id = None
        
        input_counts = {}
        node_data_map = {node['id']: node.get("data", {}).get("id") for node in Gpt_ids_json}
       
        # Transform the input JSON and count input connections
        for node in Gpt_ids_json:
            input_connections = node.get("inputs", {}).get("input_1", {}).get("connections")
            if input_connections:
                for connection in input_connections:
                    input_node = connection.get("node")
                    input_counts[input_node] = input_counts.get(input_node, 0) + 1
        logger.info(f"input_counts:{input_counts}")
        # Transform the input JSON
        for i, node in enumerate(Gpt_ids_json):
            is_root = 1 if input_counts.get(str(node["id"]), 0) > 1 else 0
            logger.info(f"nodeid: {node['id']}")
            logger.info(f"count: {input_counts.get(str(node['id']))}")
            is_next_level = "yes"
            if not node.get("outputs", {}).get("output_1", {}).get("connections"):
                is_next_level = "no"
            parent_id = None

            input_connections = node.get("inputs", {}).get("input_1", {}).get("connections")
            if input_connections:
                parent_id = input_connections[0]["node"]
                parent_data_id = node_data_map.get(parent_id)

            sort_order = node.get('sort_order', i + 1)
            output_json.append({
                "id": node["data"]["id"],
                # "node_id": node["id"],
                "name": node[key_mapping["name"]],
                "sort_order":sort_order,
                "description": None,
                "type": None,
                # "parent": parent_id,
                "parent":node_data_map.get(int(parent_id), None) if parent_id is not None else None,
                "is_next_level": is_next_level,
                "is_root":is_root
               
            })
            
        # Fetch additional details for each GPT ID
        for entry in output_json:
            gpt_id = entry["id"]
            gpt_details = session.query(
                AirflowGptTypes).filter_by(id=gpt_id).first()

            if gpt_details:
                entry["description"] = gpt_details.description
                entry["type"] = gpt_details.type
            # if entry["id"] == root_gpt_id:
            #     entry["is_root"] = 1
            # else:
            #     entry["is_root"] = 0
        # sorted_data = sorted(output_json, key=lambda x: x['sort_order'])
        try:
            sorted_data = sorted(output_json, key=lambda x: x.get('sort_order', float('inf')))
        except KeyError as e:
            logging.error(f"KeyError: {e}. Unable to find 'sort_order' key in an item.")
            sorted_data = output_json
        return sorted_data

    @expose("/prompt/<int:workflow_id>")
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def prompt(self, workflow_id):
        """
        This method is used to render the prompt.html template for creating a workflow.

        Returns:
            A rendered template with the name "Create Workflow".
        """
        session = self.appbuilder.get_session
        workflow = session.query(AirflowWorkflow).filter_by(
            id=workflow_id, deleted=DELETED_STATUS, record_status=RECORD_STATUS).first()
        gpt_ids_list = []

        if workflow and workflow.gpts is None:
            gpt_ids_list = WorkFlows.get_Gpt_ids_list(workflow.gpt_ids, session)
        else:
            gpt_ids_list = workflow.gpts
        for gpt in gpt_ids_list:
            if "parent" in gpt:
                gpt["parent_id"] = gpt["parent"]
            else:
                gpt["parent_id"] = None
        return self.render_template("/prompt.html", name="Prompt Search Page", workflow_info={"id": workflow.id, "name": workflow.name,"type": workflow.workflow_type , "gpt_ids": json.dumps(gpt_ids_list)})
    
    @expose("/search", methods=["POST"])
    def search(self):
        # print("hello search")
        gpt_id = request.json.get('gpt_id')
        workflow_id = request.json.get('workflow_id')
        prompt = request.json.get('prompt')
        is_first = request.json.get('is_first')
        chat_id = request.json.get('chat_id')
        thread_id = request.json.get('thread_id')
        """
        This method is used to render the prompt.html template for creating a workflow.
        
        Returns:
            A rendered template with the name "Create Workflow".
            Thread code to save data
        """

        session = self.appbuilder.get_session

        def execute_gpt_title(gpt_function):
            with ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(gpt_function, prompt)
            return future.result()

        
        result_keyword = ''
        if is_first:
            result_keyword_dict = execute_gpt_title(TitleGpt.generate_title)
            result_keyword = result_keyword_dict.get(
                'message').replace('"', '')
            
        created_by_id = g.user.id if g.user else None    
        if is_first:
            new_chat = AirflowChat(
                name=result_keyword,
                workflow_id=workflow_id,
                created_by_id=created_by_id,
                # Add other fields as needed
            )
            session.add(new_chat)
            session.commit()
            chat = new_chat

        else:
            chat = session.query(AirflowChat).filter_by(
                id=chat_id).order_by(desc(AirflowChat.created_at)).first()
            
        def execute_gpt_task(gpt_function):
            with ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(gpt_function, session, gpt_id, prompt,chat.id,thread_id)
            return future.result()
        result = ''
        if gpt_id:
            gpt_function = WorkFlows.generate_search_result
            result = execute_gpt_task(gpt_function)

        if chat:
            chat_id = chat.id
            # if "image_url" in result:
            #     image_path = WorkFlow.save_image_from_url(chat_id,result["image_url"])
            #     if image_path:
            #         result['image_path'] = image_path
            new_chat_details = AirflowChatDetails(
                prompt=prompt,
                chat_id=chat_id,
                workflow_id=workflow_id,
                gpt_type_id=gpt_id,
                response=result,
                status=True,
                created_by_id=created_by_id,
                thread_id = result["thread_id"] if result is not None and "thread_id" in result else None
                # Add other fields as needed
            )
            session.add(new_chat_details)
            session.commit()

        session.close()
        if is_first: 
            response = {"chat_id": chat_id,"chat_name":chat.name}
        else:
            response = {"chat_id": chat_id}
        if "message" in result:
            response["message"] = result["message"]
        if "image_url" in result:
            response["image_url"] = result["image_url"]
        if "image_path" in result:
            response["image_path"] = result["image_path"]
        if "thread_id" in result:
            response["thread_id"] = result["thread_id"]

        # Return the new JSON response
        return jsonify(response)
    
    # @expose('/csrf-token', methods=['GET'])
    # def get_csrf_token():
    #     token = csrf.generate_csrf()
    #     return jsonify({'csrf_token': token})
    @expose("/search_parallel", methods=["POST"])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def search_parallel(self):
        workflow_id = request.json.get('workflow_id')
        prompt = request.json.get('prompt')
        chat_id = request.json.get('chat_id')
        is_first = request.json.get('is_first')
        thread_id = request.json.get('thread_id')
        session = self.appbuilder.get_session
        
        def execute_gpt_title(gpt_function):
            with ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(gpt_function, prompt)
            return future.result()

        result_keyword = ''
        if is_first:
            result_keyword_dict = execute_gpt_title(TitleGpt.generate_title)
            result_keyword = result_keyword_dict.get(
                'message').replace('"', '')
            # result_keyword = prompt[:20]

        
        workflow = session.query(AirflowWorkflow).filter_by(
            id=workflow_id, deleted=DELETED_STATUS, record_status=RECORD_STATUS).first()
        if workflow:
            gpts = workflow.gpts

        root_gpt_id = None
        parallel_gpt_info = []

        for gpt in gpts:
            if gpt["is_root"] == 1:
                root_gpt_id = gpt["id"]
            else:
                parallel_gpt_info.append((gpt["id"], gpt["name"]))
        created_by_id = g.user.id if g.user else None
        if is_first:
            new_chat = AirflowChat(
                name=result_keyword,
                workflow_id=workflow_id,
                created_by_id=created_by_id,
                # Add other fields as needed
            )
            session.add(new_chat)
            session.commit()
            chat = new_chat

        else:
            chat = session.query(AirflowChat).filter_by(
                id=chat_id).order_by(desc(AirflowChat.created_at)).first()
        chat_id = chat.id    
        root_gpt_result = WorkFlows.generate_search_result(session,root_gpt_id, prompt,chat_id,thread_id)
        root_gpt_result = root_gpt_result['message'].replace("\n", " ")
        result = ''
        parallel_gpt_results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(WorkFlows.generate_search_result, session, gpt_id, root_gpt_result,chat_id,thread_id) for gpt_id, _ in parallel_gpt_info]
            for (gpt_id, gpt_name), future in zip(parallel_gpt_info, concurrent.futures.as_completed(futures)):
                result = future.result()
                type_name = result["type_name"]  # Use gpt_name instead of gpt_id
                message = result["message"]
                image_url = result.get("image_url")  # Get the image URL if available
                image_path = result.get("image_path")  # Get the image Path if available
                parallel_gpt_results.append({"type_name": type_name, "message": message, "image_url": image_url,"image_path":image_path})
                        

        result = parallel_gpt_results
        if chat:
            chat_id = chat.id
            # print("chat details save ",chat_id)
            new_chat_details = AirflowChatDetails(
                prompt=prompt,
                chat_id=chat_id,
                workflow_id=workflow_id,
                gpt_type_id=1,
                response=result,
                status=True,
                created_by_id=created_by_id
                # Add other fields as needed
            )
            session.add(new_chat_details)
            session.commit()

        session.close()
        if is_first: 
            response = {"chat_id": chat_id,"chat_name":result_keyword}
        else:
            response = {"chat_id": chat_id}
        if result:
            response["message"] = result
        # if "image_url" in result:
        #     response["image_url"] = result["image_url"]
        # if "image_path" in result:
        #     response["image_path"] = result["image_path"]

        # Return the new JSON response
        return jsonify(response)
   
    def build_hierarchy(gpts, parent_id):
        hierarchy = {}
        for gpt in gpts:
            if gpt["parent"] == parent_id:
                hierarchy[gpt["id"]] = {"info": gpt, "children": []}
        for gpt_id, node in hierarchy.items():
            parent_id = node["info"]["id"]
            for gpt in gpts:
                if gpt["parent"] == parent_id:
                    node["children"].append({"info": gpt, "children": []})
        return hierarchy

    def generate_level_list(node, level_list):
        level_list.append({"gpt_id": node["info"]["id"], "gpt_name": node["info"]["name"]})
        for child in node["children"]:
            WorkFlows.generate_level_list(child, level_list)
    def hierarchical_level_list(gpts, parent_id):
        hierarchy = WorkFlows.build_hierarchy(gpts, parent_id)
        level_lists = []
        for node in hierarchy.values():
            level_list = []
            WorkFlows.generate_level_list(node, level_list)
            level_lists.append(level_list)
        # print(level_lists)
        return level_lists
    @expose("/search_series_parallel", methods=["POST"])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def search_series_parallel(self):
        # print("hello testing")
        # payload = {
            
        #     "gpt_id": 2,
        #     "prompt":"Write something about ACS?",
        #     "workflow_id": 58,
        #     "is_first": True,
        #     "chat_id": None,
        #     "parent":1,
        #     "is_root":1
        # }
        # prompt=payload['prompt']
        # workflow_id=payload['workflow_id']
        # gpt_id=payload['gpt_id']
        # chat_id=payload['chat_id']
        # is_first=payload['is_first']
        # parent_id=payload['parent']
        # is_root=payload['is_root']

        # Retrieve data from request
        gpt_id = request.json.get('gpt_id')
        workflow_id = request.json.get('workflow_id')
        prompt = request.json.get('prompt')
        chat_id = request.json.get('chat_id')
        is_first = request.json.get('is_first')
        parent_id=request.json.get('parent')
        is_root=request.json.get('is_root')

        session = self.appbuilder.get_session
        # print("gpt_id",payload['gpt_id'],"workflow_id",workflow_id)
        # print(parent_id,"parent_id",)
        def execute_gpt_title(gpt_function):
            with ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(gpt_function, prompt)
            return future.result()

        result_keyword = ''
        if is_first:
            result_keyword_dict = execute_gpt_title(TitleGpt.generate_title)
            result_keyword = result_keyword_dict.get(
                'message').replace('"', '')
        # print("result_keyword",result_keyword)
            
        # Function to execute GPT task
        def execute_gpt_task(gpt_function, **kwargs):
            with ThreadPoolExecutor(max_workers=2) as executor:
                future = executor.submit(gpt_function, **kwargs)
            return future.result()

        # Retrieve workflow and its components
        workflow = session.query(AirflowWorkflow).filter_by(id=workflow_id, deleted=DELETED_STATUS, record_status=RECORD_STATUS).first()
        if workflow:
            gpts = workflow.gpts
        
        created_by_id = g.user.id if g.user else None
        if is_first:
            new_chat = AirflowChat(
                name=result_keyword,
                workflow_id=workflow_id,
                created_by_id=created_by_id,
                # Add other fields as needed
            )
            session.add(new_chat)
            session.commit()
            chat = new_chat

        else:
            chat = session.query(AirflowChat).filter_by(
                id=chat_id).order_by(desc(AirflowChat.created_at)).first()
        chat_id = chat.id 
        # print("chat_id",chat_id)
        new_result=''
        parallel_gpt_results = []
        root_objects = [obj for obj in gpts if obj['is_root'] == 1]
        non_root_objects = [obj for obj in gpts if obj['is_root'] == 0]
        if is_first is True or is_root==1:
            gpts=root_objects
        else:
            gpts=non_root_objects
        for gpt in  gpts:
            # print(gpt['name'],is_first)
            # logger.info("gptid",gpt['id'])
            if gpt['is_root']==1 or is_first is True:
                gpt_function = WorkFlows.generate_search_result
                root_gpt_result = execute_gpt_task(gpt_function, session=session, gpt_id=gpt['id'], prompt=prompt, chat_id=chat_id)
                if 'error' in root_gpt_result:
                    return jsonify(root_gpt_result)

                new_result=root_gpt_result['message'].replace("\n", " ")
                parallel_gpt_results = [{
                    "message": new_result,
                    "type_name": root_gpt_result['type_name']
                }]
                is_first=False
                # print("new_result",new_result)
                # print("root",gpt['is_root'],is_first)
            elif gpt['is_next_level']=='no':
                new_result=prompt
                if gpt['is_root']==0:
                    # print("input",new_result)
                    gpt_function = WorkFlows.generate_search_result
                    root_gpt_result = execute_gpt_task(gpt_function, session=session, gpt_id=gpt['id'], prompt=new_result, chat_id=chat_id)
                    if 'error' in root_gpt_result:
                        return jsonify(root_gpt_result)
                    new_result=root_gpt_result['message'].replace("\n", " ")
                    parallel_gpt_results.append ({
                    "message": new_result,
                    "type_name": root_gpt_result['type_name']
                })
                    # print("new_result_1",new_result)
                else:
                    # print("parentgpt")
                    parallel_gpt_info = []
                    if new_result == '':
                        root_gpt_result = WorkFlows.generate_search_result(session,gpt['id'], prompt,chat_id)
                    else:
                        root_gpt_result = WorkFlows.generate_search_result(session,gpt['id'], new_result,chat_id)
                    if 'error' in root_gpt_result:
                       return jsonify(root_gpt_result)
                    root_gpt_result = root_gpt_result['message'].replace("\n", " ")
                    # print("root_gpt_result",root_gpt_result)
                    # parent_gpts = [gpt for gpt in gpts if gpt["parent"] == gpt['id']]
                    
                    level_lists = WorkFlows.hierarchical_level_list(gpts, gpt['id'])
                    # print("level",level_lists)
                    for branch_idx, branch in enumerate(level_lists, 1):
                        # print(f"Branch {branch_idx}: {branch}")
                        parallel_gpt_info.append(branch)
                    result = ''
                    
                    input_data=root_gpt_result
                
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                    
                        all_futures = []
                        
                        for i, sublist in enumerate(parallel_gpt_info):
                            # print(sublist,i)
                            # For the first sublist, use root_gpt_result as input_data
                            futures = []
                            # For the first sublist, use root_gpt_result as input_data
                            for j, gpt_info in enumerate(sublist):
                                if j == 0:
                                    input_data = root_gpt_result
                                
                                future = executor.submit(WorkFlows.generate_search_result, session, gpt_info["gpt_id"], input_data, chat_id)
                                futures.append(future)
                            # futures = [executor.submit(WorkFlow.generate_search_result, session, gpt_info["gpt_id"], input_data, chat_id) for gpt_info in sublist]
                            all_futures.extend(futures)  # Store all futures for this sublist
                            # Wait for the current sublist tasks to complete and collect their results
                            for future in concurrent.futures.as_completed(futures):
                                try:
                                    result = future.result()  # Wait for the future to complete and get the result
                                    if 'error' in result:
                                        return jsonify(result)
                                except Exception as e:
                                    logger.error(f"Error processing future: {e}")
                                    return jsonify({"error": "Error processing future", "message": str(e)})
                            # Wait for the current sublist tasks to complete and collect their results
                            sublist_results = [future.result() for future in concurrent.futures.as_completed(futures)]
                            # Append the results of the current sublist to the parallel_gpt_results list
                            # parallel_gpt_results.append(sublist_results)
                            last_sublist_result = sublist_results[-1] if sublist_results else None
                            if last_sublist_result:
                                parallel_gpt_results.append(last_sublist_result)
                            # Update input_data with the result of the current sublist for the next iteration
                            previous_result = sublist_results
                            input_data = previous_result[0]['message']
                    # print(parallel_gpt_results)        
                    
                    
            # break

        result=parallel_gpt_results
        # # Save mixed results to database
        if chat_id:
            new_chat_details = AirflowChatDetails(
                prompt=prompt,
                chat_id=chat_id,
                workflow_id=workflow_id,
                gpt_type_id=gpt_id,
                response=result,
                status=True,
                created_by_id=created_by_id
                # Add other fields as needed
            )
            session.add(new_chat_details)
            session.commit()

        session.close()

        # Construct response
        response = {"chat_id": chat_id, "chat_name":result_keyword}
        # if is_first:
        # if gpt_id and is_root == 0:
        #     response["chat_name"] = result  # Modify as needed
        # # if parallel_gpt_results:
        # else:            
        response["message"] = parallel_gpt_results

        return jsonify(response)


    
    def save_image_from_url(chat_id,url):
        try:
            # Send a GET request to the URL
            response = requests.get(url)
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Generate a unique filename based on the current timestamp
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"dalle_{str(chat_id)}_{timestamp}.png"  # Adjust the file extension as needed
                # airflow_home = os.environ.get('AIRFLOW_HOME')
                
                airflow_home = "/home/ubuntu/strivenn.ai/public_html"
                # airflow_home = "C:/wamp64/www/gpt-workflow1"
                
                # Define the absolute path to the directory
                save_path = airflow_home+IMAGE_SAVING_PATH
                # save_path = IMAGE_SAVING_PATH
                directory_path = IMAGE_RETREIVING_PATH
                # Get the directory of the current script
                # script_directory = os.path.dirname(os.path.abspath(__file__))

                # print("Script Directory:", script_directory)
                # if os.path.exists(save_path):
                #     # Check if the current process has read permission for the directory
                #     if os.access(save_path, os.R_OK):
                #         print(f"Read permission for directory '{directory_path}' is granted.")
                #     else:
                #         print(f"Read permission for directory '{directory_path}' is not granted.")

                #     # Check if the current process has write permission for the directory
                #     if os.access(save_path, os.W_OK):
                #         print(f"Write permission for directory '{directory_path}' is granted.")
                #     else:
                #         print(f"Write permission for directory '{directory_path}' is not granted.")

                #     # Check if the current process has execute permission for the directory
                #     if os.access(save_path, os.X_OK):
                #         print(f"Execute permission for directory '{directory_path}' is granted.")
                #     else:
                #         print(f"Execute permission for directory '{directory_path}' is not granted.")
                # else:
                #     print(f"The directory '{save_path}' does not exist.")

                # Create the directory if it doesn't exist
                # print("save_path",save_path)
                if not os.path.exists(save_path):
                    os.makedirs(save_path,exist_ok=True)

                # Change the directory permissions to allow write access
                os.chmod(save_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)

                save_path = os.path.join(save_path, filename)
                # if not os.path.exists(directory_path):
                #     os.makedirs(directory_path,exist_ok=True)
                directory_path = os.path.join(directory_path, filename)
                # Open the image using PIL
                image = Image.open(BytesIO(response.content))

                # Save the image to the specified local path
                try:
                    image.save(save_path, format='PNG')
                except Exception as e:
                    print(f"Failed to save the image. Error: {e}")
                    return None

                print(f"Image saved successfully at: {save_path}")
                return directory_path
            else:
                print(f"Failed to download image. Status Code: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None
    def generate_search_result(session, gpt_id, prompt,chat_id,thread_id=None):
        """
        The function `generate_search_result` generates search results based on a given prompt using the
        OpenAI GPT models.
        
        :param session: The `session` parameter is an object that represents the current session or
        connection to the database. It is used to query the database for information related to the GPT
        model
        :param gpt_id: The `gpt_id` parameter is an identifier for the GPT (Generative Pre-trained
        Transformer) model type. It is used to determine which GPT model to use for generating the
        search result
        :param prompt: The prompt is a string that represents the input given to the GPT model. It can
        be a question, a sentence, or any text that you want the model to generate a response for
        :return: The function `generate_search_result` returns a dictionary with the keys "message" and
        "image_url" (if the GPT type is DALL-E). The "message" key contains the generated text response
        from the GPT model, and the "image_url" key contains the URL of the generated image (if
        applicable). If there is an error during the generation process, the function returns a
        """
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            # logger.info("client: %s", client)
            # print("initial prompt",prompt)
            # print("gpt_id",gpt_id)
            gpt_type = session.query(AirflowGptTypes).filter_by(
                id=gpt_id, deleted=DELETED_STATUS, record_status=RECORD_STATUS).first()
            if gpt_type:
                # logger.info("gpt type: %s", gpt_type.type)
                # logger.info("name",gpt_type.name)
                # print("gpt type",gpt_type.type)
                if gpt_type.is_web_scrape == 1 :
                    #In this case the prompt must be any website URL
                    #extract the url from the prompt
                    # Define a regular expression pattern for URLs
                    url_pattern = r'(https?://\S+|www\.\S+)'  # Case-insensitive, match start/end of word

                    # Find all URLs using re.findall
                    urls = re.findall(url_pattern, prompt)

                    if urls:
                        prompt_url = urls[0]
                        # Replace URLs with an empty string
                        clean_text = re.sub(url_pattern, '', prompt)

                        # Strip leading and trailing whitespace (if any)
                        clean_text = clean_text.strip()
                        #validate URL
                        if WorkFlows.validate_url(prompt_url):
                            #get prompt from url
                            # prompt = WorkFlows.get_quotes(prompt_url)
                            prompt = QuotesCrawlerManager.get_quotes(prompt_url)
                            if prompt and prompt[0]:
                                prompt = prompt[0]
                            else:
                                prompt = []
                            logging.info(f"prompt_result: {prompt}")
                        
                            if prompt == []:
                                prompt = WorkFlows.scrape_website(prompt_url)
                                if prompt is None:
                                    return {"error":"INVALID_URL","message": "Please enter a valid URL"}
                            if isinstance(prompt, dict):
                                if 'Title' in prompt and 'Content' in prompt:
                                    prompt = f"{clean_text}\tTitle: {prompt['Title']}\nContent: {prompt['Content']}"
                        else:
                            logger.info("Please enter a valid URL")
                            return {"error":"INVALID_URL","message": "Please enter a valid URL"}
                    else:
                            logger.info("Please enter a valid URL")
                            return {"error":"INVALID_URL","message": "Please enter a valid URL"}
                instruction = gpt_type.instruction
                
                if gpt_type.type == 'DALL-E':

                    response = client.images.generate(
                        model=MODEL_DALLE_GPT,
                        prompt=prompt,
                        size=IMAGE_SIZE,
                        quality=IMAGE_QUALITY,
                        n=NUMBER_OF_IMAGES,
                    )
                    # logger.info("gpt response: %s", response.data[0])
                    image_path = WorkFlows.save_image_from_url(chat_id,response.data[0].url)
                    return {
                        "type_name":gpt_type.name,
                        "message": response.data[0].revised_prompt,
                        "image_url": response.data[0].url,
                        "image_path":image_path
                    }
                elif gpt_type.type == 'ASSISTANT':
                    if thread_id is None:
                        chat_details = session.query(AirflowChatDetails).filter_by(
                        chat_id=chat_id,gpt_type_id=gpt_id, deleted=DELETED_STATUS, record_status=RECORD_STATUS).first()
                        if chat_details and chat_details.thread_id:
                            thread_id = chat_details.thread_id
                            # print(f"Retrieving existing thread for with thread_id {thread_id}")
                            thread = client.beta.threads.retrieve(thread_id)
                        else:
                            # If a thread doesn't exist, create one and store it
                            thread = client.beta.threads.create()
                            # store_thread(thread.id)
                            thread_id = thread.id
                            # print("thread_id",thread_id)                    

                    # Add message to thread
                    message = client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=prompt,
                    )
                    # Retrieve the Assistant
                    assistant = client.beta.assistants.retrieve(gpt_type.assistant_id)

                    # Run the assistant
                    run = client.beta.threads.runs.create(
                        thread_id=thread.id,
                        assistant_id=assistant.id,
                    )

                    # Wait for completion
                    while run.status != "completed":
                        # Be nice to the API
                        # time.sleep(0.5)
                        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

                    # Retrieve the Messages
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    message_content = messages.data[0].content[0].text.value
                    return {"type_name":gpt_type.name,"message": message_content,"thread_id":thread_id}
                else:
                    # logging.info(f"prompt_result_processing: {prompt}")
                    max_prompt_tokens = 500
                    if len(prompt.split()) > max_prompt_tokens:
                        # Trim the prompt to the first `max_prompt_tokens` words if it exceeds the limit
                        tokens = prompt.split()
                        prompt = " ".join(tokens[:max_prompt_tokens])
                    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": instruction},
                    ],
                    max_tokens=500
                    )
                    message_content = response.choices[0].message.content
                    logger.info("gpt response: %s", message_content)

                    return {"type_name":gpt_type.name,"message": message_content}

        except OpenAIError as e:
            error_message = str(e)
            # print("testerrr", error_message)
            
            if "rate limit exceeded" in error_message:
                logger.info("Rate limit exceeded. Waiting for 60 seconds before retrying...")
                return {
                    "error": "rate_limit_exceeded", 
                    "message": "The rate limit was exceeded. Please Wait for 60 seconds before retrying..."
                }
            elif "Request too large" in error_message:
                logger.info("Request too large. The input or output tokens must be reduced.")
                return {
                    "error": "request_too_large", 
                    "message": "The request was too large. Try reducing the prompt content or splitting into smaller parts."
                }
            else:
                logger.info("GPT_ERROR_MESSAGE: %s", error_message)
                return {
                    "error": "gpt_error", 
                    "message": error_message
                }
        
    def validate_url(url):
        try:
            result = urllib.parse.urlparse(url)
            if result.scheme and result.netloc:
                return True
            else:
                return False
        except ValueError:
            return False       
    # def scrape_website(url):
    #     html_content = WorkFlow.get_html_content(url)
    #     if html_content:
    #         soup = BeautifulSoup(html_content, 'html.parser')

    #         # Get the title of the webpage
    #         title = soup.title.string if soup.title else 'No title found'
    #         # print(f"\nTitle: {title}\n")

    #         # Find all the subtitles, paragraphs, and div contents
    #         subtitles = soup.find_all(['h2', 'h3'])  # Adjust tags as needed
    #         data = {}
    #         data[f"Title"] = title
    #         for i in range(len(subtitles)):
    #             subtitle = subtitles[i]
    #             data[f"Subtitle {i+1}"] = subtitle.get_text()
    #             # print(f"Subtitle: {subtitle.get_text()}")

    #             # Find all elements until the next subtitle or the end of subtitles
    #             next_node = subtitle.find_next_sibling()
    #             while next_node and next_node.name not in ['h2', 'h3']:
    #                 content = WorkFlow.extract_text(next_node)
    #                 if content:
    #                     data[f"{next_node.name.capitalize()} {i+1}"] = content
    #                 next_node = next_node.find_next_sibling()

    #                 # Check if the next subtitle is reached
    #                 if next_node and next_node.name in ['h2', 'h3']:
    #                     break

    #         return data
    #     else:
    #         # print("Failed to retrieve the webpage.")
    #         return {"Failed to retrieve the webpage."}
    def scrape_website(url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Title Extraction
            title_tag = soup.find('title')
            title = title_tag.get_text() if title_tag else ""

            # Script and Style Tag Removal
            for tag in soup.find_all(['script', 'style']):
                tag.extract()

            # Links extraction
            # link_urls = [urljoin(url, link['href']) for link in soup.find_all('a', href=True)]

            # # Images extraction
            # images = soup.find_all('img')
            # image_urls = []
            # for image in images:
            #     if 'src' in image.attrs:
            #         # if http or https is not present in the image url, join it with the base url
            #         if 'http' not in image['src']:
            #             image_urls.append(urljoin(url, image['src']))
            #         else:
            #             image_urls.append(image['src'])

            # Body Extraction (if it exists)
            body_content = soup.find('body')
            if body_content:
                # Minify the HTML within the body tag
                minimized_body = minify(str(body_content))
                return minimized_body
        except Exception as err:
            print(f"An error occurred: {err}")
            return None
    # Function to get the HTML content of a webpage
    def get_html_content(url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response.text    
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")
        return None
    #using scrapy package
    def get_quotes(url):
        # This list will hold the scraped data
        scraped_data = []
        try:
            def crawler_results(signal, sender, item, response, spider):
                scraped_data.append(item)
            dispatcher.connect(crawler_results, signal=signals.item_scraped)
            process = CrawlerProcess(get_project_settings())
            process.crawl(QuotesSpider, start_url=url)
            process.start()  # the script will block here until the crawling is finished
            if scraped_data and scraped_data[0]:
                return scraped_data[0]
            else:
                return scraped_data
        except Exception as err:
            print(f"An error occurred: {err}")
            return scraped_data
            
    # Function to extract text from HTML element
    def extract_text(element):
        if element.name == 'p':
            return element.get_text()
        elif element.name == 'div':
            return ' '.join(WorkFlows.extract_text(child) for child in element.children if child.name is not None)
        else:
            return ''
    @expose('/prompt_history/<int:workflow_id>/<int:chat_id>', methods=['POST'])
    # @has_access(
    #     [
    #         (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)
    #     ]
    # )
    def get_prompt_history(self, workflow_id, chat_id):
        """
        The function `get_prompt_history` retrieves the prompt history for a specific workflow and chat
        ID and returns it as a JSON response.
        
        :param workflow_id: The `workflow_id` parameter is used to identify a specific workflow in the
        database. It helps in filtering the chat history based on the workflow
        :param chat_id: The `chat_id` parameter is used to identify a specific chat or conversation. It
        is typically a unique identifier assigned to each chat or conversation in your application
        :return: a JSON response with the keys "success" and "history". The value of "success" is set to
        True, indicating that the operation was successful. The value of "history" is a list of
        dictionaries, where each dictionary represents a prompt history entry. Each dictionary contains
        the keys "id", "prompt", "response", and "gpt_type_id", which correspond to
        """
        session = self.appbuilder.get_session
        prompt_history = session.query(AirflowChatDetails).filter_by(
            workflow_id=workflow_id, chat_id=chat_id, deleted=DELETED_STATUS, record_status=RECORD_STATUS).order_by(asc(AirflowChatDetails.id)).all()
        history = [
            {
                'id': history.id,
                'prompt': history.prompt,
                'response': history.response,
                'gpt_type_id': history.gpt_type_id
            }
            for history in prompt_history
        ]
        return jsonify({"success": True, "history": history})

    @expose("/gpt_history_list/<int:workflow_id>", methods=["GET"])
    def gpt_history_list(self, workflow_id):
        """
        The `gpt_history_list` function retrieves chat history based on the workflow ID, paginates the
        results, and categorizes the history into today's, yesterday's, last week's, and all chat
        history.
        
        :param workflow_id: The `workflow_id` parameter is used to filter the chat history based on a
        specific workflow. It is used to retrieve chat history records that are associated with a
        particular workflow
        :return: a dictionary with the following keys:
        - "success": True or False, indicating the success of the function.
        - "History": a list of dictionaries containing the chat history for all time.
        - "Last Week": a list of dictionaries containing the chat history for the last week.
        - "Yesterday": a list of dictionaries containing the chat history for yesterday.
        - "Today": a
        """

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        session = self.appbuilder.get_session
        user_id = g.user.id if g.user else None

        chat_history_query = session.query(AirflowChat).filter_by(workflow_id=workflow_id, created_by_id=user_id,
                                                                  deleted=DELETED_STATUS, record_status=RECORD_STATUS).order_by(desc(AirflowChat.created_at))

        total_records = chat_history_query.count()
        total_pages = (total_records + page_size - 1) // page_size

        start = (page - 1) * page_size
        chat_history = chat_history_query.offset(start).limit(page_size).all()

        all_chat_history = [
            {
                "id":history.id,
                "name":history.name,
                "workflow_id":history.workflow_id,
                "created_at":history.created_at
            }
            for history in chat_history
        ]
        


        return {"success": True, "data": all_chat_history,"total_page": total_pages, "page": page}
    

class workflow_builder(BaseView):
    """Creating a Flask-AppBuilder View"""

    default_view = "index"

    @expose("/")
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def index(self):
        """
        The `index` function creates a default view by rendering a template with various variables
        passed as arguments.
        :return: a rendered template called "/workflow-builder.html" with the following variables:
        header, history_chats, new_chat, name, and gpt_list.
        """
        """Create default view"""
        new_chat = "New Chat"
        header = "Strivenn GPT"
        history_chats = "History"
        session = self.appbuilder.get_session
        #To update or insert assistant GPT
        gpt_type.update_or_insert_assistant_gpt(self)
        gpt_list = WorkFlows.get_gptlist(session)
        return self.render_template("/workflow-builder.html", header=header, history_chats=history_chats, new_chat=new_chat, name="Chat", gpt_list=gpt_list)

    @expose("/edit/<int:workflow_id>")
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def edit(self, workflow_id):
        """
        The `edit` function creates a default view for a workflow by retrieving data from the database
        and rendering it in a template.
        
        :param workflow_id: The `workflow_id` parameter is the ID of the workflow that needs to be
        edited
        :return: the rendered template "/workflow-builder.html" with the following variables: header,
        history_chats, new_chat, name, gpt_list, and workflow_data.
        """
        """Create default view"""
        new_chat = "New Chat"
        header = "Strivenn GPT"
        history_chats = "History"
        session = self.appbuilder.get_session
        gpt_list = WorkFlows.get_gptlist(session)
        workflows = (
            session.query(AirflowWorkflow)
            .filter_by(deleted=DELETED_STATUS, record_status=RECORD_STATUS, id=workflow_id)
            .all()
        )
        workflow_datas = {
            "id": workflows[0].id,
            "name": workflows[0].name,
            "workflow_json": workflows[0].gpt_ids,
            "workflow_type": workflows[0].workflow_type

        }
        workflow_data = json.dumps(workflow_datas)

        return self.render_template("/workflow-builder.html", header=header, history_chats=history_chats, new_chat=new_chat, name="Chat", gpt_list=gpt_list, workflow_data=workflow_data,is_edit=True)


class gpt_type(BaseView):
    default_view = "index"

    @expose("/")
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def index(self):
        """
        The function retrieves a list of GPT types from a database and renders a template with the
        retrieved information.
        :return: the rendered template "/gpt_type_list.html" with the variable "gpt_info" passed as a
        parameter.
        """
        session = self.appbuilder.get_session
        #To update or insert assistant GPT
        gpt_type.update_or_insert_assistant_gpt(self) 
        try:
            search_query = request.args.get('search', '').strip()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            current_user_id = g.user.id if g.user else None
            is_superadmin_query = session.query(exists().where(
                UserRole.user_id == current_user_id,
                UserRole.role_id == Role.id,
                Role.is_superadmin == 1
            )).scalar()

            if is_superadmin_query:
                # If the user is a superadmin, fetch all AirflowGptTypes
                query = session.query(AirflowGptTypes).filter(
                    AirflowGptTypes.deleted == 0,
                    AirflowGptTypes.record_status == 1
                )
            else:
                query = session.query(AirflowGptTypes).join(
                    GptUserAccess,
                    AirflowGptTypes.id == GptUserAccess.gpt_id
                ).filter(
                    AirflowGptTypes.deleted == 0,
                    AirflowGptTypes.record_status == 1,
                    GptUserAccess.user_id == current_user_id,
                    GptUserAccess.is_enabled == 1,
                    GptUserAccess.deleted == 0,
                    GptUserAccess.record_status == 1
                )

            if search_query:
                query = query.filter(
                    or_(
                        AirflowGptTypes.name.ilike(f'%{search_query}%'),
                        AirflowGptTypes.description.ilike(f'%{search_query}%'),
                        AirflowGptTypes.instruction.ilike(f'%{search_query}%'),
                        AirflowGptTypes.type.ilike(f'%{search_query}%')
                    )
                )

            total = query.count()
            query = query.order_by(desc(AirflowGptTypes.id))
            gpt_info = query.offset((page - 1) * per_page).limit(per_page).all()

             # Truncate instructions for display
            truncated_gpt_info = [
                {
                    'id': gpt.id,
                    'name': gpt.name,
                    'description': gpt.description,
                    'instruction':gpt.instruction,
                    'truncated_instruction': gpt_type.truncate_text(gpt.instruction, 100), # Adjust length as needed
                    'type': gpt.type
                } for gpt in gpt_info
            ]
            # Query to get only active users
            active_users = session.query(User).filter(User.active == True,User.deleted == DELETED_STATUS,User.record_status == RECORD_STATUS).all()
            current_user_id = g.user.id if g.user else None
            user_role_alias = aliased(UserRole)
            role_alias = aliased(Role)

            # Query to get users and their is_superadmin value
            is_superadmin = session.query(User, role_alias.is_superadmin).\
                select_from(User).\
                join(user_role_alias, User.id == user_role_alias.user_id).\
                join(role_alias, user_role_alias.role_id == role_alias.id).\
                filter(User.id == current_user_id).\
                all()
            for user, superadmin in is_superadmin:
                print(f'User: {user.first_name}, Is Superadmin: {superadmin}')

            return self.render_template(
                '/gpt_type_list.html',
                gpt_info=truncated_gpt_info,
                search=search_query,
                page=page,
                per_page=per_page,
                total=total,
                users=active_users,
                is_superadmin=superadmin
            )
        finally:
            session.close()
    def truncate_text(text, max_length):
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    def get_models_list():
        api_key = os.getenv("OPENAI_API_KEY")
        # Endpoint URL
        url = 'https://api.openai.com/v1/models'

        # Headers with API key and required beta header
        headers = {
            'Authorization': 'Bearer ' + api_key,
            'Content-Type': 'application/json',
            'OpenAI-Beta': 'assistants=v2'
        }

        # Making a GET request
        response = requests.get(url, headers=headers)
        # Checking if the request was successful (status code 200)
        if response.status_code == 200:
            # Print the response content (list of assistants)
            # print(response.json())
            models_list = response.json()
            return models_list['data']
        else:
            # Print error message if request was not successful
            print("Error:", response.text)

    @expose('/add_gpt', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_gpt(self):
        """
        The `add_gpt` function adds a new GPT (Generative Pre-trained Transformer) type to the database.
        :return: The code is returning a JSON response. If the request method is 'POST', it returns a
        JSON object with the keys "success" and "message". If the request method is not 'POST', it
        renders a template. If there is an OpenAIError, it returns the error as a JSON response.
        """
        session = self.appbuilder.get_session()
        try:
            if request.method == 'POST':
                name = request.form.get('name')
                description = request.form.get('description')
                instruction = request.form.get('instruction')
                type = request.form.get('type')
                is_web_scrape = request.form.get('is_web_scrape')
                file = request.files.get('gpt_file')
                created_by_id = g.user.id if g.user else None

                # Check for duplicate workflow name
                duplicate_type = (
                    session.query(AirflowGptTypes)
                    .filter(
                        (func.lower(AirflowGptTypes.name) == func.lower(name)) &
                        (AirflowGptTypes.deleted == 0) &
                        (AirflowGptTypes.record_status == 1)
                    )
                    .first()
                )

                if duplicate_type:
                    return jsonify({"success": False, "message": "Assistant already exists."})
                
                assistant_id = None
                file_path = None                
                # Ensure a file was uploaded if type is "ASSISTANT"
                if type == "ASSISTANT" and not file:
                    return jsonify({"success": False, "message": "Please attach file."})
                # Ensure a file was uploaded
                if file:
                    # Save the file temporarily for API use
                    attachment_file_path = "/home/ubuntu/strivenn.ai/public_html/attachment_files"
                    #attachment_file_path = "./attachment_files"
                    if not os.path.exists(attachment_file_path):
                        os.makedirs(attachment_file_path,exist_ok=True)
                    # Change the directory permissions to allow write access
                    os.chmod(attachment_file_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                    file_path = os.path.join(attachment_file_path, secure_filename(file.filename))
                    file.save(file_path)
                    # print("file_path",file_path)
                    # Create assistant using OpenAI API
                    api_key = os.getenv("OPENAI_API_KEY")
                    client = OpenAI(api_key=api_key)
                    openai_file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
                    # Print the uploaded file details to verify
                    logger.info(f"openai_file: {openai_file}")
                    assistant = client.beta.assistants.create(
                            name=name,
                            instructions=instruction,
                            tools=[{"type": "code_interpreter"}],
                            model="gpt-4o",
                            tool_resources={
                                "code_interpreter": {
                                "file_ids": [openai_file.id]
                                }
                            }
                        )
                    assistant_id = assistant.id
                
                # Save data to the database
                new_gpt_type = AirflowGptTypes(
                    name=name,
                    description=description,
                    instruction=instruction,
                    type=type,
                    created_by_id=created_by_id,
                    connection_id=1,
                    file=file_path,
                    assistant_id=assistant_id,
                    is_web_scrape = is_web_scrape
                )
                session.add(new_gpt_type)
                session.commit()
                new_gpt_user_access = GptUserAccess(
                                    gpt_id=new_gpt_type.id,
                                    user_id=created_by_id,
                                    is_enabled=1,
                                    created_by_id=created_by_id
                                )
                session.add(new_gpt_user_access)
                session.commit()


                return jsonify({"success": True, "message": "Assistant created successfully."})
            
            return self.render_template("/gpt_type_create.html", gpt="")
        except OpenAIError as e:
            logger.info(f"error: {e}")
            return jsonify({"success": False, "message": str(e)})
        finally:
            session.close()

    @expose('/edit_gpt/<int:gpt_id>', methods=['GET', 'POST'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def edit_gpt(self, gpt_id):
        """
        The `edit_gpt` function is used to edit a GPT record in the database and return a JSON response
        indicating the success or failure of the operation.
        
        :param gpt_id: The `gpt_id` parameter is the unique identifier of the GPT (Generative
        Pre-trained Transformer) record that needs to be edited. It is used to fetch the specific GPT
        record from the database
        :return: The code is returning a JSON response. If the request method is POST and the update is
        successful, it returns a JSON object with "success" set to True and "message" set to
        "GPT_TYPE_UPDATE_SUCCESS_MESSAGE". If the GPT record is not found, it returns a JSON object with
        "success" set to False and "message" set to "GPT_TYPE_NOT_FOUND".
        """
        session = self.appbuilder.get_session
        try:
            # Fetch the GPT record from the database
            gpt = session.query(AirflowGptTypes).filter_by(
                deleted=DELETED_STATUS, record_status=RECORD_STATUS, id=gpt_id).first()
            if not gpt:
                return jsonify({"success": False, "message": GPT_TYPE_NOT_FOUND})
            if request.method == 'POST':
                name = request.form.get('name')
                description = request.form.get('description')
                instruction = request.form.get('instruction')
                type = request.form.get('type')
                file = request.files.get('gpt_file')
                is_web_scrape = request.form.get('is_web_scrape')
                created_by_id = g.user.id if g.user else None
                assistant_id = gpt.assistant_id
                file_path = gpt.file
                api_key = os.getenv("OPENAI_API_KEY")
                client = OpenAI(api_key=api_key)
                        
                # Check for duplicate workflow name
                duplicate_type = (
                    session.query(AirflowGptTypes)
                    .filter(
                        (func.lower(AirflowGptTypes.name) == func.lower(name)) &
                        (AirflowGptTypes.id != gpt_id) &
                        (AirflowGptTypes.deleted == 0) &
                        (AirflowGptTypes.record_status == 1)
                    )
                    .first()
                )

                if duplicate_type:
                    return jsonify({"success": False, "message": GPT_TYPE_ALREADY_EXIST})
                
                # Ensure a file was uploaded if type is "ASSISTANT"
                if type == "ASSISTANT" and gpt.file is None and not file:
                    if assistant_id:
                        assistant_json_data = gpt_type.get_assistants_details(assistant_id)
                        if assistant_json_data:
                            # Extract the first file_id
                            file_id = assistant_json_data['tool_resources']['code_interpreter']['file_ids'][0]
                            # print("file_id",file_id)
                            try:
                                assistant = client.beta.assistants.update(
                                    assistant_id=assistant_id,
                                    name=name,
                                    instructions=instruction,
                                    tools=[{"type": "code_interpreter"}],
                                    model="gpt-4o",
                                    tool_resources={
                                        "code_interpreter": {
                                            "file_ids": [file_id]
                                        }
                                    }
                                )
                                print("Assistant updated successfully:", assistant)
                            except Exception as e:
                                print("An unexpected error occurred:", e)
                        else:    
                            return jsonify({"success": False, "message": "Please attach file."})
                    else:    
                        return jsonify({"success": False, "message": "Please attach file."})
                
                if type != "ASSISTANT":
                    assistant_id = None
                    file_path = None
                # Ensure a file was uploaded
                if file:
                    # Save the file temporarily for API use
                    attachment_file_path = "/home/ubuntu/strivenn.ai/public_html/attachment_files"
                    #attachment_file_path = "./attachment_files"
                    if not os.path.exists(attachment_file_path):
                        os.makedirs(attachment_file_path,exist_ok=True)
                     # Change the directory permissions to allow write access
                    os.chmod(attachment_file_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                    file_path = os.path.join(attachment_file_path, secure_filename(file.filename))
                    file.save(file_path)

                    # Create assistant using OpenAI API
                    openai_file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
                    if assistant_id is None:
                        assistant = client.beta.assistants.create(
                        name=name,
                        instructions=instruction,
                        tools=[{"type": "code_interpreter"}],
                        model="gpt-4o",
                        tool_resources={
                            "code_interpreter": {
                                "file_ids": [openai_file.id]
                            }
                        }
                        )
                        assistant_id = assistant.id
                    else:
                        try:
                            assistant = client.beta.assistants.update(
                                assistant_id=assistant_id,
                                name=name,
                                instructions=instruction,
                                tools=[{"type": "code_interpreter"}],
                                model="gpt-4o",
                                tool_resources={
                                    "code_interpreter": {
                                        "file_ids": [openai_file.id]
                                    }
                                }
                            )
                            print("Assistant updated successfully:", assistant)
                        except Exception as e:
                            print("An unexpected error occurred:", e)
                        
                # Update the existing GPT record
                gpt.name = name
                gpt.description = description
                gpt.instruction = instruction
                gpt.type = type
                gpt.file=file_path
                gpt.assistant_id=assistant_id
                gpt.created_by_id = created_by_id
                gpt.connection_id = 1
                gpt.is_web_scrape = is_web_scrape

                # Commit the changes to the database
                session.commit()
                session.close()
                return jsonify({"success": True, "message": GPT_TYPE_UPDATE_SUCCESS_MESSAGE})

            # Render the template with the GPT data
            return self.render_template("/gpt_type_create.html", gpt=gpt)
        except OpenAIError as e:
            logger.info(f"error{e}")
            return jsonify(e.error)

    @expose('/delete_gpt/<int:gpt_id>', methods=['POST'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def delete_gpt(self, gpt_id):
        """
        The `delete_gpt` function deletes a GPT record from the database by setting its `deleted` flag
        to 1.
        
        :param gpt_id: The `gpt_id` parameter is the unique identifier of the GPT (Generative
        Pre-trained Transformer) record that needs to be deleted
        :return: a JSON response. If the GPT record is found and successfully deleted, it returns a JSON
        object with "success" set to True and "message" set to "GPT type delete success message". If the
        GPT record is not found, it returns a JSON object with "success" set to False and "message" set
        to "GPT type not found". If
        """
        session = self.appbuilder.get_session
        try:
            # Fetch the GPT record from the database
            gpt = session.query(AirflowGptTypes).filter_by(
                deleted=DELETED_STATUS, record_status=RECORD_STATUS, id=gpt_id).first()

            if not gpt:
                return jsonify({"success": False, "message": GPT_TYPE_NOT_FOUND})
            
            # Retrieve all rows that match the conditions
            workflow_entries = (
                session.query(AirflowWorkflow)
                .filter_by(deleted=DELETED_STATUS, record_status=RECORD_STATUS)
                .all()
            )
            gpt_id = gpt.id
            workflow_names_with_gpt = []
            # Check if workflow_entries is not empty
            # if workflow_entries:
            #     # Check if gpt_id exists in any of the rows and if entry.gpts is not None
            #     gpt_id_exists = any(
            #         gpt_id in [gpt['id'] for gpt in entry.gpts] 
            #         for entry in workflow_entries 
            #         if entry.gpts is not None
            #     )
            if workflow_entries:
                for entry in workflow_entries:
                    # Check if the 'gpts' field is not None and contains the gpt_id
                    if entry.gpts is not None:
                        gpts_data = entry.gpts  # Assuming this is a JSON object or list
                        if isinstance(gpts_data, list):  # Ensure gpts is a list of dictionaries
                            for gpt_item in gpts_data:
                                if 'id' in gpt_item and gpt_item['id'] == gpt_id:
                                    workflow_names_with_gpt.append(entry.name)   
               
                if workflow_names_with_gpt:
                    return jsonify({"success": False, "message": GPT_TYPE_EXIST_IN_WORKFLOW, "workflows": workflow_names_with_gpt})
            
            # Soft delete the GPT record (update status or set a deleted flag)
            gpt.deleted = 1
            session.commit()
            session.close()
            assistant_id = gpt.assistant_id
            if gpt.type == "ASSISTANT" and assistant_id is not None:
                api_key = os.getenv("OPENAI_API_KEY")
                client = OpenAI(api_key=api_key)
                try:
                    response = client.beta.assistants.delete(
                        assistant_id=assistant_id
                    )
                    print("Assistant deleted successfully:", response)
                except Exception as e:
                    print("Invalid request error:", e)

            return jsonify({"success": True, "message": GPT_TYPE_DELETE_SUCCESS_MESSAGE})
        except Exception as e:
            logger.error(f"Error deleting Assistant: {e}")
            return jsonify({"success": False, "message": "An error occurred while deleting the Assistant"})
    
    @expose('/check_gpt_exist_workflow/<int:gpt_id>', methods=['GET'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def check_gpt_exist_workflow(self, gpt_id):
        session = self.appbuilder.get_session
        
        # Fetch the GPT record from the database
        gpt = session.query(AirflowGptTypes).filter_by(
            deleted=DELETED_STATUS, record_status=RECORD_STATUS, id=gpt_id).first()

        if not gpt:
            return jsonify({"success": False, "message": GPT_TYPE_NOT_FOUND})
        
        # Retrieve all rows that match the conditions
        workflow_entries = (
            session.query(AirflowWorkflow)
            .filter_by(deleted=DELETED_STATUS, record_status=RECORD_STATUS)
            .all()
        )
        gpt_id = gpt.id
        workflow_names_with_gpt = []
        if workflow_entries:
            for entry in workflow_entries:
                # Check if the 'gpts' field is not None and contains the gpt_id
                if entry.gpts is not None:
                    gpts_data = entry.gpts  # Assuming this is a JSON object or list
                    if isinstance(gpts_data, list):  # Ensure gpts is a list of dictionaries
                        for gpt_item in gpts_data:
                            if 'id' in gpt_item and gpt_item['id'] == gpt_id:
                                workflow_names_with_gpt.append(entry.name)   
            
            if workflow_names_with_gpt:
                return jsonify({"success": False, "message": GPT_TYPE_EXIST_IN_WORKFLOW, "workflows": workflow_names_with_gpt})
            
        return jsonify({"success": True, "message": GPT_TYPE_NOT_EXIST_IN_WORKFLOW})
    def update_or_insert_assistant_gpt(self):
        try:
            current_user_id = g.user.id if g.user else None
            api_key = os.getenv("OPENAI_API_KEY")
            # Define the URL
            url = 'https://api.openai.com/v1/assistants'

            # Headers with API key and required beta header
            headers = {
                'Authorization': 'Bearer ' + api_key,
                'Content-Type': 'application/json',
                'OpenAI-Beta': 'assistants=v2'
            }

            # Making a GET request
            response = requests.get(url, headers=headers)

            # Checking if the request was successful (status code 200)
            if response.status_code == 200:
                gpt_info = response.json()
                if gpt_info:
                    # Start a session
                    session = self.appbuilder.get_session()
                    try:
                        # Retrieve all existing assistant records from the database
                        existing_assistants = session.query(AirflowGptTypes).filter_by(
                            type='ASSISTANT',
                            deleted=DELETED_STATUS,
                            record_status=RECORD_STATUS
                        ).all()
                        # Create a set of assistant_ids from the API response
                        api_assistant_ids = {assistant['id'] for assistant in gpt_info['data']}
                        # Extract assistant information from gpt_info dictionary
                        with session.no_autoflush:  # Avoid premature flushing
                            for assistant in gpt_info['data']:
                                assistant_id = assistant['id']
                                name = assistant['name']
                                description = assistant.get('description', '')
                                instructions = assistant.get('instructions', '')
                                if name is not None:
                                    # Check if the assistant already exists in the database
                                    existing_assistant = session.query(AirflowGptTypes).filter_by(
                                        assistant_id=assistant_id,
                                        deleted=DELETED_STATUS,
                                        record_status=RECORD_STATUS
                                    ).first()

                                    if existing_assistant:
                                        # Update existing record
                                        existing_assistant.name = name
                                        existing_assistant.description = description
                                        existing_assistant.instruction = instructions
                                        existing_assistant.type = 'ASSISTANT'
                                    else:
                                        # Insert new record
                                        new_assistant = AirflowGptTypes(
                                            assistant_id=assistant_id,
                                            name=name,
                                            description=description,
                                            instruction=instructions,
                                            type='ASSISTANT',
                                            connection_id=1,
                                            created_by_id=current_user_id,
                                            deleted=DELETED_STATUS,
                                            record_status=RECORD_STATUS
                                        )
                                        session.add(new_assistant)
                                        
                            # Mark records as deleted if they are not in the API response
                            for existing_assistant in existing_assistants:
                                if existing_assistant.assistant_id not in api_assistant_ids:
                                    existing_assistant.deleted = 1

                        session.commit()

                    except Exception as e:
                        session.rollback()
                        logging.error(f"Error occurred during database operation: {e}")
                        raise  # Re-raise to ensure any critical errors are not suppressed

                    finally:
                        session.close()

            else:
                logging.error(f"Failed to retrieve assistants: {response.status_code}")
                logging.error(response.json())

        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")

    def get_assistants_details(gpt_id):

        api_key = os.getenv("OPENAI_API_KEY")
        # API endpoint URL
        url = f'https://api.openai.com/v1/assistants/{gpt_id}'

        # Headers with API key and required beta header
        headers = {
            'Authorization': 'Bearer ' + api_key,
            'Content-Type': 'application/json',
            'OpenAI-Beta': 'assistants=v2'
        }

        # Making a GET request
        response = requests.get(url, headers=headers)
        # Checking if the request was successful (status code 200)
        if response.status_code == 200:
            # Print the response content (list of assistants)
            print(response.json())
            assistant = response.json()
            return assistant
        else:
            # Print error message if request was not successful
            print("Error:", response.text)

    @expose('/add_gpt_access', methods=['POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_gpt_access(self):
        """
        The `add_gpt_access` function provides access to GPT IDs for a given user ID and enables access if specified.
        :return: JSON response with the keys "success" and "message".
        """
        Session = sessionmaker(bind=self.appbuilder.get_session().bind)
        session = Session()
        try:
            if request.method == 'POST':
                gpt_ids = request.json.get('gpt_ids')
                user_data = request.json.get('user_data')
                created_by_id = g.user.id if g.user else None
                updated_by_id = g.user.id if g.user else None
                
                if not gpt_ids:
                    return jsonify({"success": False, "message": "Missing required parameters gpt_ids."})
                if not user_data:
                    return jsonify({"success": False, "message": "Missing required parameters user_data."})
                
                if isinstance(user_data, str):
                    try:
                        user_data_list = json.loads(user_data)
                        if not isinstance(user_data_list, list):
                            raise ValueError("user data should be a list.")
                    except (ValueError, json.JSONDecodeError):
                        return jsonify({"success": False, "message": "Invalid format for user_data."})
                else:
                    user_data_list = user_data

                confirmation_required = False
                with session.no_autoflush:  # Prevent autoflush during this block
                    for gpt_id in gpt_ids:
                        for user in user_data_list: 
                            user_id = user.get('user_id')
                            is_enabled = user.get('is_enabled')

                            if user_id is None or is_enabled is None:
                                return jsonify({"success": False, "message": "user_id and is_enabled must be provided in user_data."})

                            existing_access = session.query(GptUserAccess).filter_by(user_id=user_id, gpt_id=gpt_id,deleted=DELETED_STATUS, record_status=RECORD_STATUS).first()
                            if existing_access:
                                if is_enabled == 0:
                                    used_in_workflow = session.query(AirflowWorkflow).filter(
                                        text("""
                                        EXISTS (
                                            SELECT 1 
                                            FROM json_array_elements(airflow_workflow.gpts) AS elem
                                            WHERE elem->>'id' = :gpt_id
                                        )
                                        """)
                                    ).params(gpt_id=str(gpt_id)).filter(
                                        AirflowWorkflow.created_by_id == user_id,
                                        AirflowWorkflow.deleted == DELETED_STATUS,
                                        AirflowWorkflow.record_status == RECORD_STATUS
                                    ).all()
                                    if used_in_workflow:
                                        confirmation = request.json.get('confirmation', False)
                                        if not confirmation:
                                            return jsonify({"success": True, "requires_confirmation": True})
                                        for workflow in used_in_workflow:
                                            workflow.deleted = CHANGE_DELETED_STATUS
                                existing_access.deleted = DELETED_STATUS if is_enabled == 1 else CHANGE_DELETED_STATUS
                                existing_access.is_enabled = is_enabled
                                existing_access.updated_by_id = updated_by_id
                            else:
                                new_gpt_user_access = GptUserAccess(
                                    gpt_id=gpt_id,
                                    user_id=user_id,
                                    is_enabled=is_enabled,
                                    created_by_id=created_by_id,
                                    updated_by_id=updated_by_id
                                )
                                session.add(new_gpt_user_access)
                
                session.commit()
                return jsonify({"success": True, "message": "Access updated successfully."})

        except Exception as e:
            session.rollback()
            print(f"Error occurred: {e}")
            return jsonify({"success": False, "message": "An error occurred while processing the request."})

        finally:
            session.close()

    @expose('/list_gpt_access', methods=['GET'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def list_gpt_access(self):
        """
        The `list_gpt_access` function retrieves all GPT user access records.
        :return: JSON response with a list of GPT user access records.
        """
        session = self.appbuilder.get_session()
        try:
            gpt_ids = request.args.getlist('gpt_ids', type=int)  # Get gpt_ids from query parameters
            modal_search_query = request.args.get('modal_search', '').strip()
            modal_page = request.args.get('modal_page', 1, type=int)
            modal_per_page = request.args.get('modal_per_page', 10, type=int)
            is_parent_child = 1
            user_alias = aliased(User)
            created_by_fk = g.user.id if g.user else None

            # Get role information of current user
            if created_by_fk:
                user_role = session.query(UserRole).filter_by(user_id=created_by_fk).first()
                current_role_name = session.query(Role.name).filter_by(id=user_role.role_id).scalar() if user_role else None

            client_admin_role = session.query(Role.id).filter(Role.name == CLIENT_ADMIN_ROLE).first()
            client_admin_role_id = client_admin_role.id if client_admin_role else None

            # Get "Default User" role ID for filtering clients if necessary
            default_user_role = session.query(Role.id).filter(Role.name == DEFAULT_ROLE).first()
            default_user_role_id = default_user_role.id if default_user_role else None

            # Step 1: Query all parent users (without pagination)
            query = session.query(
                user_alias.id.label('user_id'),
                user_alias.first_name,
                user_alias.last_name,
                user_alias.email,
                GptUserAccess.is_enabled
            ).join(UserRole, user_alias.id == UserRole.user_id) \
                .outerjoin(
                    GptUserAccess,
                    (GptUserAccess.user_id == user_alias.id) &
                    (GptUserAccess.gpt_id.in_(gpt_ids)) &
                    (GptUserAccess.deleted == DELETED_STATUS) &
                    (GptUserAccess.record_status == RECORD_STATUS)
                ) \
                .filter(
                    user_alias.active == True,
                    user_alias.deleted == DELETED_STATUS,
                    user_alias.record_status == RECORD_STATUS,
                    UserRole.role_id == client_admin_role_id,
                ).distinct(user_alias.id).order_by(user_alias.id.desc())

            # If current user is an admin, only fetch their own record
            if created_by_fk and current_role_name == CLIENT_ADMIN_ROLE:
                is_parent_child = 0
                query = query.filter(user_alias.id == created_by_fk)

            users = query.all()  # Get all parent users (without pagination)

            # Step 2: Prepare response data for main users and retrieve their clients
            user_access_data = []
            for user_access in users:
                # Query to get associated client users for each main user
                client_query = session.query(
                    user_alias.id.label('user_id'),
                    user_alias.first_name,
                    user_alias.last_name,
                    user_alias.email,
                    GptUserAccess.is_enabled
                ).join(UserRole, user_alias.id == UserRole.user_id) \
                    .outerjoin(
                        GptUserAccess,
                        (GptUserAccess.user_id == user_alias.id) &
                        (GptUserAccess.gpt_id.in_(gpt_ids)) &
                        (GptUserAccess.deleted == DELETED_STATUS) &
                        (GptUserAccess.record_status == RECORD_STATUS)
                    ) \
                    .filter(
                        user_alias.active == True,
                        user_alias.deleted == DELETED_STATUS,
                        user_alias.record_status == RECORD_STATUS,
                        UserRole.role_id == default_user_role_id,
                        user_alias.created_by_fk == user_access.user_id
                    ).distinct(user_alias.id).order_by(user_alias.id.desc())

                client_users = client_query.all()

                client_list = [
                    {
                        'user_id': client.user_id,
                        'first_name': client.first_name,
                        'last_name': client.last_name,
                        'email': client.email,
                        'is_enabled': client.is_enabled,
                    } for client in client_users
                ]

                # Append main user data and associated clients
                user_access_data.append({
                    'user_id': user_access.user_id,
                    'is_enabled': user_access.is_enabled,
                    'first_name': user_access.first_name,
                    'last_name': user_access.last_name,
                    'email': user_access.email,
                    'clients': client_list,
                })

            # Step 3: Apply search on both main users and clients after fetching the full dataset
            if modal_search_query:
                filtered_user_access_data = []
                for user in user_access_data:
                    # Check if the main user matches the search
                    if (modal_search_query.lower() in user['first_name'].lower() or
                        modal_search_query.lower() in user['last_name'].lower() or
                        modal_search_query.lower() in user['email'].lower()):
                        filtered_user_access_data.append(user)
                    else:
                        # Check if any client matches the search
                        filtered_clients = [
                            client for client in user['clients'] if (
                                modal_search_query.lower() in client['first_name'].lower() or
                                modal_search_query.lower() in client['last_name'].lower() or
                                modal_search_query.lower() in client['email'].lower()
                            )
                        ]
                        if filtered_clients:
                            user['clients'] = filtered_clients
                            filtered_user_access_data.append(user)

                user_access_data = filtered_user_access_data

            # Step 4: Apply pagination on the filtered data
            modal_total = len(user_access_data)  # Total count after search filtering
            paginated_data = user_access_data[(modal_page - 1) * modal_per_page: modal_page * modal_per_page]

            return jsonify(success=True, data=paginated_data, is_parent_child=is_parent_child,
                        modal_search=modal_search_query, modal_page=modal_page,
                        modal_total=modal_total, modal_per_page=modal_per_page)
        except Exception as e:
            return jsonify(success=False, message=str(e))
        finally:
            session.close()

class Assistants(gpt_type):
    """
    View class for handling '/assistants' routes.
    Inherits all functionality from GptTypeView.
    """
    default_view = "assistants"

    @expose("/")
    @has_access([
        (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
    ])
    def assistants(self):
        """
        Handles requests to '/assistants/' by invoking the 'index' method.
        """
        return self.index()
    
    @expose('/add_assistant', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_gpt_assistants(self):
        """
        Handles '/assistants/add_gpt' by delegating to GptTypeView's add_gpt method.
        """
        return self.add_gpt()
    
    @expose('/edit_assistant/<int:gpt_id>', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def edit_gpt_assistants(self,gpt_id):
        """
        Handles '/assistants/edit_gpt' by delegating to GptTypeView's add_gpt method.
        """
        return self.edit_gpt(gpt_id)
    @expose('/delete_assistant/<int:gpt_id>', methods=['POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def delete_gpt_assistants(self,gpt_id):
        """
        Handles '/assistants/edit_gpt' by delegating to GptTypeView's add_gpt method.
        """
        return self.delete_gpt(gpt_id)
    
    @expose('/check_gpt_exist_workflow/<int:gpt_id>', methods=['GET'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def check_gpt_exist_workflow_assistants(self,gpt_id):
        """
        Handles '/assistants/edit_gpt' by delegating to GptTypeView's add_gpt method.
        """
        return self.check_gpt_exist_workflow(gpt_id)
    
    @expose('/list_gpt_access', methods=['GET'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def list_gpt_access_assistants(self):
        return self.list_gpt_access()
    
    @expose('/add_gpt_access', methods=['POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_gpt_access_assistants(self):
        return self.add_gpt_access()
class QuotesCrawlerManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(QuotesCrawlerManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.runner = CrawlerRunner(get_project_settings())
        self.running = False
        self.crawl_thread = None
    
    def _get_quotes(self, url):
        scraped_data = []
        crawl_complete = Event()
        
        def crawler_results(signal, sender, item, response, spider):
            logging.info(f"Scraped item: {item}")
            scraped_data.append(item)
        
        def handle_spider_closed(spider):
            logging.info("Spider closed, setting crawl complete event")
            crawl_complete.set()
        
        @defer.inlineCallbacks
        def crawl():
            try:
                dispatcher.connect(crawler_results, signal=signals.item_scraped)
                dispatcher.connect(handle_spider_closed, signal=signals.spider_closed)
                logging.info("Starting crawl...")
                yield self.runner.crawl(QuotesSpider, start_url=url)
                logging.info("Crawl completed")
            except Exception as e:
                logging.error(f"Error during crawl: {e}")
                crawl_complete.set()  # Set event even on error
                raise
            finally:
                dispatcher.disconnect(crawler_results, signal=signals.item_scraped)
                dispatcher.disconnect(handle_spider_closed, signal=signals.spider_closed)
        
        def run_reactor_in_thread():
            logging.info("Starting reactor in thread")
            reactor.run(installSignalHandlers=0)
            
        if not self.running:
            self.running = True
            self.crawl_thread = threading.Thread(target=run_reactor_in_thread)
            self.crawl_thread.daemon = True
            self.crawl_thread.start()
            
        reactor.callFromThread(crawl)
        
        # Wait for crawl to complete with timeout
        if not crawl_complete.wait(timeout=300):  # 5 minute timeout
            logging.error("Crawl timed out!")
            return []
            
        return scraped_data

    @staticmethod
    def get_quotes(url):
        """Static method to get quotes from URL"""
        instance = QuotesCrawlerManager()
        return instance._get_quotes(url)
        
    def stop(self):
        """Cleanly stop the crawler and reactor"""
        if self.running:
            reactor.callFromThread(reactor.stop)
            if self.crawl_thread:
                self.crawl_thread.join()
            self.running = False