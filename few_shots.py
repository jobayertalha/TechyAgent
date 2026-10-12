
few_shots = [
    {
        "Question": "Which software products are currently active?",
        "SQLQuery": """
            SELECT product_name, category
            FROM software_products
            WHERE product_status = 'Active'
        """,
        "SQLResult": "Example result: CRM Platform, Analytics Suite",
        "Answer": "These are the currently active software products."
    },
    {
        "Question": "Which customers have past-due subscriptions?",
        "SQLQuery": """
            SELECT DISTINCT c.company_name
            FROM customers c
            JOIN subscriptions s
                ON c.customer_id = s.customer_id
            WHERE s.subscription_status = 'Past Due'
        """,
        "SQLResult": "Example result: Apex Manufacturing",
        "Answer": "These customers have past-due subscriptions."
    },
    {
        "Question": "What is the total monthly revenue from active subscriptions?",
        "SQLQuery": """
            SELECT SUM(monthly_fee) AS monthly_revenue
            FROM subscriptions
            WHERE subscription_status = 'Active'
        """,
        "SQLResult": "Example result: 5000.00",
        "Answer": "The total monthly revenue from active subscriptions is 5000.00."
    },
    {
        "Question": "How many customers are in Bangladesh?",
        "SQLQuery": """
            SELECT COUNT(*) AS customer_count
            FROM customers
            WHERE country = 'Bangladesh'
        """,
        "SQLResult": "Example result: 4",
        "Answer": "There are 4 customers in Bangladesh."
    },
    {
        "Question": "Which software products generate the most active subscription revenue?",
        "SQLQuery": """
            SELECT p.product_name, SUM(s.monthly_fee) AS monthly_revenue
            FROM software_products p
            JOIN subscriptions s
                ON p.product_id = s.product_id
            WHERE s.subscription_status = 'Active'
            GROUP BY p.product_id, p.product_name
            ORDER BY monthly_revenue DESC
            LIMIT 5
        """,
        "SQLResult": "Example result: CRM Platform, 900.00",
        "Answer": "These products generate the highest active subscription revenue."
    }
]
