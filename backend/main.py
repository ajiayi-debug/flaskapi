import os
from flask import Flask, request, jsonify, session
from dotenv import load_dotenv
from pathlib import Path
import secrets
import pandas as pd
from data import *
from gpt import *

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

# File path for the summary CSV
SUMMARY_CSV = "column_summary_info.csv"

# Generate or load the summary CSV once
def load_summary_data():
    if not os.path.exists(SUMMARY_CSV):
        data_info_col("games_description.csv", output_csv=SUMMARY_CSV)
    return pd.read_csv(SUMMARY_CSV).to_dict(orient="records")

# Load the summary data once when the app starts
summary_data = load_summary_data()

# POST request for RAG of rows or context-based question answering for column-based queries
#Chat history is ALWAYS saved for instances of switching between row based and column based queries
@app.route('/query', methods=['POST'])
def querykeywordmatching():
    user_input = request.json.get('query', '')

    # Initialize session memory if it doesn't exist
    if 'conversation' not in session:
        session['conversation'] = []

    # Retrieve relevant data from CSV for row-based retrieval
    relevant_data = retrieve_relevant_rows(user_input, 'games_description.csv')

    # Retrieve conversation history from session
    conversation_history = session['conversation']
    
    # Determine if the query is asking for metadata (column-wise) or row-based data
    row_col = query_type(user_input,conversation_history)        
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

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('conversation', None)
    return jsonify({"message": "Conversation reset."})

if __name__ == '__main__':
    app.run(debug=True)