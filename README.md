# Flask API for csv extraction
A Flask API that accepts user queries via JSON payload, extract content from [games_description.csv](games_description.csv) file and generate response using OpenAI GPT4o model.

## Instructions for project

### Local set up
1. create a .env file with the following api key(s):
```
openai-api-key=[you openai api key]
```
2. Build Docker container by running:
```
docker build -t gamesapi .
```
3. Run Docker container locally:
```
docker run -p 6000:6000 gamesapi
```
### Local testing 
I used a `.rest` file to test the API calls. To do this with the [test.rest](test.rest) file, download Rest Client by HuaChao Mao to run the `.rest` file, then click `send request` on any of the requests to test the API.

### CI/CD process
This project includes a [CI/CD pipeline](.github/workflows/ci-cd.yml) powered by GitHub Actions. The pipeline automates building, testing, and deploying the Docker image to DockerHub, ensuring that the latest version of the API is always production-ready.

#### **Prerequisites**
To enable CI/CD, ensure the following has been configured in GitHub Secrets (I have already configured using my credentials for Docker and the OpenAI API key provided):

**GitHub Secrets:**
- OPENAI_API_KEY: API key for OpenAI, required for calling GPT4o model for API usage
- DOCKER_USERNAME: DockerHub username, required to push Docker image to DockerHub
- DOCKER_PASSWORD: DockerHub password, used for logging into DockerHub to push images
  
#### **Trigger Conditions**
The pipeline is triggered on any push to the main branch or any pull request targetting the main branch

#### **Pipeline Stages**
**1) Checkout code:** 

Pipeline begins by pulling the latest code from repository.

**2) Set up python:** 

Sets up python 3.8 on environment to install dependencies and run test.

**3) Install Dependencies:** 

Installs all required dependencies listed in [requirements.txt](requirements.txt).

**4) Set up .env file for CI/CD:** 

Configure a .env file with API keys for testing. OPENAI_API_KEY is securely retrieved from GitHub Secrets and appended to .env file.

**5) Build Docker image:** 

Build docker image for repository for testing and deployment.

**6) Run Docker container:** 

Starts a Docker container from newly built image, mapping port 6000 of container to port 6000 of host.

**7) View Docker Logs:** 

Allows us to gather insights of erros or failures during testing from printed logs.

**8) Wait for API to be ready:** 

Waits up to 60 seconds for API (flask) to be ready to accept requests, done by periodically sending requests to API until it responds successfully. This waiting time is important as if the API is not ready to accept requests, we will fail the test (tests cannot run at all).

**9) Run Tests:** 

Runs API test with pytest using [test_api.py](test_api.py). Point container's endpoint to http://127.0.0.1:6000.

**10) Stop Docker container:** 

When tests are done, stop Docker container.

**11) Remove Docker container:** 

Remove Docker container to free up resaources and ensure clean environment for subsequent runs.

**12) Login to DockerHub (only executes if all previous steps are successful):** 

Logs in into DockerHub using credentials stored in GitHub Secrets (DOCKER_USERNAME and DOCKER_PASSWORD).

**13) Push Docker Image to DockerHub (Only executes if all previous steps are successful):** 

Push Docker image tagged as latest to DockerHub, making image available for deployment or further use (with latest updates).


### Cloud deployment

With every run of the CI/CD process updating the Docker image in DockerHub after all tests have run successfully, the Docker image will always be updated with the latest changes. To deploy the containerized application to AWS, follow the following steps:

#### Prerequisites
**1. DockerHub:** Ensure the Docker image is available on DockerHub and tagged as latest. The CI/CD pipeline should already handle pushing the latest image automatically.
**2. AWS account:** Access to the AWS Management Console and permissions to manage ECS, IAM roles, and security groups.

#### Step by step deployment
1) Create an ECS cluster
   - Go to the [ECS Console](https://us-east-2.signin.aws.amazon.com/oauth?client_id=arn%3Aaws%3Asignin%3A%3A%3Aconsole%2Fecs&code_challenge=fI1v0TFGTjotxDuR-tZMWngHkeR6OkhrVntSAkPa14I&code_challenge_method=SHA-256&response_type=code&redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fecs%3FhashArgs%3D%2523%26isauthcode%3Dtrue%26oauthStart%3D1731135305079%26state%3DhashArgsFromTB_us-east-2_3d356fb352cd03e3)
   - Click on **Create Cluster**
   - Choose **Networking only** and click **Next Step**
   - Name the cluster (I will name it as games-api-cluster) and click **Create**
2) Define a Task Definition
   - In the ECS console, go to **Task Definitions** and click **Create new Task Definition**.
   - Select **Fargate** as the launch type, then click **Next step**.
   - Configure the following settings:
     * **Task Definition Name:** Enter a name (I would name as games-api-task).
     * **Task Role:** Leave as None unless you have a specific IAM role.
     * **Network Mode:** Select awsvpc (required for Fargate).
    - Under Container Definitions, click **Add container**:
      * **Container Name:** Name it (I would name it games-api-container).
      * **Image:** Enter the Docker image path from DockerHub, i.e ajiayidebug/gamesapi:latest. This will pull the latest image version automatically.
      * **Port Mappings:** Enter 6000
    - Set **Task Memory** and **CPU** as required.
    - Click **Create** to save the task definition.
3) Create a service to run the task
   - In the ECS console, go to **Clusters**, select your cluster, and click **Create** under **Services**.
   - Configure the service:
     * **Launch Type:** Select **Fargate**.
     * **Task Definition:** Choose the task definition you created.
     * **Service Name:** Enter a name (I would choose games-api-service).
     * **Number of Tasks:** Set to 1 (Can scale later if needed).
    - Under **VPC** and **Security Groups**:
      * **VPC:** Select an existing VPC.
      * **Subnets:** Select the appropriate subnets within the VPC.
      * **Security Group:** Create or select a security group that allows inbound traffic on port 6000.
    - **Auto-assign Public IP:** Enable this for public access.
    - Click **Next step**, review your settings, and click **Create Service**.
4) Set Up a Load Balancer for Public Access (optional but to prevent IP address from changing everytime session ends) 
   - In the **EC2 Console**, go to **Load Balancers** and create an **Application Load Balancer**.
   - **Listeners**: Add a listener on port 80.
   - **Target Group**: Create a target group for your ECS service.
   - Attach your ECS service to this load balancer.
5) Configure Automatic Image Updates and Redeployment
   - **Create an EventBridge Rule** to detect Docker image updates on DockerHub and trigger a deployment in ECS.
   - **Set Up AWS CodePipeline:**
     * Create a pipeline that polls DockerHub for changes and redeploys the ECS service whenever a new image is detected.
     * In CodePipeline, set up:
       - **Source Stage:** Configure polling on DockerHub or an ECR repository.
       - **Deploy Stage:** Use ECS as the deploy provider, pointing to your ECS cluster and service.
   - This setup will ensure the ECS service automatically redeploys whenever a new Docker image is pushed to DockerHub (e.g., with each successful CI/CD run).
     
#### Testing API on cloud service
Once the service is up and running, find its public IP or DNS (load balancer). You should be able to access the Flask API endpoint at http://<public-ip>:6000 or through load balancer's DNS, which will listen on port 80 and forward to port 6000 of the ECS task.

### Cloud architecture

<img width="1071" alt="Screenshot 2024-11-09 at 5 30 51 PM" src="https://github.com/user-attachments/assets/97a9adb0-6584-4c75-b5f9-9d9702b19b48">


#### Components
**Client**
- Represents the end-user accessing the Flask API via HTTP requests over the internet.

**Internet**
- Provides the pathway for HTTP/HTTPS communication between the client and the AWS resources.

**Virtual Private Cloud (VPC)**
- The isolated network environment in AWS that houses both public and private subnets.
- Ensures secure communication between the API, Load Balancer, and external clients.

**Public Subnet**
- Application Load Balancer (ALB):
  * Routes incoming HTTP/HTTPS traffic to the ECS service in the private subnet.
	* Port Configuration:
    - Listens on port 80 for HTTP traffic.
    - Listens on port 443 for HTTPS traffic (secure).
	* ALB Security Group:
    - Allows inbound traffic on ports 80 (HTTP) and 443 (HTTPS) from any source.
    - Ensures that only permitted traffic can access the load balancer.

**Private Subnet**
- ECS Cluster:
  * Hosts the Fargate task that runs the Flask API container.
- ECS Security Group:
  * Configured to allow inbound traffic only from the ALB’s security group on port 6000 (the port where the Flask API listens).
- Task Definition:
  * Specifies the container configuration, including:
    - Docker image: ajiayidebug/gamesapi:latest from DockerHub, kept up-to-date through CI/CD.
    - Resource limits and networking details.
    - Port mapping: Maps port 80 from the load balancer to port 6000 on the ECS container.

**DockerHub**
- Stores the Docker image ajiayidebug/gamesapi:latest.
- Updated automatically with each successful CI/CD pipeline run, ensuring the latest application changes are deployed.
**EventBridge**
- Monitors DockerHub for any updates to the Docker image. When a new image is pushed, it triggers ECS to pull the updated image and redeploy the service automatically.

#### Dataflow
1. **Client to ALB**: The client sends an HTTP/HTTPS request to the Application Load Balancer (ALB) on port 80 (HTTP) or port 443 (HTTPS).
2. **ALB to ECS Cluster**: The ALB forwards the HTTP request to the ECS service running in the private subnet on port 6000.
3. **ECS Cluster Response**: The ECS Fargate task processes the request and sends a response back to the ALB.
4. **ALB to Client**: The ALB forwards the HTTP response from the ECS service back to the client.

This architecture ensures that the API is securely accessible over the internet through an Application Load Balancer, which manages incoming traffic via HTTP and HTTPS. The backend containers running the API are isolated within a private subnet, providing an additional layer of security by restricting direct internet access. Furthermore, when the CI/CD pipeline automatically pushes the latest Docker image to DockerHub after a successful run, AWS EventBridge monitors DockerHub for these updates and triggers an update in ECS to pull the new image, ensuring that the deployed service always runs the latest version of the API. This setup reduces manual redeployment efforts and improves update consistency across environments.
## Overview of solution

This solution is a Flask API that utilizes OpenAI’s GPT model to generate responses from a games-related dataset stored as a CSV file. The API supports two main types of queries: specific data row retrieval based on keyword matching and metadata queries about each column.

### Solution Components
1. Flask API [main.py](backend/main.py)
   - The Flask API serves as the main interface for user interactions, providing endpoints to handle queries and manage conversational context.
   - **Endpoints**:
     * /query: Accepts POST requests with a JSON payload. The endpoint determines if the query is about specific data rows or column metadata and routes it accordingly.
     * /reset: Clears the session conversation history, allowing a fresh start for user interactions.
   - **Error Handling**: Includes validation for invalid requests (e.g., non-JSON requests or empty queries).
   - **Environment Setup**: Loads configuration from a .env file, including SECRET_KEY. If not set, it generates one and stores it in .env for secure session handling.
2. Data Retrieval and Metadata Generation [data.py](backend/data.py)
   - **Row-based Queries**: The retrieve_relevant_rows function reads the CSV file and filters rows based on keywords generated by GPT-4o to ensure relevance.
   - **Metadata CSV Generation**: The data_info_col function processes the games CSV file to generate summaries using GPT4o for each column. This metadata, stored in a CSV file (column_summary_info.csv), allows efficient handling of column-based queries.
   - **Context Generation from Metadata**: The generate_context_from_csv function formats column summaries from the metadata CSV, creating a context string for column-based queries.
3. GPT based functionalities [gpt.py](backend/gpt.py)
   - This script integrates GPT-4o for:
     * **Keyword Generation**: Converts user queries into a set of keywords, facilitating more accurate row matching.
     * **Column Summarization**: Creates a concise summary of each column, used in the metadata CSV to support column-based queries.
   - This functionality enables the API to match user intent with the relevant data in the dataset, enhancing accuracy for both row and column-based queries.
4.  Environment Setup and Logging [main.py](backend/main.py)
   - **Environment Management**: The .env file stores sensitive configuration variables, such as the SECRET_KEY, which secures session handling.
   - **Logging**: Configured to capture important runtime information, which aids in debugging and monitoring API behavior.

### Solution Workflow
#### **When the Flask API starts**
- **Data Loading**: The games CSV file is loaded, and if not already created, the metadata CSV is generated.
- **Metadata Generation**: Each column in the CSV is summarized using GPT-4, with the summary stored in column_summary_info.csv.
#### **Handling a Query**
- **Query Parsing**: Determines if the query is about specific data rows or column metadata.
- **Row-based Queries**: Keywords are generated from the query, and relevant rows are retrieved based on these keywords.
- **Column-based Queries**: Metadata CSV summaries provide context for column queries, allowing GPT-4o to generate responses based on column descriptions.
#### **Chat history and Context Management**
- **Session Memory**: The system retains conversational context between interactions, helping GPT-4o provide coherent, context-aware responses.
- **Context Length Control**: Chat history is trimmed to prevent issues with token limits in GPT-4, keeping the context length manageable.
#### **CI/CD and Potential Cloud Deployment**
- **Automated Updates**: The CI/CD pipeline automatically builds and pushes Docker images to DockerHub upon successful tests. AWS EventBridge can monitor DockerHub for image updates, triggering ECS to pull the new image, ensuring the latest version is always deployed.

### API Documentation

#### Endpoints

| **Endpoint**           | **Method** | **Description**                                     | **Request Example**                                                                                                                                                                      | **Expected Response**                                                                                                                                                                                                                                   |
|------------------------|------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `/`                    | `GET`      | Checks if the API is running                        | **Request:** <br> `GET http://127.0.0.1:6000/`                                                                                                                                            | **Response (200):** <br> `{ "message": "You have successfully called the base API!" }`                                                                                                                                                                 |
| `/query`               | `POST`     | Sends a query for row or column-based (metadata) retrieval with chat history for context | **Headers:** <br> `{ "Content-Type": "application/json" }` <br> **Request:** <br> ``` POST http://127.0.0.1:6000/query { "query": "What is a game related to Monkeys?" } ```               | **Response (200):** <br> `{ "response": "Response from the GPT-4 model based on the query and context." }` <br> **Error - Empty Query (400):** <br> `{ "error": "Query field is required and cannot be empty." }` <br> **Error - Non-String Query (400):** <br> `{ "error": "Query must be a string." }` <br> **Error - Invalid JSON (400):** <br> `{ "error": "Request must be in JSON format." }` <br> **Error - Internal Error (500):** <br> `{ "error": "An internal error occurred. Please try again later." }` |
| `/reset`               | `POST`     | Resets the session conversation history             | **Headers:** <br> `{ "Content-Type": "application/json" }` <br> **Request:** <br> `POST http://127.0.0.1:6000/reset`                                                                      | **Response (200):** <br> `{ "message": "Conversation reset." }`                                                                                                                                                                                       |
| Any invalid endpoint   | `Any`      | Returns 404 if the endpoint is not found            | **Request:** <br> `POST http://127.0.0.1:6000/nonexistent`                                                                                                                                | **Error (404):** <br> `{ "error": "Endpoint not found" }`                                                                                                                                                                                             |
| Any invalid method     | `Any`      | Returns 405 if the method is not allowed for the endpoint | **Request:** <br> `GET http://127.0.0.1:6000/query` (assuming `GET` is not allowed)                                                                                                       | **Error (405):** <br> `{ "error": "Method not allowed" }`                                                                                                                                                                                             |

##### Usage Notes:
- A [test file](test_api.py) has been created with these api call tests in mind which will automatically be implemented when you run the CI/CD process or manually implemented by running the following code in the terminal: `pytest test_api.py`
- Use `curl`, Postman, or `.rest` files (download Rest Client by HuaChao Mao to run `.rest` files) in VS Code to test these API calls.
- For `/query`, ensure the request body is in JSON format and that `"query"` is a non-empty string.

