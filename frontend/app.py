import streamlit as st
import requests

st.title("Streamlit Frontend")

response = requests.get("http://127.0.0.1:8000/api/data")

if response.status_code == 200:
    data = response.json()
    st.write(data["message"])
else:
    st.error("Failed to fetch data from the backend.")
