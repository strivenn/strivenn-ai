
from flask import jsonify,request, flash, g, redirect, url_for
from flask_appbuilder import BaseView, expose
from airflow.security import permissions
from airflow.www.auth import has_access
from classes.dalle_gpt import DalleGpt
from openai import OpenAI,OpenAIError
from classes.article_gpt import ArticleGpt
from classes.grammar_check_gpt import GrammarCheck
import json
from classes.seo_gpt import SEOGpt

from workflow.models import AirflowGptTypes, AirflowWorkflow
from sqlalchemy import func


class Chat(BaseView):
    default_view = "search"
    @expose("/")
    
    def search(self):
        workflow_id=request.json.get('id')
        prompt=request.json.get('prompt')
        """
        This method is used to render the prompt.html template for creating a workflow.
        
        Returns:
            A rendered template with the name "Create Workflow".
        """
        session = self.appbuilder.get_session
        workflow = session.query(AirflowWorkflow).filter_by(id=workflow_id).first()

        if workflow:
            # Assuming gpt_ids is an attribute of AirflowWorkflow
            print("gpt_ids", workflow.gpt_ids)
            gpt_ids_list = workflow.gpt_ids
            # Sort the list based on the 'sort_order' key
            sorted_gpt_ids = sorted(gpt_ids_list, key=lambda x: x.get('sort_order', 0))

            # Extract the first gpt_id
            first_gpt_id = sorted_gpt_ids[0]['gpt_id'] if sorted_gpt_ids else None
            print("first_gpt_id",first_gpt_id)
        return self.render_template("/prompt.html", name="Create Workflow",workflow_info ="{'msg':'created'}")
        