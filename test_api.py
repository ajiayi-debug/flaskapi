import requests

BASE_URL = "http://127.0.0.1:5001"

#test row retrieval query
def test_row_query_endpoint():
    response = requests.post(f"{BASE_URL}/query", json={"query": "What is a game related to Monkeys"})
    assert response.status_code == 200
    assert "response" in response.json()  # Add more specific assertions based on your API's expected response
#test follow up qns
def test_memory_follow_up():
    response = requests.post(f"{BASE_URL}/query", json={"query": "Can you tell me more about it?"})
    assert response.status_code == 200
    assert "response" in response.json()
#test metadata query (col-based queries)
def test_col_query_endpoint():
    response = requests.post(f"{BASE_URL}/query", json={"query": "How many games do you know about?"})
    assert response.status_code == 200
    assert "response" in response.json()
#test reset conversation 
def test_reset_memory():
    response = requests.post(f"{BASE_URL}/reset")
    assert response.status_code == 200
    assert response.json()["message"] == "Conversation reset."