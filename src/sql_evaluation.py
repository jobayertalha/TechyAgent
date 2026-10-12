import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INTERACTIONS_FILE = DATA_DIR / "sql_interactions.jsonl"
RESULTS_FILE = DATA_DIR / "sql_evaluation_results.jsonl"
METRICS = ["answer_relevance", "answer_correctness", "groundedness"]
FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|"
    r"REPLACE|CALL|EXEC|EXECUTE|LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b",
    re.IGNORECASE,
)

def _read_jsonl(path):
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records

def _append_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

def record_sql_interaction(question, sql, database_result, answer, execution_success, execution_error=None):
    """Record a real SQL Assistant interaction for later, on-demand evaluation."""
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": str(question or ""),
        "sql": str(sql or ""),
        "database_result": str(database_result or ""),
        "answer": str(answer or ""),
        "execution_success": bool(execution_success),
        "execution_error": str(execution_error or ""),
        "evaluated": False,
    }
    _append_jsonl(INTERACTIONS_FILE, record)
    return record["id"]

def _extract_json_object(content):
    """Extract JSON from plain output, Markdown fences, or surrounding text."""
    if isinstance(content, list):
        content = "\n".join(
            str(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in content
        )
    text = str(content or "").strip()
    unfenced = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.I)
    for candidate in (unfenced.strip(), text):
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
        start = candidate.find("{")
        while start != -1:
            depth, in_string, escaped = 0, False, False
            for index in range(start, len(candidate)):
                char = candidate[index]
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                else:
                    if char == '"':
                        in_string = True
                    elif char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                value = json.loads(candidate[start:index + 1])
                                if isinstance(value, dict):
                                    return value
                            except json.JSONDecodeError:
                                pass
                            break
            start = candidate.find("{", start + 1)
    raise ValueError("Groq judge did not return a valid JSON object.")

def _extract_scores(content):
    values = _extract_json_object(content)
    scores = {}
    for metric in METRICS:
        if metric not in values:
            raise ValueError(f"Groq judge response is missing '{metric}'.")
        try:
            score = float(values[metric])
        except (TypeError, ValueError):
            raise ValueError(f"Groq judge returned a non-numeric '{metric}' score.")
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Invalid {metric} score: {score}")
        scores[metric] = score
    return scores

def _judge_interaction(record):
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from .env.")
    prompt = f"""
Evaluate one real interaction with a read-only SQL assistant.
Return exactly one JSON object, without Markdown fences or commentary:
{{"answer_relevance": 0.0, "answer_correctness": 0.0, "groundedness": 0.0}}
All scores must be numeric and between 0.0 and 1.0.
- answer_relevance: Does the answer address the question?
- answer_correctness: Does it agree with the supplied database result?
- groundedness: Are its factual claims supported by the supplied result?
- If execution failed or the database result is missing, correctness and
  groundedness must be at most 0.2.
- Ignore harmless spelling errors. Do not invent unsupported facts.
USER QUESTION: {record.get("question", "")}
GENERATED SQL: {record.get("sql") or "[No SQL captured]"}
EXECUTION SUCCESS: {record.get("execution_success")}
DATABASE RESULT: {record.get("database_result") or "[No database result]"}
EXECUTION ERROR: {record.get("execution_error") or "[None]"}
FINAL ANSWER: {record.get("answer", "")}
"""
    judge = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=api_key,
        temperature=0,
        max_tokens=300,
    )
    response = judge.invoke(prompt)
    return _extract_scores(response.content)

def _sql_is_valid(sql):
    """Objective safety screen; actual database execution is measured separately."""
    sql = (sql or "").strip()
    if not re.match(r"(?is)^\s*SELECT\b", sql):
        return False
    sql = sql.rstrip().rstrip(";").rstrip()
    if ";" in sql or FORBIDDEN_SQL.search(sql):
        return False
    return True

def _record_langsmith(record, evaluation):
    """Create a LangSmith run and attach feedback; local results remain primary."""
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        return None
    from langsmith import Client
    client = Client(api_key=api_key)
    run_id = uuid4()
    now = datetime.now(timezone.utc)
    project_name = os.getenv("LANGSMITH_PROJECT", "TechyAgent-SQL-Live-Evaluation")
    client.create_run(
        id=run_id,
        name="TechyAgent SQL Interaction Evaluation",
        run_type="chain",
        project_name=project_name,
        start_time=now,
        inputs={"question": record.get("question", ""), "sql": record.get("sql", "")},
        outputs={
            "answer": record.get("answer", ""),
            "database_result": record.get("database_result", ""),
            "execution_success": bool(record.get("execution_success", False)),
            "evaluation_status": evaluation.get("status", "unknown"),
            "evaluation_scores": evaluation.get("scores", {}),
        },
        end_time=datetime.now(timezone.utc),
        tags=["techyagent", "sql", "on-demand-evaluation"],
        extra={"metadata": {
            "interaction_id": record.get("id"),
            "execution_error": record.get("execution_error", ""),
        }},
    )
    if evaluation.get("status") == "completed":
        for metric, score in evaluation.get("scores", {}).items():
            client.create_feedback(
                run_id=run_id, key=metric, score=float(score),
                comment="Groq judge score for a recorded SQL interaction.",
            )
    client.create_feedback(
        run_id=run_id, key="sql_validity",
        score=float(evaluation.get("sql_validity", 0.0)),
        comment="Objective single read-only SELECT safety check.",
    )
    client.create_feedback(
        run_id=run_id, key="execution_success",
        score=float(bool(record.get("execution_success", False))),
        comment="Recorded MySQL execution outcome.",
    )
    return str(run_id)

def evaluate_pending_interactions():
    """Evaluate new interactions and retry only interactions whose latest result failed."""
    interactions = _read_jsonl(INTERACTIONS_FILE)
    existing_results = _read_jsonl(RESULTS_FILE)
    latest_status = {}
    for item in existing_results:
        interaction_id = item.get("interaction_id")
        if interaction_id and item.get("status"):
            latest_status[interaction_id] = item["status"]
    pending = [
        record for record in interactions
        if record.get("id") not in latest_status
        or latest_status.get(record.get("id")) == "failed"
    ]
    results = []
    for record in pending:
        evaluation = {
            "interaction_id": record.get("id", str(uuid4())),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": record.get("question", ""),
            "sql": record.get("sql", ""),
            "answer": record.get("answer", ""),
            "database_result": record.get("database_result", ""),
            "execution_success": bool(record.get("execution_success", False)),
            "sql_validity": float(_sql_is_valid(record.get("sql", ""))),
            "status": "completed",
            "scores": {},
            "answer_relevance": None,
            "answer_correctness": None,
            "groundedness": None,
            "evaluation_error": "",
            "langsmith_error": "",
        }
        try:
            evaluation["scores"] = _judge_interaction(record)
            for metric in METRICS:
                evaluation[metric] = evaluation["scores"][metric]
        except Exception as exc:
            evaluation["status"] = "failed"
            evaluation["evaluation_error"] = f"{type(exc).__name__}: {exc}"[:500]
        _append_jsonl(RESULTS_FILE, evaluation)
        results.append(evaluation)
        latest_status[evaluation["interaction_id"]] = evaluation["status"]
        try:
            run_id = _record_langsmith(record, evaluation)
            if run_id:
                evaluation["langsmith_run_id"] = run_id
                _append_jsonl(RESULTS_FILE, {
                    "interaction_id": evaluation["interaction_id"],
                    "langsmith_run_id": run_id,
                    "langsmith_linked_at": datetime.now(timezone.utc).isoformat(),
                    "status": evaluation["status"],
                })
        except Exception as exc:
            evaluation["langsmith_error"] = f"{type(exc).__name__}: {exc}"[:300]
    return results

def get_evaluation_results():
    """Merge canonical evaluation rows and LangSmith link metadata."""
    merged = {}
    for row in _read_jsonl(RESULTS_FILE):
        interaction_id = row.get("interaction_id")
        if not interaction_id:
            continue
        if interaction_id not in merged:
            merged[interaction_id] = dict(row)
        else:
            merged[interaction_id].update(row)
    return list(merged.values())

def get_recorded_interaction_count():
    return len(_read_jsonl(INTERACTIONS_FILE))

# ---------------------------------------------------------------------------
# Reference-answer evaluation with LangSmith
# This is separate from live-interaction evaluation above.
# ---------------------------------------------------------------------------
SQL_LANGSMITH_DATASET = "sql_evaluation"
SQL_REFERENCE_EXAMPLES = [
    {
        "question": "How many customers are in the database?",
        "answer": "There are 8 customers in the database.",
    },
    {
        "question": "How many software products are available?",
        "answer": "There are 5 software products in the database.",
    },
    {
        "question": "How many subscriptions are there in total?",
        "answer": "There are 14 subscriptions in total.",
    },
    {
        "question": "How many subscriptions are currently active?",
        "answer": "There are 11 active subscriptions.",
    },
    {
        "question": "What is the total monthly revenue from active subscriptions?",
        "answer": "The total monthly revenue from active subscriptions is $9,360.",
    },
    {
        "question": "Which product generates the highest revenue from active subscriptions, and how much?",
        "answer": "NovaAnalytics generates the highest active-subscription revenue, at $4,400.",
    },
    {
        "question": "How many customers are from Bangladesh?",
        "answer": "There are 4 customers from Bangladesh.",
    },
    {
        "question": "What is the name of the maintenance product?",
        "answer": "The maintenance product is NovaReports Classic.",
    },
]

def run_langsmith_dataset_evaluation():
    """Run the SQL chain against a separate reference-answer LangSmith dataset.
    Returns a dictionary containing the experiment URL and per-example results.
    This function does not change the SQL Assistant's normal execution path.
    """
    load_dotenv()
    langsmith_api_key = (
        os.getenv("LANGSMITH_API_KEY")
        or os.getenv("LANGCHAIN_API_KEY")
    )
    if not langsmith_api_key:
        raise ValueError("LANGSMITH_API_KEY is missing from .env.")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing from .env.")
    from langsmith import Client
    from langchain_groq import ChatGroq
    from langchain_helper import chain
    client = Client(api_key=langsmith_api_key)
    # Reuse the dedicated dataset if it already exists.
    datasets = list(client.list_datasets(dataset_name=SQL_LANGSMITH_DATASET))
    dataset = next(
        (item for item in datasets if item.name == SQL_LANGSMITH_DATASET),
        None,
    )
    if dataset is None:
        dataset = client.create_dataset(
            dataset_name=SQL_LANGSMITH_DATASET,
            description=(
                "Reference-answer evaluation set for the TechyAgent SQL Assistant. "
                "Kept separate from the RAG evaluation dataset."
            ),
        )
    # Use the existing manually uploaded dataset as-is. Do not silently
    # create/seed a second dataset or replace the user's reference examples.
    existing_examples = list(client.list_examples(dataset_id=dataset.id))
    if not existing_examples:
        raise ValueError(
            f"LangSmith dataset '{SQL_LANGSMITH_DATASET}' has no examples. "
            "Upload the SQL question/reference-answer CSV first."
        )
    judge = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=groq_api_key,
        temperature=0,
        max_tokens=200,
    )
    captured_results = []

    def target(inputs: dict) -> dict:
        """Run a dataset question and return its database answer."""
        question = str(inputs.get("question", "")).strip()
        if not question:
            raise ValueError("Dataset example is missing 'question'.")

        # Use the same SQL chain as the live application.
        result = chain.invoke({"query": question})

        # Normalize chain output. Some configurations return a dict with
        # "answer" and/or "sql"/"result"; others return a plain string.
        if isinstance(result, dict):
            answer = result.get("answer")
            candidate = result.get("sql") or result.get("result")
        else:
            answer = None
            candidate = result

        # Prefer an explicit final answer when the chain provides one.
        if answer is not None and str(answer).strip():
            return {"answer": str(answer)}

        if not candidate:
            raise ValueError(
                "SQL chain returned neither an answer nor a query."
            )

        candidate_text = str(candidate).strip()

        # Remove optional SQL code fences.
        cleaned = re.sub(
            r"^\s*```(?:sql)?\s*|\s*```\s*$",
            "",
            candidate_text,
            flags=re.IGNORECASE,
        ).strip()

        # Remove common chain labels like "SQLQuery:" or "Query:".
        cleaned = re.sub(
            r"^\s*(?:SQLQuery|Query)\s*:\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # If the text does not start with SELECT, try to locate one,
        # but only if nothing dangerous precedes it.
        if not cleaned.upper().startswith("SELECT"):
            match = re.search(r"\bSELECT\b", cleaned, flags=re.IGNORECASE)
            if match:
                prefix = cleaned[:match.start()]
                if re.search(
                    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|"
                    r"CREATE|REPLACE|GRANT|REVOKE|EXEC|EXECUTE|CALL)\b",
                    prefix,
                    flags=re.IGNORECASE,
                ):
                    raise ValueError(
                        "Unsafe SQL content appeared before SELECT."
                    )
                cleaned = cleaned[match.start():]

        # Strip chain-generated result/answer sections if present.
        cleaned = re.split(
            r"\n\s*(?:SQLResult|SQL Result|Answer)\s*:",
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        # If we still don't have SQL, preserve the raw response as the answer.
        if not cleaned.upper().startswith("SELECT"):
            return {"answer": candidate_text}

        # Validate the extracted SQL against the read-only safety check.
        if not _sql_is_valid(cleaned):
            raise ValueError(
                "Generated SQL failed the read-only SELECT safety check."
            )

        # SafeSQLDatabase.run() performs the existing validation.
        database = (
            getattr(chain, "database", None)
            or getattr(chain, "db", None)
        )
        if database is None:
            raise RuntimeError(
                "Could not access the SQL database attached to the chain."
            )

        database_result = database.run(cleaned)
        return {"answer": f"Database result: {database_result}"}

    def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
        """Notebook-compatible LangSmith evaluator signature."""
        question = str(inputs.get("question", ""))
        predicted = str(outputs.get("answer", ""))
        reference = str(reference_outputs.get("answer", ""))
        prompt = f"""
You are evaluating the correctness of a SQL assistant answer.
Compare the predicted answer with the reference answer using the question
and factual meaning, not exact wording. Mark correct only if the key factual
answer and numeric values agree. If the prediction is ambiguous, unsupported,
or contradicts the reference, mark it incorrect.
Return only a JSON object in this format:
{{"correct": true}}
Question: {question}
Reference answer: {reference}
Predicted answer: {predicted}
"""
        response = judge.invoke(prompt)
        parsed = _extract_json_object(response.content)
        score = parsed.get("correct", False)
        if isinstance(score, str):
            score = score.strip().lower() in {"true", "yes", "1"}
        score = bool(score)
        captured_results.append(
            {
                "question": question,
                "reference_answer": reference,
                "predicted_answer": predicted,
                "correct": score,
            }
        )
        return score

    experiment_results = client.evaluate(
        target,
        data=dataset.name,
        evaluators=[correctness],
        experiment_prefix="techyagent-sql-reference-evaluation",
        description="Reference-answer evaluation for the TechyAgent SQL Assistant.",
    )
    experiment_url = getattr(experiment_results, "experiment_url", None)
    if experiment_url is None:
        experiment_url = getattr(experiment_results, "url", None)
    return {
        "dataset_name": dataset.name,
        "experiment_url": str(experiment_url) if experiment_url else None,
        "results": captured_results,
    }