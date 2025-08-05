from fastapi.testclient import TestClient
from app.main import app, hash_pass
import base64
import os

client = TestClient(app)

# بيانات تسجيل الدخول (موجودة في قاعدة البيانات تلقائيًا)
EMAIL = "admin@example.com"
PASSWORD = "123"
BASIC_AUTH = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()

headers = {
    "Authorization": f"Basic {BASIC_AUTH}"
}


def test_root_page():
    """
    Test the root endpoint to ensure it returns a 200 status code and
    the response content-type is 'text/html'.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_upload_txt_file():
    """Test uploading a TXT file and receiving a success response."""
    filename = "sample.txt"
    with open(filename, "w") as f:
        f.write("This is a test document.")

    with open(filename, "rb") as f:
        response = client.post(
            "/upload",
            headers=headers,
            files={"file": (filename, f, "text/plain")}
        )

    os.remove(filename)

    assert response.status_code == 200
    assert "File uploaded and indexed" in response.text


def test_ask_question():
    """Test asking a question and receiving an answer."""
    response = client.post(
        "/ask",
        headers=headers,
        json={"question": "What is this document about?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "latency" in data


def test_logs_endpoint():
    """Test fetching logs."""
    response = client.get("/logs", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_files():
    """Test retrieving list of uploaded files (or 404 if none)."""
    response = client.get("/files", headers=headers)
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert isinstance(response.json(), dict)