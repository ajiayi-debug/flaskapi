import requests

BASE_URL = "http://127.0.0.1:5001"

# Test row retrieval query with a valid question based on row retrieval
def test_row_query_endpoint():
    response = requests.post(f"{BASE_URL}/query", json={"query": "What is a game related to Monkeys"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)  

# Test follow-up question (memory test)
def test_memory_follow_up():
    response = requests.post(f"{BASE_URL}/query", json={"query": "Can you tell me more about it?"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

# Test metadata query (column-based)
def test_col_query_endpoint():
    response = requests.post(f"{BASE_URL}/query", json={"query": "How many games do you know about?"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

# Test resetting conversation
def test_reset_memory():
    response = requests.post(f"{BASE_URL}/reset")
    assert response.status_code == 200
    assert response.json()["message"] == "Conversation reset."

# Test invalid input (empty query)
def test_empty_query():
    response = requests.post(f"{BASE_URL}/query", json={"query": ""})
    assert response.status_code == 400 
    assert "error" in response.json()
    assert response.json()["error"] == "Query field is required and cannot be empty."

# Test invalid input type (non-string query)
def test_non_string_query():
    response = requests.post(f"{BASE_URL}/query", json={"query": 12345})
    assert response.status_code == 400 
    assert "error" in response.json()
    assert response.json()["error"] == "Query must be a string."

# Test special characters in query (to see how the API handles them)
def test_special_characters_query():
    response = requests.post(f"{BASE_URL}/query", json={"query": "@#$%^&*()"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

# Test for long query input (edge case) (row based retrieval)
def test_long_query():
    long_query = "What is the game that involves a long description?" * 100  # Generate a long string
    response = requests.post(f"{BASE_URL}/query", json={"query": long_query})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

# Test query after reset to ensure session has been cleared
def test_query_after_reset():
    # First, reset the session
    reset_response = requests.post(f"{BASE_URL}/reset")
    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "Conversation reset."

    # Now, make a new query to check if session has been cleared
    response = requests.post(f"{BASE_URL}/query", json={"query": "What is a game related to Dinosaurs?"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

# Test for session persistence across multiple queries
def test_session_persistence():
    response1 = requests.post(f"{BASE_URL}/query", json={"query": "Tell me about games related to space."})
    assert response1.status_code == 200
    assert "response" in response1.json()

    response2 = requests.post(f"{BASE_URL}/query", json={"query": "Can you give me more details?"})
    assert response2.status_code == 200
    assert "response" in response2.json()

    # Ensure the second response depends on the first query (based on the session)
    assert response1.json()["response"] != response2.json()["response"]

# Test reset after multiple queries
def test_reset_after_multiple_queries():
    # Make multiple queries
    requests.post(f"{BASE_URL}/query", json={"query": "What is a game related to fantasy?"})
    requests.post(f"{BASE_URL}/query", json={"query": "And what about space games?"})

    # Reset the session
    reset_response = requests.post(f"{BASE_URL}/reset")
    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "Conversation reset."

    # Make a new query and check if it's treated independently
    response = requests.post(f"{BASE_URL}/query", json={"query": "What is a game related to adventure?"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

# Test unexpected endpoints (error handling for non-existing routes)
def test_non_existent_endpoint():
    response = requests.post(f"{BASE_URL}/nonexistent")
    assert response.status_code == 404