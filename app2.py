import streamlit as st
import sqlite3
import google.generativeai as genai

# Gemini AI API Key
genai.configure(api_key="AIzaSyC2RdwCoxLHwXrcXDhcBCgAua4VqNk2ZBg")

# Database Setup
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Create Tables
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ingredients TEXT,
                    recipe TEXT,
                    favorite INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
conn.commit()

# Function to Generate Recipe using Gemini AI
def generate_recipe(ingredients):
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"Suggest a delicious recipe using these ingredients: {ingredients}"
    response = model.generate_content(prompt)
    return response.text

# Function to Register User
def register_user(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except:
        return False

# Function to Authenticate User
def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone()

# Streamlit UI
st.set_page_config(page_title="AI Chef 🍽️", page_icon="🍔", layout="wide")

st.markdown("<h1 style='text-align: center; color: #e63946;'>👨‍🍳 AI Chef - Smart Recipe Generator</h1>", unsafe_allow_html=True)

# Login / Signup System
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Sign Up":
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if register_user(new_user, new_pass):
            st.success("Account Created Successfully! Please Login.")
        else:
            st.error("Username already exists! Try another.")

elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state["user"] = user[0]  # Store user ID
            st.success(f"Welcome, {username}! 🎉")
        else:
            st.error("Invalid Credentials! Try Again.")

# Main App (After Login)
if "user" in st.session_state:
    st.subheader("🍽️ Enter Ingredients for Recipe Suggestion")

    # Ingredients Input
    ingredients = st.text_area("Enter ingredients (comma-separated):")

    # Generate Recipe Button
    if st.button("🍽️ Get Recipe", key="generate_recipe"):
        if ingredients:
            with st.spinner("Cooking... 🍳"):
                recipe = generate_recipe(ingredients)
            st.success("Here is your recipe:")
            st.write(recipe)

            # Save Recipe to Database
            cursor.execute("INSERT INTO recipes (user_id, ingredients, recipe) VALUES (?, ?, ?)",
                           (st.session_state["user"], ingredients, recipe))
            conn.commit()
        else:
            st.warning("Please enter some ingredients!")

    # Show Saved Recipes
    st.subheader("📜 Your Saved Recipes")
    cursor.execute("SELECT id, ingredients, recipe, favorite FROM recipes WHERE user_id=?", (st.session_state["user"],))
    saved_recipes = cursor.fetchall()

    if saved_recipes:
        for recipe_id, ingr, rec, fav in saved_recipes:
            with st.container():
                st.markdown(f"""
                    <div style="background-color: #fff; padding: 15px; border-radius: 10px; 
                                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 15px;">
                        <h4>🍲 Ingredients:</h4> {ingr}
                        <h4>📖 Recipe:</h4> {rec}
                    </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                
                with col1:
                    fav_label = "❤️ Favorite" if not fav else "💔 Unfavorite"
                    if st.button(fav_label, key=f"fav_{recipe_id}"):
                        new_fav_status = 1 if not fav else 0
                        cursor.execute("UPDATE recipes SET favorite=? WHERE id=?", (new_fav_status, recipe_id))
                        conn.commit()
                        st.rerun()

                with col2:
                    if st.button("🗑 Delete", key=f"del_{recipe_id}"):
                        cursor.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
                        conn.commit()
                        st.rerun()

    else:
        st.info("No saved recipes yet. Start cooking! 🍜")

# Close Database Connection
conn.close()