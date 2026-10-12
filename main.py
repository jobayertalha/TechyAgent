import streamlit as st
from langchain_helper import get_few_shot_db_chain

st.set_page_config(page_title="TechyAgent", page_icon="🛠️", layout="centered")

st.title("🛠️ TechyAgent")
st.caption("AI assistant for IT company data — ask questions about products, customers, and subscriptions.")

with st.sidebar:
    st.subheader("Example questions")
    st.markdown(
        "- Which products are active?\n"
        "- Which customers have past-due subscriptions?\n"
        "- What is the monthly revenue from active subscriptions?\n"
        "- Which product generates the most active subscription revenue?\n"
        "- Show enterprise subscriptions and customer names."
    )
    st.info("This first version answers questions from the MySQL database. Technical-document RAG will be added next.")

question = st.text_input(
    "Ask a question about TechyAgent's software products or subscriptions",
    placeholder="e.g. Which customers have past-due subscriptions?",
)

if question:
    try:
        with st.spinner("Querying the database..."):
            chain = get_few_shot_db_chain()
            result = chain.invoke({"query": question})

        st.subheader("Answer")
        st.write(result.get("result", "No answer was returned."))

        steps = result.get("intermediate_steps")
        if steps:
            with st.expander("View generated SQL and execution details"):
                st.write(steps)
    except Exception as exc:
        st.error("The request could not be completed. Check your database connection, API key, and package setup.")
        with st.expander("Technical details"):
            st.code(str(exc))
