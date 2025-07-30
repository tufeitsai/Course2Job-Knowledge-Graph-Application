import streamlit as st
import requests

# -------- Streamlit Config --------
st.set_page_config(page_title="Role to Courses", layout="wide")
st.title("💼 Role to Courses Recommendation")

st.markdown("Type in your **career goal**, **major**, and **academic level** to get course suggestions!")

# -------- Initialize chat history --------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------- Input box --------
user_input = st.chat_input("Describe your goal (e.g., I'm a graduate in CS and want to be a machine learning engineer)")

# -------- Display previous messages --------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------- Handle new input --------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        with st.spinner("🤖 Thinking..."):
            res = requests.post("http://127.0.0.1:5000/chat", json={"message": user_input})
            res.raise_for_status()  # Will raise an error for non-200 responses
            bot_reply = res.json().get("reply", "Sorry, I didn't understand that.")
    except Exception as e:
        bot_reply = f"❌ Error: {e}\n\nRaw response: {res.text if 'res' in locals() else 'No response received'}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
