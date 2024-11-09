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

4. Test the API locally by running the following command in your terminal after Flask server has loaded:
```
pytest test_api.py
```


### CI/CD process
This project includes a [CI/CD pipeline](.github/workflows/ci-cd.yml) powered by GitHub Actions. The pipeline automates building, testing, and deploying the Docker image to DockerHub, ensuring that the latest version of the API is always production-ready.

#### **Prerequisites**
To enable CI/CD, configure the following GitHub Secrets:
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

## Overview of solution

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

