from sqlalchemy import Boolean, Column, Integer, Text, TIMESTAMP, JSON,SmallInteger,String,DateTime, ForeignKey, Table, Enum, Date, Time, Float, BigInteger, Numeric, UniqueConstraint, Index, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AirflowWorkflow(Base):
    """
    Represents an Airflow workflow.

    Attributes:
        id (int): The unique identifier of the workflow.
        name (str): The name of the workflow.
        gpt_ids (list): The list of GPT IDs associated with the workflow.
        created_by_id (int): The ID of the user who created the workflow.
        updated_by_id (int): The ID of the user who last updated the workflow.
        created_at (datetime): The timestamp when the workflow was created.
        updated_at (datetime): The timestamp when the workflow was last updated.
        deleted (int): Indicates whether the workflow is deleted (0 for not deleted, 1 for deleted).
        record_status (int): The status of the workflow (1 for active, 0 for inactive).
    """

    __tablename__ = 'airflow_workflow'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    gpt_ids = Column(JSON, nullable=False)
    gpts = Column(JSON, nullable=False)
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    deleted = Column(Integer, nullable=False, default=0)
    record_status = Column(Integer, nullable=False, default=1)
    workflow_type = Column(Text, nullable=True) 

class AirflowGptTypes(Base):
    """
    Represents the Airflow GPT types table.

    Attributes:
        id (int): The primary key of the table.
        name (str): The name of the GPT type.
        description (str): The description of the GPT type.
        connection_id (int): The ID of the connection associated with the GPT type.
        created_at (datetime): The timestamp when the record was created.
        updated_at (datetime): The timestamp when the record was last updated.
        created_by_id (int): The ID of the user who created the record.
        updated_by_id (int): The ID of the user who last updated the record.
        record_status (int): The status of the record.
        deleted (int): Indicates whether the record is deleted or not.
    """

    __tablename__ = 'airflow_gpt_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    instruction = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    connection_id = Column(Integer, nullable=False)
    file = Column(Text, nullable=True)
    assistant_id = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    record_status = Column(SmallInteger, nullable=False, default=1)
    deleted = Column(SmallInteger, nullable=False, default=0)
    is_web_scrape = Column(SmallInteger, nullable=False, default=0)


class AirflowChat(Base):
    

    __tablename__ = 'airflow_chat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    workflow_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    record_status = Column(SmallInteger, nullable=False, default=1)
    deleted = Column(SmallInteger, nullable=False, default=0)

class AirflowChatDetails(Base):
    

    __tablename__ = 'airflow_chat_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    chat_id = Column(Integer, nullable=False)
    workflow_id = Column(Integer, nullable=False)
    response = Column(JSON, nullable=False)
    gpt_type_id = Column(Integer, nullable=False)
    status = Column(Boolean, nullable=False)
    thread_id = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    record_status = Column(SmallInteger, nullable=False, default=1)
    deleted = Column(SmallInteger, nullable=False, default=0)
class GptUserAccess(Base):
    __tablename__ = 'gpt_user_access'

    id = Column(Integer, primary_key=True, autoincrement=True)
    gpt_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    is_enabled = Column(SmallInteger, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    record_status = Column(SmallInteger, nullable=False, default=1)
    deleted = Column(SmallInteger, nullable=False, default=0)

class User(Base):
    __tablename__ = 'ab_user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(256), nullable=False)
    last_name = Column(String(256), nullable=False)
    username = Column(String(512), nullable=False, unique=True, index=True)
    password = Column(String(256))
    active = Column(Boolean)
    email = Column(String(512), nullable=False, unique=True)
    last_login = Column(DateTime)
    login_count = Column(Integer)
    fail_login_count = Column(Integer)
    created_on = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    changed_on = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by_fk = Column(Integer, ForeignKey('ab_user.id'))
    user_limit = Column(Integer, nullable=False, default=0)
    deleted = Column(SmallInteger, nullable=False, default=0)
    record_status = Column(SmallInteger, nullable=False, default=1)
    
class Role(Base):
    __tablename__ = 'ab_role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True)
    is_superadmin = Column(SmallInteger, default=0, nullable=False)

class UserRole(Base):
    __tablename__ = 'ab_user_role'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    role_id = Column(Integer)

class UserWorkflowAccess(Base):
    __tablename__ = 'user_workflow_access'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    is_enabled = Column(SmallInteger, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    record_status = Column(SmallInteger, nullable=False, default=1)
    deleted = Column(SmallInteger, nullable=False, default=0)