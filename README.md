# Flask API for csv extraction
A Flask API that accepts user queries via JSON payload, extract content from [games_description.csv](games_description.csv) file and generate response using OpenAI GPT4o model.

## Overview of solution


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

### Cloud deployment

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

Push Docker image tagged as latest to DockerHub, making iomage available for deployment or further use (with latest updates).
