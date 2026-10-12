import re
import streamlit as st
# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="TechyAgent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ============================================================
# SESSION STATE
# ============================================================
DEFAULTS = {
    "dark_mode": True,
    "page": "Dashboard",
    "sql_messages": [],
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
# Keep old saved navigation values from breaking the app.
if st.session_state.page == "AI Assistant":
    st.session_state.page = "Dashboard"
# ============================================================
# THEME
# ============================================================
if st.session_state.dark_mode:
    bg = "#10131C"
    sidebar = "#171B28"
    card = "#1C2232"
    text = "#F5F6FA"
    muted = "#AAB3C5"
    border = "#343B50"
else:
    bg = "#F5F7FB"
    sidebar = "#FFFFFF"
    card = "#FFFFFF"
    text = "#172033"
    muted = "#596579"
    border = "#DCE2EC"
maroon = "#842747"
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg};
        color: {text};
    }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar};
        border-right: 1px solid {border};
    }}
    h1, h2, h3, p, label {{
        color: {text};
    }}
    .brand {{
        font-size: 27px;
        font-weight: 800;
        color: {text};
        margin-bottom: 4px;
    }}
    .brand span {{
        color: {maroon};
    }}
    .subtitle {{
        color: {muted};
        font-size: 14px;
        margin-bottom: 24px;
    }}
    .card {{
        background: {card};
        border: 1px solid {border};
        border-top: 3px solid {maroon};
        border-radius: 12px;
        padding: 20px;
        min-height: 145px;
    }}
    .card h3 {{
        margin-top: 0;
        font-size: 19px;
    }}
    .card p {{
        color: {muted};
        font-size: 14px;
        line-height: 1.6;
    }}
    /* Keep Dashboard cards exactly the same height. */
    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {{
        height: 270px !important;
        min-height: 270px !important;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
    }}
    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {{
        height: 100%;
        min-height: 0;
        display: flex;
        flex-direction: column;
    }}
    /* Keep the action buttons aligned at the bottom of each card. */
    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"] {{
        margin-top: auto;
    }}
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid {maroon} !important;
        color: {text} !important;
        background: {card} !important;
        transition: background-color 160ms ease, border-color 160ms ease;
    }}
    .stButton > button:hover,
    .stButton > button:focus,
    .stButton > button:active {{
        color: #FFFFFF !important;
        background: {maroon} !important;
        border-color: {maroon} !important;
    }}
    .stButton > button[kind="primary"] {{
        color: #FFFFFF !important;
        background: {maroon} !important;
        border-color: {maroon} !important;
    }}
    a {{
        color: {maroon} !important;
    }}
    hr {{
        border-color: {border};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
# ============================================================
# NAVIGATION
# ============================================================
PAGES = ["Dashboard", "SQL Assistant", "Evaluation", "Contact"]
with st.sidebar:
    st.markdown(
        '<div class="brand">Techy<span>Agent</span> 🤖</div>',
        unsafe_allow_html=True,
    )
    st.caption("AI-powered IT assistant")
    st.divider()
    if st.button(
        "☀️ Light mode" if st.session_state.dark_mode else "🌙 Dark mode",
        use_container_width=True,
        key="toggle_theme",
    ):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    st.divider()
    st.markdown("### Navigation")
    for page in PAGES:
        if st.button(
            page,
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if st.session_state.page == page else "secondary",
        ):
            st.session_state.page = page
            st.rerun()
    st.divider()
    st.caption("TechyAgent · Your Support Asistant")
# ============================================================
# DASHBOARD
# ============================================================
if st.session_state.page == "Dashboard":
    st.title("TechyAgent Dashboard")
    st.markdown(
        '<div class="subtitle">Your AI-powered IT business and technical support assistant.</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.subheader("🗄️ SQL Assistant")
            st.write(
                "Ask questions about customers, software products, and subscriptions "
                "using natural language."
            )
            st.write("")
            if st.button(
                "Open SQL Assistant →",
                key="open_sql",
                use_container_width=True,
            ):
                st.session_state.page = "SQL Assistant"
                st.rerun()
    with col2:
        with st.container(border=True):
            st.subheader("📊 SQL Evaluation")
            st.write(
                "Review evaluation metrics from recorded SQL Assistant interactions."
            )
            st.write("")
            if st.button(
                "Open Evaluation →",
                key="open_eval",
                use_container_width=True,
            ):
                st.session_state.page = "Evaluation"
                st.rerun()
    st.write("")
    st.info("Ask database questions in SQL Assistant or review recorded interaction metrics in Evaluation.")
# ============================================================
# SQL ASSISTANT
# ============================================================
elif st.session_state.page == "SQL Assistant":
    st.title("🗄️ SQL Assistant")
    st.write("Ask questions about customers, software products, and subscriptions.")
    if st.button("🗑️ Clear conversation", key="clear_sql"):
        st.session_state.sql_messages = []
        st.rerun()
    for message in st.session_state.sql_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sql"):
                with st.expander("View SQL query"):
                    st.code(message["sql"], language="sql")
    question = st.chat_input(
        "Ask a question about your database...",
        key="sql_chat_input",
    )
    if question:
        st.session_state.sql_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        executed_sql = None
        database_result = None
        answer = None
        with st.chat_message("assistant"):
            with st.spinner("Querying the database..."):
                try:
                    from langchain_helper import chain
                    # Keep the existing LangChain SQL chain and its read-only
                    # validation. The user's question is not restricted to a
                    # predefined list of prompts.
                    result = chain.invoke({"query": question})
                    steps = result.get("intermediate_steps", [])
                    for step in steps:
                        if isinstance(step, dict):
                            if step.get("sql_cmd"):
                                executed_sql = str(step["sql_cmd"]).strip()
                        elif isinstance(step, str):
                            stripped = step.strip()
                            if stripped.upper().startswith("SELECT") and executed_sql is None:
                                executed_sql = stripped
                            # SQLDatabaseChain often stores query output as a
                            # string representation of rows in a later step.
                            if stripped.startswith("[") or stripped.startswith("("):
                                database_result = stripped
                    if database_result is None:
                        raw_result = result.get("result")
                        if raw_result is not None:
                            database_result = str(raw_result)
                    # Some SQLDatabaseChain versions put generated SQL in
                    # result["result"] instead of returning the rows clearly.
                    # If rows were not extracted from intermediate_steps, execute
                    # the captured SELECT once more through the same safe DB wrapper.
                    if database_result is None and executed_sql:
                        try:
                            database = getattr(chain, "database", None) or getattr(chain, "db", None)
                            if database is not None:
                                database_result = str(database.run(executed_sql))
                        except Exception:
                            # Keep the original response as a fallback; do not hide
                            # the SQL chain's original successful result.
                            pass
                    raw_result = result.get("result")
                    final_answer = result.get("answer")
                    def _looks_like_sql(value):
                        return isinstance(value, str) and value.strip().upper().startswith(
                            ("SELECT ", "WITH ", "INSERT ", "UPDATE ", "DELETE ")
                        )
                    if database_result is not None:
                        # Render scalar results as values and multi-column results as Markdown tables.
                        try:
                            import ast
                            parsed_rows = ast.literal_eval(database_result)

                            if not isinstance(parsed_rows, (list, tuple)):
                                parsed_rows = [(parsed_rows,)]
                            elif parsed_rows and not isinstance(parsed_rows[0], (list, tuple)):
                                parsed_rows = [(value,) for value in parsed_rows]

                            parsed_rows = [list(row) for row in parsed_rows]

                            if not parsed_rows:
                                display_result = "No rows returned."
                            elif len(parsed_rows) == 1 and len(parsed_rows[0]) == 1:
                                display_result = str(parsed_rows[0][0])
                            else:
                                # Derive readable headings from SELECT aliases/column names.
                                columns = []
                                if executed_sql:
                                    match = re.search(
                                        r"\bSELECT\s+(.*?)\s+FROM\b",
                                        executed_sql,
                                        flags=re.IGNORECASE | re.DOTALL,
                                    )
                                    if match:
                                        select_part = match.group(1)
                                        expressions = []
                                        current = []
                                        depth = 0
                                        for char in select_part:
                                            if char == "(":
                                                depth += 1
                                            elif char == ")":
                                                depth = max(0, depth - 1)
                                            if char == "," and depth == 0:
                                                expressions.append("".join(current).strip())
                                                current = []
                                            else:
                                                current.append(char)
                                        if current:
                                            expressions.append("".join(current).strip())

                                        for expression in expressions:
                                            alias = re.search(
                                                r"\s+AS\s+[\"`]?([\w ]+)[\"`]?\s*$",
                                                expression,
                                                flags=re.IGNORECASE,
                                            )
                                            if alias:
                                                columns.append(alias.group(1).strip())
                                            else:
                                                clean_expression = expression.strip().strip('"`')
                                                columns.append(clean_expression.split(".")[-1].strip('"`'))

                                width = max(len(row) for row in parsed_rows)
                                if len(columns) != width:
                                    columns = [f"Column {index + 1}" for index in range(width)]

                                def _cell(value):
                                    return str(value).replace("|", "\\|").replace("\n", " ")

                                table_lines = [
                                    "| " + " | ".join(_cell(name) for name in columns) + " |",
                                    "| " + " | ".join("---" for _ in columns) + " |",
                                ]
                                table_lines.extend(
                                    "| " + " | ".join(_cell(value) for value in row) + " |"
                                    for row in parsed_rows
                                )
                                display_result = "\n".join(table_lines)
                        except (ValueError, SyntaxError, TypeError):
                            display_result = database_result

                        answer = f"**Database result:**\n\n{display_result}"
                    elif raw_result is not None and not _looks_like_sql(str(raw_result)):
                        answer = str(raw_result)
                    elif final_answer is not None and not _looks_like_sql(str(final_answer)):
                        answer = str(final_answer)
                    else:
                        answer = (
                            "The query ran, but I couldn't extract the database result. "
                            "Open **View SQL query** and check the terminal for details."
                        )
                    st.markdown(str(answer))
                    if executed_sql:
                        with st.expander("View SQL query"):
                            st.code(executed_sql, language="sql")
                    st.session_state.sql_messages.append(
                        {
                            "role": "assistant",
                            "content": str(answer),
                            "sql": executed_sql,
                        }
                    )
                    # Record only the interaction. The evaluator is not called
                    # during normal SQL Assistant usage.
                    try:
                        from src.sql_evaluation import record_sql_interaction
                        record_sql_interaction(
                            question=question,
                            sql=executed_sql,
                            database_result=database_result,
                            answer=str(answer),
                            execution_success=True,
                        )
                    except ImportError:
                        st.warning(
                            "Interaction was not recorded because src/sql_evaluation.py "
                            "is not available yet."
                        )
                    except Exception as record_error:
                        st.warning(f"Could not record this interaction: {record_error}")
                except Exception as e:
                    error_text = f"{type(e).__name__}: {e}"
                    st.error("The SQL Assistant encountered an error.")
                    st.code(error_text)
                    # Failed executions are also recorded so execution-success
                    # metrics include failures, not only successful queries.
                    try:
                        from src.sql_evaluation import record_sql_interaction
                        record_sql_interaction(
                            question=question,
                            sql=executed_sql,
                            database_result=database_result,
                            answer="SQL execution failed.",
                            execution_success=False,
                            execution_error=error_text,
                        )
                    except Exception:
                        pass
# ============================================================
# SQL EVALUATION
# ============================================================
elif st.session_state.page == "Evaluation":
    st.title("📊 SQL Assistant Evaluation")
    st.write(
        "Evaluate the actual SQL Assistant interactions recorded during normal use. "
        "Evaluation runs only when you press the button below."
    )
    try:
        import src.sql_evaluation as sql_evaluation
        from src.sql_evaluation import (
            evaluate_pending_interactions,
            get_evaluation_results,
            get_recorded_interaction_count,
        )
    except ImportError as exc:
        st.error("The SQL evaluation module is not available.")
        st.code(f"{type(exc).__name__}: {exc}")
        st.info("Create and save src/sql_evaluation.py before starting an evaluation.")
    else:
        # Clear history removes saved SQL interactions and their evaluation results.
        if "confirm_clear_sql_history" not in st.session_state:
            st.session_state.confirm_clear_sql_history = False
        header_col, action_col = st.columns([3, 1], vertical_alignment="center")
        with header_col:
            st.metric("Recorded interactions", get_recorded_interaction_count())
        with action_col:
            if st.button(
                "🗑️ Clear history",
                use_container_width=True,
                key="request_clear_sql_history",
            ):
                st.session_state.confirm_clear_sql_history = True
                st.rerun()
        if st.session_state.confirm_clear_sql_history:
            st.warning(
                "This permanently removes saved SQL interaction history and evaluation results. "
                "It does not delete database records or your LangSmith datasets."
            )
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button(
                    "Confirm clear history",
                    type="primary",
                    use_container_width=True,
                    key="confirm_clear_sql_history_button",
                ):
                    try:
                        sql_evaluation.INTERACTIONS_FILE.parent.mkdir(
                            parents=True, exist_ok=True
                        )
                        sql_evaluation.INTERACTIONS_FILE.write_text("", encoding="utf-8")
                        sql_evaluation.RESULTS_FILE.write_text("", encoding="utf-8")
                        st.session_state.confirm_clear_sql_history = False
                        st.success("SQL interaction and evaluation history cleared.")
                        st.rerun()
                    except Exception as clear_error:
                        st.error(f"Could not clear history: {clear_error}")
            with cancel_col:
                if st.button(
                    "Cancel",
                    use_container_width=True,
                    key="cancel_clear_sql_history_button",
                ):
                    st.session_state.confirm_clear_sql_history = False
                    st.rerun()
        total = get_recorded_interaction_count()
        if st.button(
            "▶️ Start Evaluation",
            type="primary",
            use_container_width=True,
            key="start_sql_evaluation",
        ):
            if total == 0:
                st.warning("No SQL interactions have been recorded. Ask a question in SQL Assistant first.")
            else:
                with st.spinner("Evaluating recorded SQL interactions..."):
                    try:
                        new_results = evaluate_pending_interactions()
                        completed_new = sum(
                            1 for item in new_results if item.get("status") == "completed"
                        )
                        failed_new = len(new_results) - completed_new
                        st.success(
                            f"Evaluation finished: {completed_new} completed, "
                            f"{failed_new} failed, out of {len(new_results)} newly processed interactions."
                        )
                    except Exception as exc:
                        st.error("Evaluation could not be completed.")
                        st.code(f"{type(exc).__name__}: {exc}")
        results = get_evaluation_results()
        if not results:
            st.info("No evaluation results yet. Click Start Evaluation after recording SQL interactions.")
        else:
            # In case an earlier run wrote more than one record for an
            # interaction, display the most recently written result.
            latest_by_id = {}
            for item in results:
                latest_by_id[item.get("interaction_id", item.get("id", str(id(item))))] = item
            results = list(latest_by_id.values())
            completed = [item for item in results if item.get("status") == "completed"]
            failed = [item for item in results if item.get("status") != "completed"]
            st.subheader("Evaluation Summary")
            m1, m2 = st.columns(2)
            m1.metric("Completed evaluations", len(completed))
            m2.metric("Failed evaluations", len(failed))
            metric_keys = [
                ("sql_validity", "SQL validity"),
                ("execution_success", "Execution success"),
                ("answer_correctness", "Answer correctness"),
                ("answer_relevance", "Answer relevance"),
                ("groundedness", "Groundedness"),
            ]
            metric_cols = st.columns(len(metric_keys))
            for col, (key, label) in zip(metric_cols, metric_keys):
                values = []
                for item in completed:
                    value = item.get(key)
                    if value is None and isinstance(item.get("scores"), dict):
                        value = item["scores"].get(key)
                    if value is not None:
                        try:
                            values.append(float(value))
                        except (TypeError, ValueError):
                            pass
                if key == "execution_success":
                    # Prefer the objective recorded execution status.
                    values = [
                        1.0 if item.get("execution_success") is True else 0.0
                        for item in completed
                        if item.get("execution_success") is not None
                    ]
                col.metric(label, f"{sum(values) / len(values):.1%}" if values else "N/A")
            st.caption(
                "SQL validity and execution success should be objective checks. "
                "Answer correctness, relevance, and groundedness are LLM-judge estimates, "
                "not ground-truth measurements unless reference answers are supplied."
            )
            with st.expander("View interaction details"):
                for index, item in enumerate(results, start=1):
                    question_text = item.get("question", "(question unavailable)")
                    st.markdown(f"**{index}. {question_text}**")
                    st.caption(f"Status: {item.get('status', 'unknown')}")
                    if item.get("sql"):
                        st.markdown("**Generated SQL**")
                        st.code(item["sql"], language="sql")
                    if item.get("answer"):
                        st.markdown("**Assistant answer**")
                        st.write(item["answer"])
                    if item.get("evaluation_error"):
                        st.error(item["evaluation_error"])
                    st.divider()
# ============================================================
# CONTACT
# ============================================================
elif st.session_state.page == "Contact":
    st.title("📞 Contact")
    st.write("Get in touch with the developer.")
    with st.container(border=True):
        st.subheader("Talha Jobayer Zihan")
        st.write("Researcher & AI/ML Engineer")
        st.divider()
        st.markdown("**📱 Phone**")
        st.markdown("[+880 1721 577792](tel:+8801721577792)")
        st.markdown("**✉️ Email**")
        st.markdown("[jobayertalha2020@gmail.com](mailto:jobayertalha2020@gmail.com)")
        st.markdown("**💻 GitHub**")
        st.markdown("[github.com/jobayertalha](https://github.com/jobayertalha)")
        st.markdown("**🔗 LinkedIn**")
        st.markdown("[linkedin.com/in/talha-jobayer](https://www.linkedin.com/in/talha-jobayer-696a74237/)")
        st.markdown("**🌐 Portfolio**")
        st.markdown("[Personal Portfolio](https://v0-personal-portfolio-site-tau.vercel.app/)")
