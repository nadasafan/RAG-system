from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
import sqlite3, os, time, hashlib, urllib3, nest_asyncio, uvicorn

# Allow asyncio reentry and suppress certificate warnings in development
nest_asyncio.apply()
urllib3.disable_warnings()

# FastAPI app setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
security = HTTPBasic()

# Elasticsearch configuration
ES_URL = "https://6d84c186e61444748fef843caa05b264.us-central1.gcp.cloud.es.io:443"
USERNAME = "elastic"
PASSWORD = "B1rXTbSF1xIEH1OyMbJ2VzBq"
es_client = Elasticsearch(ES_URL, basic_auth=(USERNAME, PASSWORD), verify_certs=True)

# OpenAI API key
os.environ["OPENAI_API_KEY"] = "######"#api-keys

# Database path
DB_PATH = os.getenv("DB_PATH", "logs.db")

# -------- Helper Functions --------
def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            question TEXT,
            response TEXT,
            timestamp TEXT,
            latency REAL)''')
        conn.commit()

def create_default_user():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                         ("admin@example.com", hash_pass("123")))
            conn.commit()
    except sqlite3.IntegrityError:
        pass

def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    email, password = credentials.username, hash_pass(credentials.password)
    with sqlite3.connect(DB_PATH) as conn:
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return email

# Setup on startup
setup_database()
create_default_user()

# -------- API Endpoints --------

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login-check")
async def login_check(user: str = Depends(authenticate)):
    return {"message": "✅ Authenticated"}

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...), user: str = Depends(authenticate)):
    temp_path = f"temp_{user.replace('@', '_').replace('.', '_')}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    loader = PyPDFLoader(temp_path) if file.filename.endswith(".pdf") else TextLoader(temp_path)
    docs = loader.load()
    chunks = CharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
    index_name = f"docs_{user.replace('@', '').replace('.', '')}"
    embeddings = OpenAIEmbeddings()

    ElasticsearchStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        es_url=ES_URL,
        index_name=index_name,
        es_user=USERNAME,
        es_password=PASSWORD,
        verify_certs=True
    )
    os.remove(temp_path)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"✅ File uploaded and indexed: {file.filename}"
    })

class Question(BaseModel):
    question: str

@app.post("/ask")
async def ask(question: Question, user: str = Depends(authenticate)):
    index_name = f"docs_{user.replace('@', '').replace('.', '')}"
    if not es_client.indices.exists(index=index_name):
        raise HTTPException(status_code=404, detail="No uploaded documents found.")

    start = time.time()
    vectorstore = ElasticsearchStore(
        embedding=OpenAIEmbeddings(),
        index_name=index_name,
        es_url=ES_URL,
        es_user=USERNAME,
        es_password=PASSWORD,
        verify_certs=True
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    qa = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
    response = qa.run(question.question)
    latency = round(time.time() - start, 2)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''INSERT INTO logs (user_email, question, response, timestamp, latency)
                        VALUES (?, ?, ?, datetime('now'), ?)''',
                     (user, question.question, response, latency))
        conn.commit()

    return {"answer": response, "latency": latency}

@app.get("/logs")
async def get_logs(user: str = Depends(authenticate)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT * FROM logs WHERE user_email=?", (user,))
        return [{
            "id": row[0],
            "user_email": row[1],
            "question": row[2],
            "response": row[3],
            "timestamp": row[4],
            "latency": row[5]
        } for row in cursor.fetchall()]

@app.get("/files")
async def get_files(user: str = Depends(authenticate)):
    index_name = f"docs_{user.replace('@', '').replace('.', '')}"
    if not es_client.indices.exists(index=index_name):
        raise HTTPException(status_code=404, detail="No uploaded files.")
    return es_client.indices.get(index=index_name)

# Run the server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
