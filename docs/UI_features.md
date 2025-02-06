# Intel® AI for Enterprise RAG UI

## Login

Upon visiting https://erag.com, the following page will be displayed. By clicking **Login** button you will be redirected to Keycloak login page where you will be asked to enter your credentials.

![Login page screenshot](../images/ui/login.png)

> [!NOTE]
> To access **Intel® AI for Enterprise RAG UI**, you have to use one time credentials for admin (`KEYCLOAK_ERAG_ADMIN_USERNAME` and `KEYCLOAK_ERAG_ADMIN_PASSWORD`) or user (`KEYCLOAK_ERAG_USER_USERNAME` and `KEYCLOAK_ERAG_USER_PASSWORD`) generated in `default_credentials.txt` file inside `deployment` folder.
>
> After first login you will be requested to change the default password. Your new password must be at least 12 characters long, include at least 1 digit, 1 uppercase letter, 1 lowercase letter and 1 special character. It also must be different from the last 5 passwords you have used.

## Chat

Once logged in, you will be redirected to the chat page. In the text input field, enter your question and click on circle button with arrow to send it.

After sending your question, you will see pulsing dot next to the atom icon. It indicates waiting for chat response. You can interrupt waiting for the response by clicking stop button placed in the bottom right corner of text input field.

When you receive a response from the chat, verify whether it responds correctly to your question.

![Screenshot of chat page - displaying welcome message and text input](../images/ui/chat_initial.png)

![Screenshot of chat page - waiting for response from chat](../images/ui/chat_waiting.png)

In the top right corner of the page, if you logged in as an admin, you will see three interactive elements - **Admin Panel** button, **Light/Dark Mode** switch and **Logout** button. If you logged in as a regular user, **Admin Panel** button won't be visible for you.

## Admin Panel

In the Admin Panel you can access three views using the following tabs: [Control Plane](#control-plane), [Data Ingestion](#data-ingestion) and [Telemetry & Authentication](#telemetry--authentication).

### Control Plane

![Screenshot of Control Plane view with a graph of pipeline services](../images/ui/control_plane_initial.png)

The **Control Plane** view shown above allows the user to see all the components of the currently deployed pipeline as a graph. Each service can be selected from the graph to get further information on the configuration settings of each service. In some components it is also possible to edit service arguments for the services.

For example, when you click on the LLM service, as shown in the screenshot below, the right pane is populated with the LLM parameters that can be modified like `max_new_tokens`, `temperature` etc. To confirm parameters changes, click **Confirm Change** button.

![Screenshot of Control Plane view presenting a graph of pipeline services. LLM service selected.](../images/ui/control_plane_llm_selected.png)

![Screenshot of Control Plane view presenting a graph of pipeline services. LLM max_new_tokens parameter value changed to 2048, waiting to be confirmed.](../images/ui/control_plane_confirm.png)


### Data Ingestion

The Admin Panel also has the interface for Data Ingestion as shown below:

![Screenshot of Data Ingestion view presenting two empty tables for ingested files and links](../images/ui/data_ingestion_initial.png)

To upload new data, click on **Upload** button. The following dialog will be displayed:

![Screenshot of Data Ingestion view presenting upload dialog](../images/ui/data_ingestion_upload.png)

Any file belonging to the supported file format shown in the screenshot or a link to a website can be added to the knowledge base via this interface.

### Telemetry & Authentication

This tab contains links to the other services - Grafana Dashboard and Keycloak Admin Panel. Clicking on one of the visible blocks will open a new tab in your browser with an URL leading to interface of the selected service.

![Screenshot of Telemetry & Authentication view presenting links to the other services - Grafana Dashboard and Keycloak Admin Panel](../images/ui/telemetry_authentication.png)
