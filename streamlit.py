import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Load environment variables
load_dotenv()

# Database connection configuration
db_config = {
    "host": "gateway01.ap-northeast-1.prod.aws.tidbcloud.com", # REPLACE with your TiDB Host
    "user": "2kGWXq57L6vMrMK.root",                              # REPLACE with your TiDB User
    "password": "adskK1GljNGdhhsQ",                       # REPLACE with your TiDB Password
    "database": "test",                               # REPLACE with the DB name you used in Step 2 (often 'test')
    "port": 4000,                                     # TiDB uses port 4000, not 3306
    "ssl_disabled": False                             # Enforce SSL/TLS
}

# Function to create a database connection
def create_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as e:
        st.error(f"Error connecting to database: {e}")
        logging.error(f"Database connection error: {e}")
        return None

# Function to execute SELECT queries
def fetch_data(query, params=None):
    connection = create_connection()
    if connection:
        try:
            df = pd.read_sql(query, connection, params=params)
            connection.close()
            return df
        except mysql.connector.Error as e:
            st.error(f"Error executing query: {e}")
            logging.error(f"Query error: {e} - Query: {query} - Params: {params}")
            return None
    return None

# Function to execute INSERT, UPDATE, DELETE queries
def execute_query(query, params=None):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
            logging.error(f"Execute query error: {e} - Query: {query} - Params: {params}")
            return False
    return False

# Function to validate input
def validate_input(data, required_fields):
    for field, value in data.items():
        if field in required_fields and (value is None or value == ""):
            st.error(f"{field} is required.")
            return False
    return True

# Function to check if foreign key exists
def check_foreign_key(table, column, value):
    query = f"SELECT COUNT(*) FROM {table} WHERE {column} = %s"
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query, (value,))
            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return count > 0
        except mysql.connector.Error as e:
            st.error(f"Error checking foreign key: {e}")
            logging.error(f"Foreign key check error: {e}")
            return False
    return False

# Initialize session state for fetched record
if "fetched_record" not in st.session_state:
    st.session_state.fetched_record = None
if "fetch_triggered" not in st.session_state:
    st.session_state.fetch_triggered = False

# Streamlit App
st.title("Personal Finance Management System 💸")
st.markdown("Manage your income, expenses, and budgets.")

# Sidebar for navigation
st.sidebar.title("Navigation")
option = st.sidebar.selectbox(
    "Select Operation",
    ["View Data", "Add Record", "Update Record", "Delete Record", "Run Queries"]
)
table = st.sidebar.selectbox(
    "Select Table",
    ["users", "categories", "incomes", "expenses", "budgets"]
)

# CRUD Operations
if option == "View Data":
    st.subheader(f"View {table} Data")
    query = f"SELECT * FROM {table}"
    data = fetch_data(query)
    if data is not None:
        st.dataframe(data, use_container_width=True)

elif option == "Add Record":
    st.subheader(f"Add New {table} Record")
    with st.form(f"add_{table}_form"):
        if table == "users":
            user_id = st.number_input("User ID", min_value=1, step=1)
            name = st.text_input("Name", max_chars=100)
            email = st.text_input("Email", max_chars=100)
            password = st.text_input("Password", type="password", max_chars=255)
            
            data = {"user_id": user_id, "name": name, "email": email, "password": password}
            required_fields = ["user_id", "name", "email", "password"]
            query = "INSERT INTO users (user_id, name, email, password) VALUES (%s, %s, %s, %s)"
            params = (user_id, name, email, password)

        elif table == "categories":
            category_id = st.number_input("Category ID", min_value=1, step=1)
            user_ids = fetch_data("SELECT user_id FROM users")["user_id"].tolist()
            user_id = st.selectbox("User ID", user_ids) if user_ids else st.number_input("User ID", min_value=1)
            name = st.text_input("Category Name", max_chars=100)
            description = st.text_area("Description")

            data = {"category_id": category_id, "user_id": user_id, "name": name}
            required_fields = ["category_id", "user_id", "name"]
            query = "INSERT INTO categories (category_id, user_id, name, description) VALUES (%s, %s, %s, %s)"
            params = (category_id, user_id, name, description)

        elif table == "incomes":
            income_id = st.number_input("Income ID", min_value=1, step=1)
            
            # --- START OF CHANGES ---
            # 1. Fetch User Names to show instead of just IDs
            users_df = fetch_data("SELECT user_id, name FROM users")
            user_map = dict(zip(users_df["name"], users_df["user_id"])) if users_df is not None else {}
            selected_user_name = st.selectbox("User", list(user_map.keys())) if user_map else None
            user_id = user_map[selected_user_name] if selected_user_name else st.number_input("User ID", min_value=1)

            source = st.text_input("Source", max_chars=100)

            # 2. Fetch Category Names to show instead of just IDs
            cat_df = fetch_data("SELECT category_id, name FROM categories")
            # Create a dictionary mapping Name -> ID
            cat_map = dict(zip(cat_df["name"], cat_df["category_id"])) if cat_df is not None else {}
            # Show the Names in the selectbox
            selected_cat_name = st.selectbox("Category", list(cat_map.keys())) if cat_map else None
            # Retrieve the ID corresponding to the selected Name
            category_id = cat_map[selected_cat_name] if selected_cat_name else st.number_input("Category ID", min_value=1)
            # --- END OF CHANGES ---

            amount = st.number_input("Amount", min_value=0.0, step=0.01)
            income_date = st.date_input("Date", value=datetime.now())
            note = st.text_area("Note")

            data = {"income_id": income_id, "user_id": user_id, "amount": amount}
            required_fields = ["income_id", "user_id", "amount"]
            query = "INSERT INTO incomes (income_id, user_id, source, category_id, amount, income_date, note) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            params = (income_id, user_id, source, category_id, amount, income_date, note)

        elif table == "expenses":
            expense_id = st.number_input("Expense ID", min_value=1, step=1)
             # --- START OF CHANGES ---
            # 1. Fetch User Names to show instead of just IDs
            users_df = fetch_data("SELECT user_id, name FROM users")
            user_map = dict(zip(users_df["name"], users_df["user_id"])) if users_df is not None else {}
            selected_user_name = st.selectbox("User", list(user_map.keys())) if user_map else None
            user_id = user_map[selected_user_name] if selected_user_name else st.number_input("User ID", min_value=1)

            source = st.text_input("Source", max_chars=100)

            # 2. Fetch Category Names to show instead of just IDs
            cat_df = fetch_data("SELECT category_id, name FROM categories")
            # Create a dictionary mapping Name -> ID
            cat_map = dict(zip(cat_df["name"], cat_df["category_id"])) if cat_df is not None else {}
            # Show the Names in the selectbox
            selected_cat_name = st.selectbox("Category", list(cat_map.keys())) if cat_map else None
            # Retrieve the ID corresponding to the selected Name
            category_id = cat_map[selected_cat_name] if selected_cat_name else st.number_input("Category ID", min_value=1)
            # --- END OF CHANGES ---

            amount = st.number_input("Amount", min_value=0.0, step=0.01)
            income_date = st.date_input("Date", value=datetime.now())
            note = st.text_area("Note")

            data = {"income_id": "expense_id", "user_id": user_id, "amount": amount}
            required_fields = ["income_id", "user_id", "amount"]
            query = "INSERT INTO incomes (income_id, user_id, source, category_id, amount, income_date, note) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            params = (expense_id, user_id, source, category_id, amount, income_date, note)
            
        elif table == "budgets":
            budget_id = st.number_input("Budget ID (Auto-inc if 0)", min_value=0, step=1)
            user_ids = fetch_data("SELECT user_id FROM users")["user_id"].tolist()
            user_id = st.selectbox("User ID", user_ids) if user_ids else st.number_input("User ID", min_value=1)
            cat_ids = fetch_data("SELECT category_id FROM categories")["category_id"].tolist()
            category_id = st.selectbox("Category ID", cat_ids) if cat_ids else st.number_input("Category ID", min_value=1)
            limit_amount = st.number_input("Limit Amount", min_value=0.0, step=0.01)
            start_date = st.date_input("Start Date", value=datetime.now())
            end_date = st.date_input("End Date", value=datetime.now())

            data = {"user_id": user_id, "limit_amount": limit_amount}
            required_fields = ["user_id", "limit_amount"]
            # Handling auto-increment for budget_id if left 0
            if budget_id > 0:
                query = "INSERT INTO budgets (budget_id, user_id, category_id, limit_amount, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s)"
                params = (budget_id, user_id, category_id, limit_amount, start_date, end_date)
            else:
                 query = "INSERT INTO budgets (user_id, category_id, limit_amount, start_date, end_date) VALUES (%s, %s, %s, %s, %s)"
                 params = (user_id, category_id, limit_amount, start_date, end_date)

        submitted = st.form_submit_button("Add Record")
        if submitted:
            if validate_input(data, required_fields):
                valid_fk = True
                
                # RULE 1: Check User ID (Foreign Key)
                # Only check if User exists if we are NOT currently adding a new User
                if table != "users" and "user_id" in locals():
                     if not check_foreign_key("users", "user_id", user_id):
                        st.error("Invalid User ID (User does not exist)")
                        valid_fk = False

                # RULE 2: Check Category ID (Foreign Key)
                # Only check if Category exists if we are NOT currently adding a new Category
                if table != "categories" and "category_id" in locals():
                     if not check_foreign_key("categories", "category_id", category_id):
                        st.error("Invalid Category ID (Category does not exist)")
                        valid_fk = False

                # If all checks pass, save to database
                if valid_fk:
                    if execute_query(query, params):
                        st.success(f"{table} record added successfully!")
                        logging.info(f"Added {table} record: {params}")

elif option == "Update Record":
    st.subheader(f"Update {table} Record")
    
    # Determine Primary Key based on table name
    pk_map = {
        "users": "user_id",
        "categories": "category_id",
        "incomes": "income_id",
        "expenses": "expense_id",
        "budgets": "budget_id"
    }
    pk_col = pk_map[table]
    
    record_id = st.number_input(f"{table} ID to Update", min_value=1, step=1, key=f"update_id_{table}")

    if st.button("Fetch Record"):
        st.session_state.fetch_triggered = True
        query = f"SELECT * FROM {table} WHERE {pk_col} = %s"
        data = fetch_data(query, (record_id,))
        if data is not None and not data.empty:
            st.session_state.fetched_record = data.iloc[0].to_dict()
        else:
            st.error(f"{table} record not found.")
            st.session_state.fetched_record = None

    if st.session_state.fetch_triggered and st.session_state.fetched_record:
        rec = st.session_state.fetched_record
        with st.form(f"update_{table}_form"):
            if table == "users":
                name = st.text_input("Name", value=rec["name"], max_chars=100)
                email = st.text_input("Email", value=rec["email"], max_chars=100)
                password = st.text_input("Password", value=rec["password"], type="password")
                query = "UPDATE users SET name=%s, email=%s, password=%s WHERE user_id=%s"
                params = (name, email, password, record_id)
                
            elif table == "categories":
                name = st.text_input("Category Name", value=rec["name"])
                description = st.text_area("Description", value=rec["description"] or "")
                query = "UPDATE categories SET name=%s, description=%s WHERE category_id=%s"
                params = (name, description, record_id)
                
            elif table == "expenses":
                amount = st.number_input("Amount", value=float(rec["amount"]))
                note = st.text_area("Note", value=rec["note"] or "")
                # Simply updating amount/note for simplicity, could add FKs if needed
                query = "UPDATE expenses SET amount=%s, note=%s WHERE expense_id=%s"
                params = (amount, note, record_id)

            elif table == "incomes":
                amount = st.number_input("Amount", value=float(rec["amount"]))
                note = st.text_area("Note", value=rec["note"] or "")
                query = "UPDATE incomes SET amount=%s, note=%s WHERE income_id=%s"
                params = (amount, note, record_id)

            elif table == "budgets":
                limit_amount = st.number_input("Limit Amount", value=float(rec["limit_amount"]))
                query = "UPDATE budgets SET limit_amount=%s WHERE budget_id=%s"
                params = (limit_amount, record_id)

            if st.form_submit_button("Update Record"):
                if execute_query(query, params):
                    st.success("Updated successfully!")
                    st.session_state.fetched_record = None
                    st.session_state.fetch_triggered = False

elif option == "Delete Record":
    st.subheader(f"Delete {table} Record")
    pk_map = {
        "users": "user_id", "categories": "category_id",
        "incomes": "income_id", "expenses": "expense_id", "budgets": "budget_id"
    }
    pk_col = pk_map[table]
    
    del_id = st.number_input(f"Enter {pk_col} to Delete", min_value=1, step=1)
    if st.button("Delete"):
        query = f"DELETE FROM {table} WHERE {pk_col} = %s"
        if execute_query(query, (del_id,)):
            st.success("Deleted successfully!")
        else:
            st.error("Delete failed. Check dependencies.")

elif option == "Run Queries":
    st.subheader("Run Predefined Queries")
    query_option = st.selectbox(
        "Select Query",
        [
            "All Incomes with User Names",
            "Total Expenses by User",
            "Categories with User Details",
            "Budgets vs Limits"
        ]
    )
    
    if st.button("Run Query"):
        if query_option == "All Incomes with User Names":
            query = """
            SELECT u.name AS User, i.source, i.amount, i.income_date 
            FROM incomes i
            JOIN users u ON i.user_id = u.user_id
            """
        elif query_option == "Total Expenses by User":
            query = """
            SELECT u.name, SUM(e.amount) as Total_Expense
            FROM expenses e
            JOIN users u ON e.user_id = u.user_id
            GROUP BY u.name
            """
        elif query_option == "Categories with User Details":
            query = """
            SELECT c.name as Category, c.description, u.name as Owner
            FROM categories c
            JOIN users u ON c.user_id = u.user_id
            """
        elif query_option == "Budgets vs Limits":
            query = """
            SELECT u.name, c.name as Category, b.limit_amount, b.start_date, b.end_date
            FROM budgets b
            JOIN users u ON b.user_id = u.user_id
            JOIN categories c ON b.category_id = c.category_id
            """
            
        data = fetch_data(query)
        if data is not None:
            st.dataframe(data, use_container_width=True)

