# TechyAgent 🤖

TechyAgent is an AI-powered SQL assistant for a fictional IT software company. It lets users ask questions in natural language and explore database information through a Streamlit dashboard.

## Features

- **AI SQL Assistant:** Converts natural-language questions into MySQL queries.
- **Read-only SQL validation:** Restricts generated queries to a single `SELECT` statement.
- **Semantic few-shot examples:** Uses LangChain, sentence-transformer embeddings, and Chroma to select relevant SQL examples.
- **Evaluation dashboard:** Records SQL interactions and evaluates answer relevance, correctness, and groundedness on demand.
- **Interactive dashboard:** Includes Dashboard, SQL Assistant, Evaluation, and Contact pages.

## Tech Stack

Python · Streamlit · LangChain · Groq · MySQL · SQLAlchemy · Chroma · Sentence Transformers

## Run Locally

1. Clone this repository.
2. Create and activate a Python virtual environment.
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the required configuration:

   ```env
   GROQ_API_KEY=your_groq_api_key
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_PORT=3306
   DB_NAME=techyagent_db
   ```

5. Create the MySQL database using [`database/technyagent_it.sql`](database/technyagent_it.sql).
6. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

The MySQL server must be running and reachable from your machine.

## Evaluation

The Evaluation page uses locally recorded SQL interactions. Evaluation results are stored in local JSONL files under `data/`; these generated files are excluded from the repository.

## Security Notes

- Never commit `.env`, API keys, database passwords, or Streamlit secrets.
- Use a dedicated, read-only MySQL account for the assistant.
- This is a portfolio prototype using fictional sample data, not a production support system.
