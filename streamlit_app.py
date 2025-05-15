import streamlit as st

st.title("My First App")
st.write("Hello World! 🚀")

# Add a sample slider
number = st.slider("Choose a number:", 0, 100, 50)
st.write(f"Selected number: {number}")
