
from flask import  jsonify, request, g,Flask, url_for
from flask_appbuilder import BaseView, expose
from airflow.security import permissions
from airflow.www.auth import has_access
import json
import os
from user_management.params import *
from workflow.models import Role,User, UserRole,AirflowWorkflow,UserWorkflowAccess
from sqlalchemy import asc, desc, func,cast, JSON
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import requests
from io import BytesIO
from time import sleep
load_dotenv()
logger = logging.getLogger(__name__)
app = Flask(__name__)
import concurrent.futures
csrf = CSRFProtect(app)
from werkzeug.utils import secure_filename
import numpy as np
import re
from sqlalchemy import or_, exists
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
import hashlib
import binascii
import os
from werkzeug.security import generate_password_hash
from sqlalchemy import and_
from sqlalchemy import func, cast, JSON,select,text
from sqlalchemy.orm import joinedload
def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

class user_management(BaseView):
    default_view = "index"

    @expose("/")
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def index(self):
        
        session = self.appbuilder.get_session
        try:
            search_query = request.args.get('search', '').strip()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            current_user_id = g.user.id if g.user else None
            if current_user_id:
                # Query the UserRole table to get the role associated with the current user
                user_role = session.query(UserRole).filter_by(user_id=current_user_id).first()

                if user_role:
                    # Now query the Role table to get the role name based on the role_id from UserRole
                    role = session.query(Role).filter_by(id=user_role.role_id).first()

                    if role:
                        current_role_name = role.name
                    else:
                        current_role_name=None
                else:
                    current_role_name=None
            
            if current_role_name == CLIENT_ADMIN_ROLE:
                
                role = session.query(Role.id).filter(Role.name == DEFAULT_ROLE).first()
                role_id = role.id if role else None
                query = session.query(User).filter(
                        User.created_by_fk == current_user_id,
                        User.deleted==DELETED_STATUS, User.record_status==RECORD_STATUS
                    )
                if role_id:
                    query = query.join(UserRole, User.id == UserRole.user_id).filter(
                        UserRole.role_id == role_id
                    )

                if search_query:
                    query = query.filter(
                        or_(
                            User.first_name.ilike(f'%{search_query}%'),
                            User.username.ilike(f'%{search_query}%'),
                            User.email.ilike(f'%{search_query}%')
                        )
                    )

                total = query.count()
                query = query.order_by(desc(User.id))
                user_info = query.offset((page - 1) * per_page).limit(per_page).all()

                users_info = [
                    {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'user_name':user.username,
                        'email': user.email,
                        'is_active': user.active
                    } for user in user_info
                ]
                

                return self.render_template(
                    '/user_list.html',
                    users_info=users_info,
                    search=search_query,
                    page=page,
                    per_page=per_page,
                    total=total
                )
            else:
                user_list=user_management.get_client_admins_and_users(session, current_user_id, search_query, page, per_page)
                # return {"message":current_role_name, "user_list":user_list["client_user_list"], "total":user_list["total"]}
                return self.render_template(
                    '/all_user_list.html',
                    users_info=user_list['client_user_list'],
                    search=search_query,
                    page=page,
                    per_page=per_page,
                    total=user_list['total']
                )
        finally:
            session.close()
    def get_client_admins_and_users(session, current_user_id, search_query=None, page=1, per_page=10):
        # Step 1: Get "Client Admin" role ID
        client_admin_role = session.query(Role.id).filter(Role.name == CLIENT_ADMIN_ROLE).first()
        client_admin_role_id = client_admin_role.id if client_admin_role else None
        
        # Step 2: Get "Default User" role ID (this is to filter users if necessary)
        default_user_role = session.query(Role.id).filter(Role.name == DEFAULT_ROLE).first()
        default_user_role_id = default_user_role.id if default_user_role else None

        # Step 3: Query all Client Admins
        client_admins_query = session.query(User).join(UserRole, User.id == UserRole.user_id).filter(
            UserRole.role_id == client_admin_role_id,
            User.deleted == DELETED_STATUS, 
            User.record_status == RECORD_STATUS
        )
        
        # Step 4: Add search query for client admins (optional)
        if search_query:
            client_admins_query = client_admins_query.filter(
                or_(
                    User.first_name.ilike(f'%{search_query}%'),
                    User.username.ilike(f'%{search_query}%'),
                    User.email.ilike(f'%{search_query}%')
                )
            )
        # Step 5: Query for users matching the search query
        users_query = session.query(User).filter(
            User.deleted == DELETED_STATUS, 
            User.record_status == RECORD_STATUS,
            User.active == True
        )
        
        if search_query:
            users_query = users_query.filter(
                or_(
                    User.first_name.ilike(f'%{search_query}%'),
                    User.username.ilike(f'%{search_query}%'),
                    User.email.ilike(f'%{search_query}%')
                )
            )
        if default_user_role_id:
            users_query = users_query.join(UserRole, User.id == UserRole.user_id).filter(
                UserRole.role_id == default_user_role_id
            )

        # Step 6: Collect all client admin IDs related to the users
        users = users_query.all()
        client_admin_ids_from_users = {user.created_by_fk for user in users}
        # Step 7: Merge client admin results (both from client admin search and user search)
        client_admins_query = client_admins_query.union(
            session.query(User).filter(User.id.in_(client_admin_ids_from_users))
        )
        # Step 5: Pagination and counting
        total_client_admins = client_admins_query.count()
        client_admins_query = client_admins_query.order_by(desc(User.id))
        client_admins = client_admins_query.offset((page - 1) * per_page).limit(per_page).all()

        # Step 6: Prepare the final JSON response
        result = []

        for client_admin in client_admins:
            # Query the users created by this Client Admin
            users_query = session.query(User).filter(
                User.created_by_fk == client_admin.id,
                User.deleted == DELETED_STATUS, 
                User.record_status == RECORD_STATUS,
                User.active == True
            )
            # Step 7: Add search query for users (optional)
            if search_query:
                users_query = users_query.filter(
                    or_(
                        User.first_name.ilike(f'%{search_query}%'),
                        User.username.ilike(f'%{search_query}%'),
                        User.email.ilike(f'%{search_query}%')
                    )
                )

            if default_user_role_id:
                users_query = users_query.join(UserRole, User.id == UserRole.user_id).filter(
                    UserRole.role_id == default_user_role_id
                )

            users = users_query.all()

            # Prepare users list for this client admin
            users_list = [
                {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_name':user.username,
                    'email': user.email,
                    'is_active': user.active,
                    'role': DEFAULT_ROLE
                } for user in users
            ]

            # Append client admin and their users to the result
            result.append({
                'id': client_admin.id,
                'first_name': client_admin.first_name,
                'last_name': client_admin.last_name,
                'user_name':client_admin.username,
                'email': client_admin.email,
                'is_active': client_admin.active,
                'users': users_list,
                'role': CLIENT_ADMIN_ROLE
            })
        return {"client_user_list":result,"total":total_client_admins}

    @expose('/add_user', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_user(self):
        """
        Adds a new user to the system and assigns the default user role.
        """
        try:
            with self.appbuilder.get_session() as session:
                if request.method == 'POST':
                    first_name = request.form.get('first_name')
                    last_name = request.form.get('last_name')
                    username = request.form.get('username')
                    active = request.form.get('is_active')
                    active_value = True if active == 'true' else False
                    email = request.form.get('email')
                    password = request.form.get('password')
                    confirm_password = request.form.get('confirm_password')
                    role = request.form.get('role')
                    user_limit = request.form.get('user_limit')

                    # Validate first_name and last_name to not contain numbers
                    if any(char.isdigit() for char in first_name) or any(char.isdigit() for char in last_name):
                        return jsonify({"success": False, "message": "Invalid name format."})

                    # Validate email format
                    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                    if not re.match(email_regex, email):
                        return jsonify({"success": False, "message": "Invalid email format."})

                    # Validate uniqueness of username
                    existing_user = session.query(User).filter(
                        User.username == username,
                        User.deleted == DELETED_STATUS,
                        User.record_status == RECORD_STATUS
                    ).first()
                    
                    if existing_user:
                        return jsonify({"success": False, "message": USERNAME_EXIST})
                    
                    # Validate uniqueness of email
                    existing_email = session.query(User).filter(
                        User.email == email,
                        User.deleted == DELETED_STATUS,
                        User.record_status == RECORD_STATUS
                    ).first()
                    
                    if existing_email:
                        return jsonify({"success": False, "message": EMAIL_EXIST})
                    
                    # Ensure password and confirm password are equal
                    if password.strip() != confirm_password.strip():
                        return jsonify({"success": False, "message": PASSWORD_MUST_MATCH})
                    
                    # User limit validation only for client admin
                    if user_limit is None:
                        current_user_id = g.user.id if g.user else None
                        client_admin = session.query(User).filter(
                            User.id == current_user_id,
                            User.deleted == DELETED_STATUS,
                            User.record_status == RECORD_STATUS
                        ).first()
                        created_user_count = session.query(User).filter(
                            User.created_by_fk == current_user_id,
                            User.deleted == DELETED_STATUS,
                            User.record_status == RECORD_STATUS
                        ).count()

                        if (created_user_count + 1) >= client_admin.user_limit:
                            return jsonify({"success": False, "message": USER_LIMIT_EXCEEDED})

                    encrypted_password = generate_password_hash(password)
                    
                    # Save data to the database
                    new_user = User(
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                        active=active_value,
                        email=email,
                        password=encrypted_password,
                        created_by_fk=g.user.id if g.user else None,
                        user_limit=user_limit if user_limit else 0
                    )
                    session.add(new_user)
                    session.commit()

                    if role:
                        # Save the User Role details
                        user_role = UserRole(
                            user_id=new_user.id,
                            role_id=role
                        )
                        session.add(user_role)
                        session.commit()

                    return jsonify({"success": True, "message": ADD_USER_SUCCESS})
                
                # Handle GET request
                current_user_id = g.user.id if g.user else None
                user_role_alias = aliased(UserRole)
                role_alias = aliased(Role)

                # Fetch the user's role details
                user_role_details = None
                try:
                    user_role_details = session.query(role_alias.name, role_alias.is_superadmin).\
                        select_from(user_role_alias).\
                        join(role_alias, user_role_alias.role_id == role_alias.id).\
                        filter(user_role_alias.user_id == current_user_id).\
                        one()
                except Exception:
                    user_role_details = None

                # Determine the role to be assigned
                role = None
                is_superadmin = 0
                if user_role_details:
                    if user_role_details.is_superadmin == 1:
                        is_superadmin = 1
                        role = session.query(Role).filter(Role.name.like("%Client Admin%")).one_or_none()
                    elif "Client Admin" in user_role_details:
                        role = session.query(Role).filter(Role.name.like("%Default User%")).one_or_none()

                # Render the template
                return self.render_template("/user_add.html", user="", role_list=role, user_role="", is_superadmin=is_superadmin)

        except Exception as e:
            logging.error(f"Error adding user: {str(e)}")  # Log the error
            return jsonify({"success": False, "message": "An unexpected error occurred."}), 500


    @expose('/edit_user/<int:user_id>', methods=['GET', 'POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def edit_user(self, user_id):
        """
        Edits an existing user in the system.

        This function handles both GET and POST requests:
        - For GET requests, it retrieves the user details and renders a form for editing the user's information.
        - For POST requests, it processes the submitted form data to update the user's details in the database.

        Parameters:
            user_id (int): The ID of the user to edit.

        The function performs the following operations:
            1. Validates the uniqueness of the `username` and `email` fields to ensure no duplicates exist.
            2. Updates the user's information in the database, including their first name, last name, username, active status, email, and user limit.

        Returns:
            - On success (POST): A JSON response indicating success, along with a success message.
            - On failure (POST): A JSON response indicating failure, along with an appropriate error message.
            - On GET: Renders the user edit form pre-filled with the user's existing data.

        Raises:
            - Exception: If any unexpected error occurs during database operations or session management.

        Example:
            To edit a user via POST request:
            ```
            POST /edit_user/1
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "is_active": "on",
                "email": "janedoe@example.com",
                "role": "default_user_role_id",
                "user_limit": 10
            }
            ```

        Notes:
            - The function checks for user existence based on the provided `user_id` and ensures that it is valid.
            - All interactions with the database are performed within a session context to ensure integrity and proper error handling.
        """
        with self.appbuilder.get_session() as session:  # Use context manager for session
            user = (
                session.query(User, UserRole.role_id)
                .outerjoin(UserRole, User.id == UserRole.user_id)
                .filter(
                    User.deleted == DELETED_STATUS,
                    User.record_status == RECORD_STATUS,
                    User.id == user_id
                )
                .first()
            )
            if not user:
                return jsonify({"success": False, "message": USER_NOT_FOUND}), 404
            
            user_obj, role_id = user
            try:
                if request.method == 'POST':
                    first_name = request.form.get('first_name')
                    last_name = request.form.get('last_name')
                    username = request.form.get('username')
                    active = request.form.get('is_active')
                    active_value = True if active == 'true' else False
                    email = request.form.get('email')
                    role = request.form.get('role')
                    user_limit = request.form.get('user_limit')

                    # Validate first_name and last_name to not contain numbers
                    if any(char.isdigit() for char in first_name) or any(char.isdigit() for char in last_name):
                        return jsonify({"success": False, "message": "Invalid name format."})

                    # Validate email format
                    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                    if not re.match(email_regex, email):
                        return jsonify({"success": False, "message": "Invalid email format."})

                    # Validate uniqueness of username
                    existing_user = session.query(User).filter(
                        and_(User.username == username, User.id != user_id, User.deleted == DELETED_STATUS, User.record_status == RECORD_STATUS)
                    ).first()
                    if existing_user:
                        return jsonify({"success": False, "message": "Username already exists"})

                    # Validate uniqueness of email
                    existing_email = session.query(User).filter(
                        and_(User.email == email, User.id != user_id, User.deleted == DELETED_STATUS, User.record_status == RECORD_STATUS)
                    ).first()
                    if existing_email:
                        return jsonify({"success": False, "message": "Email already exists"})
                    
                    if user_limit:
                        user_limit = int(user_limit)
                        created_user_count = session.query(User).filter(
                            and_(
                                User.created_by_fk == user_id,
                                User.deleted == DELETED_STATUS,
                                User.record_status == RECORD_STATUS
                            )
                        ).count()
                        if created_user_count >= user_limit:
                            return jsonify({
                                "success": False,
                                "message": f"Invalid User Limit. {created_user_count+1} users have already been created."
                            })

                    # Update user details
                    user_obj.first_name = first_name
                    user_obj.last_name = last_name
                    user_obj.username = username
                    user_obj.active = active_value
                    user_obj.email = email
                    user_obj.changed_by_fk = g.user.id if g.user else None
                    user_obj.user_limit = user_limit if user_limit else 0

                    session.commit()

                    return jsonify({"success": True, "message": "User updated successfully"})
                
                # Fetch user role details for rendering the edit form
                current_user_id = g.user.id if g.user else None
                user_role_alias = aliased(UserRole)
                role_alias = aliased(Role)

                try:
                    user_role_details = session.query(role_alias.name, role_alias.is_superadmin).\
                        select_from(user_role_alias).\
                        join(role_alias, user_role_alias.role_id == role_alias.id).\
                        filter(user_role_alias.user_id == current_user_id).\
                        one()
                except Exception:
                    user_role_details = None
                
                # Determine the role to be assigned
                is_superadmin = 0
                role = None
                if user_role_details:
                    if user_role_details.is_superadmin == 1:
                        is_superadmin = 1
                        role = session.query(Role).filter(Role.name.like("%Client Admin%")).one_or_none()
                    elif "Client Admin" in user_role_details:
                        role = session.query(Role).filter(Role.name.like("%Default User%")).one_or_none()
                
                # Render the edit form with user data
                return self.render_template("/user_add.html", user=user_obj, role_list=role, user_role=role_id, is_superadmin=is_superadmin)

            except Exception as e:
                session.rollback()  # Roll back if there's an error
                return jsonify({"success": False, "message": str(e)}), 500


    @expose('/delete_user/<int:user_id>', methods=['POST'])
    @has_access(
        [
            (permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE),
        ]
    )
    def delete_user(self, user_id):
        session = self.appbuilder.get_session
        try:
            user = session.query(User).filter_by(
                deleted=DELETED_STATUS, record_status=RECORD_STATUS, id=user_id).first()

            if not user:
                return jsonify({"success": False, "message": USER_NOT_FOUND})
            
            # Soft delete the user record
            user.deleted = 1
            user.active = 0
            user.changed_by_fk = g.user.id if g.user else None
            session.commit()
            session.close()

            return jsonify({"success": True, "message": USER_DELETE_SUCCESS_MESSAGE})
        except Exception as e:
            logger.error(f"Error deleting User: {e}")
            return jsonify({"success": False, "message": USER_DELETE_SUCCESS_FAILURE})
        
    @expose('/list_workflow_access', methods=['GET'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def list_workflow_access(self):
        """
        Retrieve the workflow access for users and their associated clients.
        """
        session = self.appbuilder.get_session()
        try:
            workflow_id = request.args.get('workflow_id', type=int)
            modal_search_query = request.args.get('modal_search', '').strip()
            modal_page = request.args.get('modal_page', 1, type=int)
            modal_per_page = request.args.get('modal_per_page', 10, type=int)
            is_parent_child = 1
            user_alias = aliased(User)
            created_by_fk = g.user.id if g.user else None

            # Get role information of the current user
            if created_by_fk:
                user_role = session.query(UserRole).filter_by(user_id=created_by_fk).first()
                current_role_name = session.query(Role.name).filter_by(id=user_role.role_id).scalar() if user_role else None

            client_admin_role = session.query(Role.id).filter(Role.name == CLIENT_ADMIN_ROLE).first()
            client_admin_role_id = client_admin_role.id if client_admin_role else None

            default_user_role = session.query(Role.id).filter(Role.name == DEFAULT_ROLE).first()
            default_user_role_id = default_user_role.id if default_user_role else None

            # Step 1: Query all parent users (without pagination)
            query = session.query(
                user_alias.id.label('user_id'),
                user_alias.first_name,
                user_alias.last_name,
                user_alias.email,
                UserWorkflowAccess.is_enabled
            ).join(UserRole, user_alias.id == UserRole.user_id) \
                .outerjoin(
                    UserWorkflowAccess,
                    (UserWorkflowAccess.user_id == user_alias.id) &
                    (UserWorkflowAccess.workflow_id == workflow_id) &
                    (UserWorkflowAccess.deleted == DELETED_STATUS) &
                    (UserWorkflowAccess.record_status == RECORD_STATUS)
                ) \
                .filter(
                    user_alias.active == True,
                    user_alias.deleted == DELETED_STATUS,
                    user_alias.record_status == RECORD_STATUS,
                    UserRole.role_id == client_admin_role_id,
                ).distinct(user_alias.id).order_by(user_alias.id.desc())

            if created_by_fk and current_role_name == CLIENT_ADMIN_ROLE:
                is_parent_child = 0
                query = query.filter(user_alias.id == created_by_fk)

            users = query.all()  # Get all parent users (without pagination)

            # Step 2: Prepare response data for main users and retrieve their clients
            user_access_data = []
            for user_access in users:
                client_query = session.query(
                    user_alias.id.label('user_id'),
                    user_alias.first_name,
                    user_alias.last_name,
                    user_alias.email,
                    UserWorkflowAccess.is_enabled
                ).join(UserRole, user_alias.id == UserRole.user_id) \
                    .outerjoin(
                        UserWorkflowAccess,
                        (UserWorkflowAccess.user_id == user_alias.id) &
                        (UserWorkflowAccess.workflow_id == workflow_id) &
                        (UserWorkflowAccess.deleted == DELETED_STATUS) &
                        (UserWorkflowAccess.record_status == RECORD_STATUS)
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

    
    @expose('/add_workflow_access', methods=['POST'])
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def add_workflow_access(self):
        Session = sessionmaker(bind=self.appbuilder.get_session().bind)
        session = Session()
        try:
            if request.method == 'POST':
                workflow_id = request.json.get('workflow_id')
                user_data = request.json.get('user_data')
                created_by_id = g.user.id if g.user else None
                updated_by_id = g.user.id if g.user else None
                
                if not workflow_id:
                    return jsonify({"success": False, "message": "Missing required parameters workflow_id."})
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
                
                with session.no_autoflush:  # Prevent autoflush during this block
                    for user in user_data_list: 
                        user_id = user.get('user_id')
                        is_enabled = user.get('is_enabled')

                        if user_id is None or is_enabled is None:
                            return jsonify({"success": False, "message": "user_id and is_enabled must be provided in user_data."})

                        existing_access = session.query(UserWorkflowAccess).filter_by(user_id=user_id, workflow_id=workflow_id).first()
                        if existing_access:
                            existing_access.deleted = DELETED_STATUS
                            existing_access.is_enabled = is_enabled
                            existing_access.updated_by_id = updated_by_id
                        else:
                            new_gpt_user_access = UserWorkflowAccess(
                                workflow_id=workflow_id,
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