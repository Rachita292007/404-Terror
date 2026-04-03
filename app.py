import streamlit as st
import requests

st.title("Ignisia Frontend")

# The IP of Laptop 3 (the LLM/Backend laptop)
# Ask Person 3 for their 'ipconfig' or 'ifconfig' address!
BACKEND_URL = "http://10.23.xx.xxx:8001/query" 

user_input = st.text_input("Ask a question:")

if st.button("Send"):
    # Sending the request to the Backend Laptop
    response = requests.post(BACKEND_URL, json={"prompt": user_input})
    
    if response.status_code == 200:
        st.write(response.json()["answer"])
    else:
        st.error("Could not connect to Backend.")