from flask import  jsonify, request, g,Flask, url_for
from flask_appbuilder import BaseView, expose
from airflow.security import permissions
from airflow.www.auth import has_access
import json
import os
import re
from sqlalchemy import or_, exists
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy import asc, desc, func,cast, JSON
from urllib.parse import urljoin
from workflow.models import AirflowGptTypes, AirflowWorkflow, Role,User, UserRole
from workflow.params import *
from werkzeug.security import generate_password_hash

class ClientAdmin(BaseView):

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
        This method is the index page for the workflow views.
        It renders the "workflow.html" template with the name "Chat".
        """
        session = self.appbuilder.get_session
        current_user_id = g.user.id if g.user else None
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        user_role_alias = aliased(UserRole)
        role = session.query(Role.id).filter(Role.name == "Client Admin").first()
        if role:
            role_id = role.id
            query = session.query(User).filter(User.deleted == 0,User.record_status == 1).\
                join(user_role_alias, User.id == user_role_alias.user_id).\
                filter(user_role_alias.role_id == role_id)
            total = query.count()
            query = query.order_by(desc(User.id))
            user_info = query.offset((page - 1) * per_page).limit(per_page).all()
        else:
            print("Role not found")
            user_info = []
            total=0
        
        return self.render_template(
                '/client_admin_list.html',
                client_info=user_info,
                search=search_query,
                page=page,
                per_page=per_page,
                total=total
                
            )
    @expose('/add_client', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_client(self):
        """
        The `add_gpt` function adds a new GPT (Generative Pre-trained Transformer) type to the database.
        :return: The code is returning a JSON response. If the request method is 'POST', it returns a
        JSON object with the keys "success" and "message". If the request method is not 'POST', it
        renders a template. If there is an OpenAIError, it returns the error as a JSON response.
        """
        session = self.appbuilder.get_session()
        
        try:
            if request.method == 'POST':
                firstname = request.form.get('firstname')
                lastname = request.form.get('lastname')
                username = request.form.get('username')
                is_active = request.form.get('active')
                email = request.form.get('email')
                password = request.form.get('password')
                confirmpassword = request.form.get('confirmpassword')
                created_by_id = g.user.id if g.user else None
                created_on = func.now()
                user_limit = request.form.get('userlimit')
                encrypted_password = generate_password_hash(password)
                # Check for duplicate workflow name
                # active_value = True if is_active == 'on' else False
                if is_active == 'true':
                    active_value = True  # Convert 'true' to True, 'false' to False
                else:
                    active_value = False  # Treat None as False
                               
                username_exists = (
                    session.query(User)
                    .filter(
                        (func.lower(User.username) == func.lower(username)),
                        User.deleted == DELETED_STATUS,
                        User.record_status == RECORD_STATUS
                    )
                    .first()
                )

                if username_exists:
                    return jsonify({"success": False, "message": "User Name already exists."})
                

                email_exists = (
                    session.query(User)
                    .filter(
                        (func.lower(User.email) == func.lower(email)),
                        User.deleted == DELETED_STATUS,
                        User.record_status == RECORD_STATUS
                    )
                    .first()
                )
                if email_exists:
                    return jsonify({"success": False, "message": "Email already exists."})
                if password != confirmpassword :
                    return jsonify({"success": False, "message": "Password and Confirm Password do not match."})
                
                # Save data to the database
                create_new_client = User(
                    first_name=firstname,
                    last_name=lastname,
                    username=username,
                    active=active_value,
                    email=email,
                    password=encrypted_password,
                    created_by_fk=created_by_id,
                    user_limit=user_limit,
                    created_on=created_on
                    )
                   
                session.add(create_new_client)
                session.commit()
                if create_new_client:
                    # Get Client Admin role id or create it
                    role = session.query(Role.id).filter(Role.name == "Client Admin").first()
                    
                    if not role:
                        role = Role(name='Client Admin', is_superadmin=0)
                        session.add(role)
                        session.commit()
                        
                    create_role=UserRole(
                        user_id=create_new_client.id,
                        role_id=role.id)
                    session.add(create_role)
                    session.commit()

                return jsonify({"success": True, "message": "Client Admin created successfully."})
            
            return self.render_template("/client_admin_create.html", clientadmin="")
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
        finally:
            session.close()

    @expose('/edit_client/<int:client_id>', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def edit_client(self, client_id):
        """
        Handle editing an existing client.

        :param client_id: ID of the client to be edited.
        :return: JSON response for 'POST' requests with the status and message of the operation.
                Renders a template with the client data for 'GET' requests.
        """
        session = self.appbuilder.get_session()

        try:
            if request.method == 'POST':
                # Retrieve form data
                firstname = request.form.get('firstname')
                lastname = request.form.get('lastname')
                username = request.form.get('username')
                is_active = request.form.get('active')
                email = request.form.get('email')
                password = request.form.get('password')
                confirmpassword = request.form.get('confirmpassword')
                user_limit = request.form.get('userlimit')

                # Fetch the existing client
                client = session.query(User).filter(User.id == client_id).first()

                if not client:
                    return jsonify({"success": False, "message": "Client not found."})

                # Update client details
                if username:
                    username_exists = session.query(User).filter(
                        func.lower(User.username) == func.lower(username),
                        User.id != client_id,
                        User.deleted == DELETED_STATUS,
                        User.record_status == RECORD_STATUS
                    ).first()
                    if username_exists:
                        return jsonify({"success": False, "message": "Username already exists."})
                    client.username = username

                if email:
                    email_exists = session.query(User).filter(
                        func.lower(User.email) == func.lower(email),
                        User.id != client_id,
                        User.deleted == DELETED_STATUS,
                        User.record_status == RECORD_STATUS
                    ).first()
                    if email_exists:
                        return jsonify({"success": False, "message": "Email already exists."})
                    client.email = email

                if password:
                    if password != confirmpassword:
                        return jsonify({"success": False, "message": "Passwords do not match."})
                    client.password = generate_password_hash(password)

                client.first_name = firstname
                client.last_name = lastname
                client.active = True if is_active == 'true' else False
                client.user_limit = user_limit

                session.commit()

                return jsonify({"success": True, "message": "Client updated successfully."})

            # Handle 'GET' request to display the current client details
            client = session.query(User).filter(User.id == client_id).first()

            if not client:
                return jsonify({"success": False, "message": "Client not found."})

            return self.render_template("/client_admin_create.html", clientadmin=client)

        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

        finally:
            session.close()

    @expose('/delete_client/<int:client_id>', methods=['POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def delete_client(self, client_id):
        """
        Deletes a client admin from the database.
        :param id: The ID of the client admin to be deleted.
        :return: A JSON response with success status and message.
        """
        session = self.appbuilder.get_session()
        current_user_id = g.user.id if g.user else None
       
        print(f"Searching for client with ID: {client_id}")
        client = session.query(User).filter(User.id == client_id).first()
        print(client, "client found")
        if not client:
            return jsonify({"success": False, "message": "Client Admin not found."})
        
        client.deleted=1
        client.record_status = 1
        client.changed_by_fk = current_user_id
       
        try:
            # Your code...
            session.commit()
            return jsonify({"success": True, "message": "Client Admin deleted successfully."})
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)})
        finally:
            session.close()