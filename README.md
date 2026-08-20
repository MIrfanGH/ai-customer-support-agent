# AI Customer Support Agent

A FastAPI-based AI customer support agent that answers questions using a controlled support corpus, with RAG, validation, retry handling, and source-grounded responses.



## 📂 Project Structure

The repository follows a modular architecture to support ingestion, retrieval, and LLM‑based response generation.

ai-customer-support-agent/
│
├── app/                # Core application logic
│   ├── main.py         # Entry point (FastAPI app)
│   ├── config.py       # Environment & settings
│   ├── api/            # API routes
│   ├── ingestion/      # Document processing pipeline
│   ├── retrieval/      # Vector store search
│   ├── llm/            # Classifier & LLM utilities
│   └── db/             # Database models & session
│
├── data/documents/     # Raw input documents
├── scripts/ingest.py   # Script for ingestion pipeline
├── tests/              # Unit & integration tests
│
├── PROJECT_SPEC.md     # Specification & design notes
├── README.md           # Project overview
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
└── COSTS.md            # Cost tracking (LLM/API usage)