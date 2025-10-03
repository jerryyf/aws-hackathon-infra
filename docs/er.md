erDiagram
 direction TB
 User {
  uuid id PK ""  
  string email UK ""  
  string username UK ""  
  string password_hash  ""  
  string first_name  ""  
  string last_name  ""  
  string profile_image_url  ""  
  string preferred_language  ""  
  string theme_preference  ""  
  boolean email_verified  ""  
  timestamp created_at  ""  
  timestamp updated_at  ""  
  timestamp last_login  ""  
  string cognito_user_id UK ""  
 }

 UserRole {
  uuid id PK ""  
  uuid user_id FK ""  
  uuid role_id FK ""  
  timestamp assigned_at  ""  
  uuid assigned_by FK ""  
 }

 ProjectMember {
  uuid id PK ""  
  uuid project_id FK ""  
  uuid user_id FK ""   
  %% User id of the user who added the user
  uuid added_by_id FK ""  
  timestamp joined_at  ""  
 }

 Notification {
  uuid id PK ""  
  uuid user_id FK ""  
  string type  ""  
  string title  ""  
  text message  ""  
  boolean read  ""  
  json metadata  ""  
  timestamp created_at  ""  
  timestamp read_at  ""  
 }

 AuditLog {
  uuid id PK ""  
  uuid user_id FK ""  
  string action  ""  
  string resource_type  ""  
  uuid resource_id  ""  
  json previous_state  ""  
  json new_state  ""  
  string ip_address  ""  
  string user_agent  ""  
  timestamp created_at  ""  
 }

 Role {
  uuid id PK ""  
  string name UK ""  
  string description  ""  
  timestamp created_at  ""  
  timestamp updated_at  ""  
 }

 Permission {
  uuid id PK ""  
  uuid role_id FK ""  
  string resource  ""  
  string action  ""  
  timestamp created_at  ""  
 }

 Organization {
  uuid id PK ""  
  string name  ""  
  string domain  ""  
  json settings  ""  
  timestamp created_at  ""  
  timestamp updated_at  ""  
 }

 Project {
  uuid id PK ""  
  string name  ""  
  string description  ""  
  string status  ""  
  decimal value  ""  
  date deadline  ""  
  integer progress_percentage  ""  
  uuid created_by FK ""  
  uuid completed_by FK ""
  timestamp created_at  ""  
  timestamp updated_at  ""  
  timestamp completed_at  ""   
  json metadata  ""  
 }

 ProjectDocument {
  uuid id PK ""  
  uuid project_id FK ""  
  string file_name  ""  
  string file_path  ""  
  string file_type  ""  
  bigint file_size  ""  
  string location  "" 
  uuid uploaded_by FK ""  
  timestamp uploaded_at  ""  
  json metadata  ""  
 }

 KnowledgeBase {
  uuid id PK ""  
  string name  ""  
  string description  ""  
  string scope  ""  
  uuid project_id FK ""  
  integer document_count  ""  
  uuid created_by FK ""  
  timestamp created_at  ""  
  timestamp updated_at  ""  
  string vector_store_id  ""  
 }

 Artifact {
  uuid id PK ""  
  uuid project_id FK ""  
  string name  "" 
  %% tuep - <worddoc | pdf | ppt | excel> 
  string type  ""  
  %% categoty-  < document | q_and_a | excel >,
  string category  ""  
  string status  ""   
  uuid created_by FK ""  
  uuid approved_by FK ""  
  timestamp created_at  ""  
  timestamp approved_at  ""  
 }

 WorkflowExecution {
  uuid id PK ""  
  uuid project_id FK ""  
  string status  ""  
        %% User Id, who initiate the workflow
  uuid initiated_by FK ""  
        %% User Id, who is being handle the workflow
  uuid handled_by FK "" 
        %% User Id, who completed the workflow
  uuid completed_by FK "" 
  timestamp started_at  ""  
  timestamp completed_at  "" 
  timestamp last_updated_at  ""   
  json workflow_config  ""  
  json error_log  ""
  text error_message  "" 
  json results  ""  
 }

 KnowledgeBaseDocument {
  uuid id PK ""  
  uuid knowledge_base_id FK ""  
  string file_name  ""  
  string file_path  ""  
  string file_type  ""  
  bigint file_size  ""  
  string s3_bucket  ""  
  string s3_key  ""  
  uuid uploaded_by FK ""  
  timestamp uploaded_at  ""  
  json metadata  ""  
  string vector_ids  ""  
 }

 KnowledgeBasePermission {
  uuid id PK ""  
  uuid knowledge_base_id FK ""  
  uuid user_id FK ""  
  uuid role_id FK ""  
  string permission_type  ""  
  timestamp granted_at  ""  
 }

 ArtifactVersion {
  uuid id PK ""  
  uuid artifact_id FK ""  
  integer version_number  ""  
  json content  ""  
  %% Optional
  stirng location ""
  uuid created_by FK ""  
  timestamp created_at  ""   
 }

 AgentConfiguration {
  uuid id PK ""  
  string agent_type UK ""  
  string model_name  ""  
  float temperature  ""  
  integer max_tokens  ""  
  json system_prompt  ""  
  json additional_parameters  ""  
  boolean enabled  ""  
  timestamp created_at  ""  
  timestamp updated_at  ""  
  uuid updated_by FK ""  
 }

 AgentTask {
  uuid id PK ""  
  uuid workflow_execution_id FK ""  
        %% User Id, who initiate the agent task
  uuid initiated_by FK ""  
        %% User Id, who is being handle the agent task
  uuid handled_by FK "" 
        %% User Id, who completed the agent task
  uuid completed_by FK "" 
        %% Name of the agent who process this task
  string agent  ""  
  string status  ""  
  integer sequence_order  ""  
  json input_data  ""  
  json output_data  ""  
  json task_config  ""
  json error_log  ""
  text error_message  ""  
  timestamp started_at  ""  
  timestamp completed_at  ""  
  float execution_time_seconds  ""   
 }

 Integration {
  uuid id PK ""  
  string type UK ""  
  string name  ""  
  json configuration  ""  
  boolean enabled  ""  
  uuid created_by FK ""  
  timestamp created_at  ""  
  timestamp updated_at  ""  
 }

 IntegrationLog {
  uuid id PK ""  
  uuid integration_id FK ""  
  string action  ""  
  string status  ""  
  json request_data  ""  
  json response_data  ""  
  text error_message  ""  
  timestamp created_at  ""  
 }

 BidStatistics {
  uuid id PK ""  
  date period_start  ""  
  date period_end  ""  
  integer submitted_bids  ""  
  integer won_bids  ""  
  decimal total_value  ""  
  decimal won_value  ""  
  float success_rate  ""  
  integer active_rfps  ""  
  json detailed_metrics  ""  
  timestamp calculated_at  ""  
 }

 SubmissionRecord {
  uuid id PK ""  
  uuid project_id FK ""  
  uuid artifact_id FK ""  
  string portal_name  ""  
  string submission_id  ""  
  string status  ""  
  uuid submitted_by FK ""  
  timestamp submitted_at  ""  
  json submission_metadata  ""  
 }

 Untitled-Entity {

 }

 User||--o{UserRole:"has"
 User||--o{ProjectMember:"member of"
 User||--o{Notification:"receives"
 User||--o{AuditLog:"performs"
 Role||--o{UserRole:"assigned"
 Role||--o{Permission:"has"
 Project||--o{ProjectMember:"has"
 Project||--o{ProjectDocument:"contains"
 Project||--o{KnowledgeBase:"uses local"
 Project||--o{Artifact:"produces"
 Project||--o{WorkflowExecution:"triggers"
 KnowledgeBase||--o{KnowledgeBaseDocument:"contains"
 KnowledgeBase||--o{KnowledgeBasePermission:"has access"
 Artifact||--o{ArtifactVersion:"has versions"
 WorkflowExecution||--o{AgentTask:"contains"
 Integration||--o{IntegrationLog:"logs"
 Project||--o{SubmissionRecord:"submitted via"
 Artifact||--o{SubmissionRecord:"submitted as"
 User||--o{SubmissionRecord:"submits"

 