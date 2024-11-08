# Flask API for csv extraction
A Flask API that accepts user queries via JSON payload, extract content from [games_description.csv](games_description.csv) file and generate response using OpenAI GPT4o model.

## Overview of solution


## Instructions for project

### Local set up
create a .env file with the following api key(s):
```
openai-api-key=[you openai api key]
```
To start docker container locally, run
```
docker build -t gamesapi .
```
to build the container. Then run
```
docker run -p 6000:6000 gamesapi
```
to run the container locally.

To test api locally, run the following command in your terminal after flask loads and the tqdm loading bar has completed it's process.
```
pytest test_api.py
```
