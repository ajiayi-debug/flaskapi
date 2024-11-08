import os
import secrets
from flask import Flask, request, jsonify, session
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from data import *
from gpt import *
import logging
from openai import OpenAIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load any existing .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Check if SECRET_KEY exists in the .env file
secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    # Generate a new secret key if it doesn't exist
    secret_key = secrets.token_hex(16)
    print("Generated a new secret key:", secret_key)

    # Save the new secret key to the .env file
    with open(env_path, 'a') as f:
        f.write(f'\nSECRET_KEY={secret_key}')
    
    print("Secret key saved to .env file.")
else:
    print("Using existing secret key.")

# Initialize Flask app with secret key
app = Flask(__name__)
app.secret_key = secret_key

# File path for the metadata CSV
SUMMARY_CSV = "column_summary_info.csv"

# Generate or load the metadata CSV once
def load_summary_data():
    if not os.path.exists(SUMMARY_CSV):
        data_info_col("games_description.csv", output_csv=SUMMARY_CSV)
    return pd.read_csv(SUMMARY_CSV).to_dict(orient="records")

# Load the meta data once when the app starts
summary_data = load_summary_data()

@app.route("/")
def home():
    return "You have successfully called the base API! "

# POST request for RAG of rows as context (plus chat history) for question answering or metadata as context (plus chat history) for column based queries
@app.route('/query', methods=['POST'])
def querykeywordmatching():
    # Ensure request is JSON
    if not request.is_json:
        logger.warning("Request must be in JSON format.")
        return jsonify({"error": "Request must be in JSON format"}), 400

    data = request.get_json()
    user_input = data.get('query', None)

    # Handle empty or non-string query
    if not isinstance(user_input, str):
        return jsonify({"error": "Query must be a string."}), 400
    if user_input is None or user_input.strip() == "":
        return jsonify({"error": "Query field is required and cannot be empty."}), 400
    
    user_input = user_input.strip()

    try:
        # Initialize session memory if it doesn't exist
        if 'conversation' not in session:
            session['conversation'] = []

        # Retrieve relevant data from CSV for row-based retrieval
        relevant_data = retrieve_relevant_rows(user_input, 'games_description.csv')

        # Retrieve conversation history from session
        conversation_history = session['conversation']
        
        # Determine if the query is asking for metadata (column-wise) or row-based data
        row_col = query_type(user_input, conversation_history)
        
        if row_col == 'Metadata':
            # Generate response based on column-wise (metadata) information
            answer = generator_rag_colbase(conversation_history, user_input, summary_data)                    
        else:
            # Generate response based on row-wise retrieval
            answer = generator_rag_rowbase(conversation_history, user_input, relevant_data)  

        # Update conversation history in session
        conversation_history.append({"user": user_input, "assistant": answer})
        session['conversation'] = conversation_history

        return jsonify({"response": answer})

    except KeyError as e:
        logger.error(f"Missing field: {e}")
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except ValueError as e:
        logger.error(f"Invalid value: {e}")
        return jsonify({"error": str(e)}), 400
    except OpenAIError as e:
        logger.error(f"Query API service error: {e}")
        return jsonify({"error": "Failed to connect to query API service"}), 502
    except TimeoutError:
        logger.error("Query API service timed out.")
        return jsonify({"error": "The query API service timed out. Please try again later."}), 504
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('conversation', None)
    return jsonify({"message": "Conversation reset."})

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000)