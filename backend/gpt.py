from openai import OpenAI
from dotenv import load_dotenv
import os
from data import *
load_dotenv()

#initialize openai client
client = OpenAI(
    api_key=os.environ.get("openai-api-key"),
)

#Maximium history length such that out context length does not exceed token length
MAX_HISTORY_LENGTH = 10  # Limit for recent exchanges in full to prevent exceeding token length

#summarize older convos to retain key info and to keep exchanges longer based on max history length set in script
def summarize_conversation(conversation):
    """Summarize older exchanges into a single line"""
    summary = " ".join([f"{exchange['user']} asked about {exchange['assistant']}." for exchange in conversation[:-MAX_HISTORY_LENGTH]])
    return summary

#gpt 4o function to summarise columns for metadata
def summarise_cols(name,col):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""Based on the column name and content provided, generate a concise and general summary that describes the main purpose of this column in a dataset about game descriptions.

                Column Name: {name}
                Column Content: {col}

                The summary should briefly explain what information this column contains without going into extensive detail."""
            },
        ],
    )
    answer = response.choices[0].message.content
    return answer


#function for row based queries
def generator_rag_rowbase(conversation_history, user_input, relevant_data):
    # Convert retrieved data (rows) to readable text block for gpt 4o to understand context
    context = "\n\n".join([
    f"Game: {row['name']}\n"
    f"Short Description: {row['short_description']}\n"
    f"Long Description: {row['long_description']}\n"
    f"Genres: {row['genres']}\n"
    f"Minimum System Requirement: {row['minimum_system_requirement']}\n"
    f"Recommended System Requirement: {row['recommend_system_requirement']}\n"
    f"Release Date: {row['release_date']}\n"
    f"Developer: {row['developer']}\n"
    f"Publisher: {row['publisher']}\n"
    f"Overall Player Rating: {row['overall_player_rating']}\n"
    f"Number of Reviews from Purchased People: {row['number_of_reviews_from_purchased_people']}\n"
    f"Number of English Reviews: {row['number_of_english_reviews']}\n"
    f"Link: {row['link']}"
    for row in relevant_data
    ])
    #generate a prompt with summarized older exchanges, full recent exchanges AND rows retrieved
    prompt = generate_prompt_row(conversation_history, user_input, context)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"{prompt}"
            },
        ],
    )
    answer = response.choices[0].message.content
    return answer


#Gives context from retrieved rows and history from chat to gpt 4o as a prompt for contextual response
def generate_prompt_row(conversation, user_input, context):
    """
    Generates a prompt with summarized older exchanges and full recent exchanges,
    along with context (row data) and the latest user input.
    """

    # Summarize older exchanges
    summary = summarize_conversation(conversation)

    # Keep only recent exchanges in full detail
    recent_conversation = conversation[-MAX_HISTORY_LENGTH:]

    # Build the prompt
    prompt = f"This is a conversation about video games. Here is some context:\n\n{context}\n\n"
    
    # add summarized history if it exists
    if summary:
        prompt += f"Summary of previous conversation: {summary}\n\n"

    # add recent number of (MAX HISTORY LENGTH) conversation exchanges in full detail
    for exchange in recent_conversation:
        prompt += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n"
    
    # add the latest user input
    prompt += f"User: {user_input}\nAssistant:"
    return prompt

#function for response to col-based queries
def generator_rag_colbase(conversation_history, user_input,csv_summary):

    prompt = generate_prompt_col(conversation_history, user_input,csv_summary)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"{prompt}"
            },
        ],
    )
    answer = response.choices[0].message.content
    return answer


#gives context in terms of meta data, convo history and summarise history for convos that exceed length. 
def generate_prompt_col(conversation, user_input,csv_summary):
    """
    Generates a prompt with summarized older exchanges and full recent exchanges,
    along with context and the latest user input.
    """
    # Format the CSV summary data (meta data) as part of the context
    csv_context = "\n\n".join([
        f"{col_summary['Column Name']}: {col_summary['Description']}: {col_summary['Total Rows']}:"
        for col_summary in csv_summary
    ])


    # Summarize older exchanges
    summary = summarize_conversation(conversation)

    # Keep only recent exchanges in full detail
    recent_conversation = conversation[-MAX_HISTORY_LENGTH:]

    # Build the prompt
    prompt = f"""You are a knowledgeable assistant for a dataset about video games.
    Please respond concisely to the user's question based on the information provided.
    Do not reference this context explicitly unless the user asks for details.
    Here is the dataset context:
    {csv_context}"""
    
    # add summarized history if it exists
    if summary:
        prompt += f"Summary of previous conversation: {summary}\n\n"

    # add recent number of (MAX HISTORY LENGTH) conversation exchanges in full detail
    for exchange in recent_conversation:
        prompt += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n"
    
    # add the latest user input
    prompt += f"User: {user_input}\nAssistant:"
    return prompt

#keyword generator for row based retrieval. 
def generate_keywords(query):
    """
    Creates keywords from query based on the provided prompt and query.

    Parameters:
    - query (str): The user's query.
    Returns:
    - answer (str): The response content generated by GPT-4o.
    """
    system_message = "Generate keywords from the user query to perform keyword matching and retrieve relevant rows."
    user_message = query

    # Generate response using GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]
        )
        # Extract and return the answer content
        answer = response.choices[0].message.content
        return answer
    
    except Exception as e:
        print(f"Error in GPT-4o generation: {e}")
        return "An error occurred while processing the query."

#determine if the query is asking row based or column based questions. Allow us to determine if we retreive rows or look at overall data as meta
def query_type(query, conversation):
    """
    Classifies the query as Metadata or Row-specific using the query and recent conversation context.
    Metadata: For col based queries
    Row-specific: For row based queries
    """
    # Get the previous user query or assistant response as context, if available
    previous_context = conversation[-1]['user'] if conversation else ""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    """You are determining whether the user's query pertains to metadata about the dataset or specific row-based information. Use the last user input or assistant response to help clarify if the query is vague."""
                )
            },
            {
                "role": "user",
                "content": f"""Previous context: "{previous_context}"\n\n
                You are working with a dataset that contains information about video games, including details such as titles, descriptions, genres, system requirements, ratings, reviews, and more.

                Here is a summary of the dataset structure:
                - "Metadata" includes general information about the dataset, such as the total number of games, descriptions of each column, and types of data in each column.
                - "Row-specific" information pertains to specific details about individual games, like information for a particular title or details about a specific game's rating, genre, or release date.

                Determine whether the following query is asking for:
                1. **Metadata** (general dataset information) - Examples include "How many games are in the dataset?", "What columns are in the dataset?", "Describe the types of data available."
                2. **Row-specific** information - Examples include "Tell me about Cyberpunk 2077", "What are the system requirements for Red Dead Redemption 2?", or "Show details for games in the RPG genre."

                Query: "{query}"

                Instructions:
                - If the query asks for general information about the dataset, such as counts, types of columns, or descriptions of column content, classify it as **Metadata**.
                - If the query asks about specific games, individual details, or content that varies per row, classify it as **Row-specific**.
                - Output "Metadata" or "Row-specific" based on the query's intent."""
            },
        ],
    )
    answer = response.choices[0].message.content.strip()
    return answer