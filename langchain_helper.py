
import os
import re

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from functools import lru_cache

from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_groq import ChatGroq
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector

from few_shots import few_shots


load_dotenv()


def clean_and_validate_sql(query: str) -> str:
    """Allow only a single read-only SELECT query."""

    query = query.strip()

    # Remove Markdown code fences.
    query = re.sub(r"\A```(?:sql)?\s*", "", query, flags=re.IGNORECASE)
    query = re.sub(r"\s*```\Z", "", query)

    # Remove the SQLQuery label if present.
    query = re.sub(
        r"^\s*SQLQuery\s*:\s*",
        "",
        query,
        flags=re.IGNORECASE,
    ).strip()

    # Remove one trailing semicolon.
    query = query.removesuffix(";").strip()

    if not query:
        raise ValueError("The model returned an empty SQL query.")

    # Only SELECT statements are allowed.
    if not re.match(r"^SELECT\b", query, flags=re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")

    # Prevent multiple SQL statements.
    if ";" in query:
        raise ValueError("Multiple SQL statements are not allowed.")

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|"
        r"REPLACE|GRANT|REVOKE|CALL|EXECUTE|LOAD|OUTFILE|DUMPFILE)\b",
        flags=re.IGNORECASE,
    )

    if forbidden.search(query):
        raise ValueError("The query contains a prohibited operation.")

    return query + ";"


class SafeSQLDatabase(SQLDatabase):
    """Validate generated SQL before executing it."""

    def run(self, command: str, *args, **kwargs) -> str:
        safe_command = clean_and_validate_sql(command)
        return super().run(safe_command, *args, **kwargs)


def get_few_shot_db_chain():
    """Create the TechyAgent SQL assistant."""

    required = [
        "GROQ_API_KEY",
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_NAME",
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}. "
            "Check your .env file."
        )

    # Connect to MySQL.
    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
    )

    db = SafeSQLDatabase.from_uri(
        connection_url,
        include_tables=[
            "software_products",
            "customers",
            "subscriptions",
        ],
        sample_rows_in_table_info=3,
    )

    # Configure Gemini.
    llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    )

    # Create embeddings for selecting relevant SQL examples.
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Store the examples in Chroma.
    examples_text = [
        " ".join(str(value) for value in example.values())
        for example in few_shots
    ]

    vectorstore = Chroma.from_texts(
        texts=examples_text,
        embedding=embeddings,
        metadatas=few_shots,
        collection_name="techyagent_sql_examples",
    )

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2,
    )

    # SQL generation instructions.
    mysql_prompt = """
You are TechyAgent, an assistant for an IT software company.

Convert the user's question into one valid MySQL SELECT query.

Rules:
- Use only software_products, customers, and subscriptions.
- Generate exactly one read-only SELECT query.
- Never generate write or administrative SQL operations.
- Use only columns present in the database schema.
- Use declared relationships when joining tables.
- For active monthly revenue, sum subscriptions.monthly_fee
  where subscription_status = 'Active'.
- Do not confuse base_monthly_price with actual subscription fees.
- Use LIMIT for listing queries.
- Never invent database results.
- Return raw SQL only, without Markdown fences.
- Do not add a preamble.

Return the SQL query only.
"""

    example_prompt = PromptTemplate(
        input_variables=[
            "Question",
            "SQLQuery",
            "SQLResult",
            "Answer",
        ],
        template=(
            "Question: {Question}\n"
            "SQLQuery: {SQLQuery}\n"
            "SQLResult: {SQLResult}\n"
            "Answer: {Answer}"
        ),
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=mysql_prompt,
        suffix=(
            "\nDatabase schema:\n{table_info}"
            "\n\nQuestion: {input}"
            "\nReturn at most {top_k} rows for listing queries."
            "\nSQLQuery:"
        ),
        input_variables=["input", "table_info", "top_k"],
    )

    # Build the chain.
    return SQLDatabaseChain.from_llm(
        llm=llm,
        db=db,
        prompt=few_shot_prompt,
        verbose=True,
        return_intermediate_steps=True,
        use_query_checker=False,
        top_k=10,
    )


# Create the chain when this module is imported.
@lru_cache(maxsize=1)
def get_cached_chain():
    return get_few_shot_db_chain()


chain = get_cached_chain()