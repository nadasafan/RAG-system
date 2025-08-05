# 📚 QA Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A smart web application that enables users to upload PDF or TXT files and ask questions about their content. The answers are generated using advanced AI models from OpenAI and information retrieval powered by Elasticsearch.

---

## 🚀 Features

- ✅ Secure login with email and password
- 📄 Supports uploading PDF and TXT documents
- 🧠 AI-powered content analysis via OpenAI
- 🔎 Search and retrieve answers using Elasticsearch
- 💬 Ask natural language questions and get intelligent answers
- 🗂️ Logs all Q&A into a local SQLite database
- 🌐 Simple and modern UI built with HTML + TailwindCSS

---

## 🧪 Demo Credentials

| Email                | Password |
|----------------------|----------|
| `admin@example.com`  | `123`    |

---

## 📦 Requirements

Before starting, make sure you have:

- Python 3.10 or higher
- An active OpenAI API Key
- A running Elasticsearch instance
- Internet connection

---

## ⚙️ Installation & Running

```bash
# 1. (Optional but recommended) Create a virtual environment
python -m venv venv

# Activate the virtual environment:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 2. Install required dependencies
pip install -r requirements.txt

# 3. Run the application
uvicorn main:app --reload


📁 QA_Assistant_Project
├── app/                   # (Optional) extra modules
├── templates/             # HTML templates
│   └── index.html
├── static/                # CSS/JS files if any
├── logs.db                # SQLite database
├── requirements.txt       # Dependency list
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Optional Docker setup
├── main.py                # Main FastAPI app
└── README.md              # This file
