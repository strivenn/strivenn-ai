-- Adminer 4.8.1 PostgreSQL 13.13 (Debian 13.13-1.pgdg120+1) dump
DROP TABLE IF EXISTS "airflow_chat";
CREATE TABLE "airflow_chat" (
     "id" serial NOT NULL,
    PRIMARY KEY ("id"),
    "name" character varying NOT NULL,
    "workflow_id" integer NOT NULL,
    "created_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,  
    "created_by_id" integer NOT NULL,
    "updated_by_id" integer,
    "record_status" smallint NOT NULL,
    "deleted" smallint NOT NULL
    
) WITH (oids = false);


DROP TABLE IF EXISTS "airflow_chat_details";
CREATE TABLE "airflow_chat_details" (
     "id" serial NOT NULL,
  PRIMARY KEY ("id"),
    "prompt" character varying NOT NULL,
    "response" json NOT NULL,
    "workflow_id" integer NOT NULL,
    "chat_id" integer NOT NULL,
    "gpt_type_id" integer NOT NULL,
    "status" boolean DEFAULT false NOT NULL,
    "created_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,  
    "created_by_id" integer NOT NULL,
    "updated_by_id" integer,
    "record_status" smallint NOT NULL,
    "deleted" smallint NOT NULL
   
) WITH (oids = false);


DROP TABLE IF EXISTS "airflow_gpt_types";
CREATE TABLE "airflow_gpt_types" (
  "id" serial NOT NULL,
  PRIMARY KEY ("id"),
  "name" text NOT NULL,
  "description" text NULL,
  "instruction" text,
  "type" text,
  "connection_id" integer NOT NULL,
  "created_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "created_by_id" integer NOT NULL,
  "updated_by_id" integer NULL,
  "record_status" smallint NOT NULL DEFAULT '1',
  "deleted" smallint NOT NULL DEFAULT '0'
);


DROP TABLE IF EXISTS "airflow_workflow";
CREATE TABLE "airflow_workflow" (
  "id" serial NOT NULL,
  PRIMARY KEY ("id"),
  "name" text NOT NULL,
  "gpt_ids" json NOT NULL,
  "gpts" json NOT NULL,
  "created_by_id" integer NOT NULL,
  "updated_by_id" integer NULL,
  "created_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,  
  "deleted" integer NOT NULL DEFAULT '0',
  "record_status" integer NOT NULL DEFAULT '1'
);


DROP TABLE IF EXISTS "gpt_user_access";
CREATE TABLE "gpt_user_access" (
  "id" serial NOT NULL,
  PRIMARY KEY ("id"),
  "gpt_id" integer NOT NULL,
  "user_id" integer NOT NULL,
  "is_enabled" smallint NOT NULL DEFAULT '0',
  "created_by_id" integer NOT NULL,
  "updated_by_id" integer NULL,
  "created_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,  
  "deleted" integer NOT NULL DEFAULT '0',
  "record_status" integer NOT NULL DEFAULT '1'
);

ALTER TABLE ONLY "gpt_user_access" ADD CONSTRAINT "gpt_user_access_fk1" FOREIGN KEY (user_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "gpt_user_access" ADD CONSTRAINT "gpt_user_access_fk2" FOREIGN KEY (created_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "gpt_user_access" ADD CONSTRAINT "gpt_user_access_fk3" FOREIGN KEY (updated_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "gpt_user_access" ADD CONSTRAINT "gpt_user_access_fk4" FOREIGN KEY (gpt_id) REFERENCES airflow_gpt_types(id) NOT DEFERRABLE;

ALTER TABLE ONLY "airflow_chat_details" ADD CONSTRAINT "airflow_chat_details_fk0" FOREIGN KEY (workflow_id) REFERENCES airflow_workflow(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_chat_details" ADD CONSTRAINT "airflow_chat_details_fk1" FOREIGN KEY (gpt_type_id) REFERENCES airflow_gpt_types(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_chat_details" ADD CONSTRAINT "airflow_chat_details_fk2" FOREIGN KEY (created_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_chat_details" ADD CONSTRAINT "airflow_chat_details_fk3" FOREIGN KEY (updated_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_chat_details" ADD CONSTRAINT "airflow_chat_details_fk0" FOREIGN KEY (chat_id) REFERENCES airflow_chat(id) NOT DEFERRABLE;

ALTER TABLE ONLY "airflow_gpt_types" ADD CONSTRAINT "airflow_gpt_types_fk0" FOREIGN KEY (connection_id) REFERENCES connection(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_gpt_types" ADD CONSTRAINT "airflow_gpt_types_fk1" FOREIGN KEY (created_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_gpt_types" ADD CONSTRAINT "airflow_gpt_types_fk2" FOREIGN KEY (updated_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;

ALTER TABLE ONLY "airflow_workflow" ADD CONSTRAINT "airflow_workflow_fk0" FOREIGN KEY (created_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_workflow" ADD CONSTRAINT "airflow_workflow_fk1" FOREIGN KEY (updated_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;

ALTER TABLE ONLY "airflow_chat" ADD CONSTRAINT "airflow_chat_fk0" FOREIGN KEY (workflow_id) REFERENCES airflow_workflow(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_chat" ADD CONSTRAINT "airflow_chat_fk2" FOREIGN KEY (created_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "airflow_chat" ADD CONSTRAINT "airflow_chat_fk3" FOREIGN KEY (updated_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;

-- 2023-12-13 12:52:46.178568+00

INSERT INTO "connection" ("conn_id", "conn_type", "description", "host", "schema", "login", "password", "port", "is_encrypted", "is_extra_encrypted", "extra")
VALUES ('', 'sample connection', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO "airflow_gpt_types" ("name", "description","instruction","type", "connection_id", "created_at", "updated_at", "created_by_id", "updated_by_id", "record_status", "deleted")VALUES 
('Idea GPT', 'The go-to solution for sparking creativity and generating fresh blog ideas effortlessly.','Generate a list of blog ideas. Provide unique and engaging topics that would captivate readers and encourage them to explore further. Each idea should be concise and creative, catering to a broad audience interested.','GPT', '1', now(), now(), '1', NULL, '1', '0'),
('Draft Article GPT', 'An innovative tool designed to effortlessly turn your blog ideas and bullet points into fully drafted articles.','Generate a comprehensive article based on the given prompt. The article should be well-researched, include key insights, and provide a balanced perspective on the topic. Ensure that it has a clear structure, covering major points, supporting evidence, and a compelling conclusion.','GPT', '1', now(), now(), '1', NULL, '1', '0'),
('Einstein GPT', 'A revolutionary approach to article refinement by tapping into the collective knowledge of a diverse group of individuals.','Give me a five experts name with their explanation on','GPT', '1', now(), now(), '1', NULL, '1', '0'),
('Grammarly GPT', 'A trusted companion for achieving flawless content.','Please Follow the steps and Give the grammar corrected sentence 
                    1. Correct any grammatical errors in the text.
                    2. Ensure proper punctuation and sentence structure.
                    3. Flag any ambiguous or unclear phrases for clarification.
                    4. Suggest improvements for overall coherence and flow.
                    5. Do not change the original meaning of the text.
                    6.Only return corrected text.Additional texts no needed.','GPT', '1', now(), now(), '1', NULL, '1', '0'),
('SEO GPT', 'An advanced tool to analyze your input and strategically inject keywords and metadata, enhancing your article discoverability.','Find relevant keywords in the text','GPT', '1', now(), now(), '1', NULL, '1', '0'),
('DALL-E GPT', 'An innovative tool transforms your textual input into stunning visual narratives.','Give me an image','DALL-E', '1', now(), now(), '1', NULL, '1', '0');


-- query to remove security menu access

DELETE FROM ab_permission_view_role 
WHERE permission_view_id IN (
    SELECT id 
    FROM ab_permission_view
    WHERE view_menu_id = (
        SELECT id 
        FROM ab_view_menu 
        WHERE name = 'Security' 
        LIMIT 1
    )
    LIMIT 1
);

-- query to add column in workflow_type
ALTER TABLE airflow_workflow ADD COLUMN workflow_type TEXT DEFAULT NULL;

-- query to add column in airflow_gpt_types
ALTER TABLE airflow_gpt_types ADD COLUMN file TEXT DEFAULT NULL;
ALTER TABLE airflow_gpt_types ADD COLUMN assistant_id TEXT DEFAULT NULL;

ALTER TABLE airflow_chat_details ADD COLUMN thread_id TEXT DEFAULT NULL;

ALTER TABLE airflow_gpt_types ADD COLUMN is_web_scrape smallint NOT NULL DEFAULT '0';

ALTER TABLE ab_role ADD COLUMN is_superadmin smallint NOT NULL DEFAULT '0';

ALTER TABLE ab_user ADD COLUMN user_limit int NOT NULL DEFAULT '0';
ALTER TABLE ab_user ADD COLUMN deleted smallint NOT NULL DEFAULT '0';
ALTER TABLE ab_user ADD COLUMN record_status smallint NOT NULL DEFAULT '1';

ALTER TABLE ab_user DROP CONSTRAINT ab_user_username_uq;
ALTER TABLE ab_user DROP CONSTRAINT ab_user_email_uq;
DROP INDEX IF EXISTS idx_ab_user_username;

DROP TABLE IF EXISTS "user_workflow_access";
CREATE TABLE "user_workflow_access" (
  "id" serial NOT NULL,
  PRIMARY KEY ("id"),
  "workflow_id" integer NOT NULL,
  "user_id" integer NOT NULL,
  "is_enabled" smallint NOT NULL DEFAULT '0',
  "created_by_id" integer NOT NULL,
  "updated_by_id" integer NULL,
  "created_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
  "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,  
  "deleted" integer NOT NULL DEFAULT '0',
  "record_status" integer NOT NULL DEFAULT '1'
);
ALTER TABLE ONLY "user_workflow_access" ADD CONSTRAINT "user_workflow_access_fk1" FOREIGN KEY (user_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "user_workflow_access" ADD CONSTRAINT "user_workflow_access_fk2" FOREIGN KEY (created_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "user_workflow_access" ADD CONSTRAINT "user_workflow_access_fk3" FOREIGN KEY (updated_by_id) REFERENCES ab_user(id) NOT DEFERRABLE;
ALTER TABLE ONLY "user_workflow_access" ADD CONSTRAINT "user_workflow_access_fk4" FOREIGN KEY (workflow_id) REFERENCES airflow_workflow(id) NOT DEFERRABLE;