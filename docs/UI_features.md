# Intel® AI for Enterprise RAG UI

## Table of Contents

- [Login](#login)
- [Chat](#chat)
- [Admin Panel](#admin-panel)
  - [Control Plane](#control-plane)
  - [Data Ingestion](#data-ingestion)
  - [Telemetry \& Authentication](#telemetry--authentication)

## Login

Upon visiting https://erag.com, you will be redirected to Keycloak login page where you will be asked to enter your credentials.

> [!NOTE]
> To access **Intel® AI for Enterprise RAG UI**, you have to use one time credentials for admin (`KEYCLOAK_ERAG_ADMIN_USERNAME` and `KEYCLOAK_ERAG_ADMIN_PASSWORD`) or user (`KEYCLOAK_ERAG_USER_USERNAME` and `KEYCLOAK_ERAG_USER_PASSWORD`) generated in `default_credentials.txt` file inside `deployment/ansible-logs` folder.
>
> After first login you will be requested to change the default password. Your new password must be at least 12 characters long, include at least 1 digit, 1 uppercase letter, 1 lowercase letter and 1 special character. It also must be different from the last 5 passwords you have used.

## Chat

Once logged in, you will be redirected to the chat page. In the text input field, enter your question and click on circle button with arrow to send it.

After sending your question, you will see pulsing dot next to the atom icon. It indicates waiting for chat response. You can interrupt waiting for the response by clicking stop button placed in the bottom right corner of text input field.

When you receive a response from the chat, verify whether it responds correctly to your question.

![Screenshot of chat page - displaying welcome message and text input](../images/ui/chat_initial.png)

![Screenshot of chat page - waiting for response from chat](../images/ui/chat_waiting.png)

After receiving a message your chat will be saved in Chat History. You can access it by clicking panel icon in the top left corner. Side menu will show up.

![Screenshot of chat page - side panel with Chat History](../images/ui/chat_history_saved.png)

By clicking three dots next to the name of your chat you will see the options to manage your chat. You can rename your chat, export its contents in JSON format and delete it.

![Screenshot of chat page - side panel with Chat History - chat options menu displayed](../images/ui/chat_history_options.png)

In the top right corner of the page, if you logged in as an admin, you will see three interactive elements - **Admin Panel** button, **Light/Dark Mode** switch and **Logout** button. If you logged in as a regular user, **Admin Panel** button won't be visible for you.

## Admin Panel

In the **Admin Panel** you can access three views using the following tabs: [Control Plane](#control-plane), [Data Ingestion](#data-ingestion) and [Telemetry & Authentication](#telemetry--authentication).

### Control Plane

![Screenshot of Control Plane view with a graph of pipeline services](../images/ui/control_plane_initial.png)

The **Control Plane** view shown above allows the user to see all the components of the currently deployed pipeline as a graph. Each service can be selected from the graph to get further information on the configuration settings of each service. In some components it is also possible to edit service arguments for the services.

For example, when you click on the LLM service, as shown in the screenshot below, the right pane is populated with the LLM parameters that can be modified like `max_new_tokens`, `temperature` etc. To confirm parameters changes, click **Confirm Changes** button.

![Screenshot of Control Plane view presenting a graph of pipeline services. LLM service selected.](../images/ui/control_plane_llm_selected.png)

![Screenshot of Control Plane view presenting a graph of pipeline services. LLM max_new_tokens parameter value changed to 512, waiting to be confirmed.](../images/ui/control_plane_confirm.png)

From **Control Plane** view you are also able to change currently used prompt templates by selecting Prompt Template service node from the graph. Edit current prompt templates and click "Change Prompt Template" to update them.

![Screenshot of Control Plane view presenting a graph of pipeline services. Prompt Template service selected.](../images/ui/control_plane_prompt_template.png)

> [!NOTE]
> Prompt Templates cannot be empty and have to contain three placeholders: **{user_prompt}**, **{reranked_docs}** and **{conversation_history}** that can be placed anywhere in both templates once. In case any of these requirements are not met, an error message will be displayed on the screen under text inputs as shown below.

![Screenshot of Control Plane view presenting a graph of pipeline services. Prompt Template textarea inputs in invalid state with error message displayed below.](../images/ui/control_plane_prompt_template_invalid.png)

### Data Ingestion

The Data Ingestion UI provides visibility into synchronization and processing workflows. It is intended for administrative use and supports the following features:

**Synchronization Monitoring**
  - View status of synchronization processes with external storage endpoints (e.g., S3).
  - Identify sync failures or delays.

**File Processing Monitoring**
  - Track processing status of individual files and links (queued, in progress, completed, failed).
  - View and manage the queue of files and links awaiting processing.

**Error Handling**
  - Inspect error messages for failed processing tasks.
  - Manually trigger retries for failed items.

**Performance Metrics**
  - Monitor processing statistics per file/link.
  - View detailed timing breakdowns for each processing step.

This is an example of the Data Ingestion UI:

![Screenshot of Data Ingestion view presenting two empty tables for ingested files and links](../images/ui/data_ingestion_files.png)

Detailed overview of processing time is displayed after clicking the processing time for individual file or link:
![Screenshot of Data Ingestion view with Detailed Overview](../images/ui/data_ingestion_timings.png)

The Data Ingestion UI is designed for lightweight, administrative interactions with data sources and should not be used for uploading or managing large volumes of files.

Recommended workflow for ingesting data:
- Primary data source: External storage endpoints (e.g., S3 compatible sotrage endpoints) should be used as the main interface for data ingestion.
- File operations: Users are encouraged to use their existing tools (e.g., S3 GUI, Windows mounts, CLI tools) to upload, delete, or organize files.
- UI limitations:
  - File uploads via the UI are restricted to the main folder only, making it difficult to preserve complex directory structures.
  - Data manipulation through the UI is limited to admin users, reducing flexibility for users and broader teams.

Configuring external sources is covered in [EDP's README.md](../src/edp/README.md) file.

Nevertheless, you can upload sample data using this UI by click on **Upload** button. The following dialog will be displayed:

![Screenshot of Data Ingestion view presenting upload dialog](../images/ui/data_ingestion_upload.png)

Any file belonging to the supported file format shown in the screenshot or a link to a website can be added to the knowledge base via this interface. Uploading files requires selecting S3 bucket from the select dropdown placed above file input. For links S3 bucket does not have to be selected.

### Telemetry & Authentication

This tab contains links to the other services - Grafana Dashboard and Keycloak Admin Panel. Clicking on one of the visible blocks will open a new tab in your browser with an URL leading to interface of the selected service.

![Screenshot of Telemetry & Authentication view presenting links to the other services - Grafana Dashboard and Keycloak Admin Panel](../images/ui/telemetry_authentication.png)
