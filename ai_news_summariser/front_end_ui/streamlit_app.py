import streamlit as st
from sseclient import SSEClient
import threading
import time
import queue
import json

def stream_from_api(url, msg_queue, stop_event):
    messages = SSEClient(url)

    for msg in messages:
        
        if stop_event.is_set():
            print("Stop event set, exiting stream_from_api")
            return
        if msg.data:
            data = json.loads(msg.data)
            msg_queue.put({"key": data["node_name"], "data": data["node_result"]})
            print("-"*10,"\n\n",type(data["node_result"]))

            if data["node_name"] == "final_genre_summary":
                return

def main():
    st.title("📡 Streamlit SSE Streaming Demo")

    url = st.text_input("Enter your streaming API URL", "http://localhost:8080/news_summariser")

    if "streaming" not in st.session_state:
        st.session_state.streaming = False

    if "message_log" not in st.session_state:
        st.session_state.message_log = []

    if "msg_queue" not in st.session_state:
        st.session_state.msg_queue = queue.Queue()
    
    if "stop_event" not in st.session_state:
        st.session_state.stop_event = threading.Event()

    if st.button("Start Streaming") and not st.session_state.streaming:
        st.session_state.streaming = True
        st.session_state.stop_event.clear()

        # Start background thread, pass the queue
        thread = threading.Thread(target=stream_from_api, args=(url, st.session_state.msg_queue, st.session_state.stop_event), daemon=True)
        thread.start()

    
    message_placeholder = st.empty()

    if st.session_state.streaming:
        if st.button("Stop Streaming"):
            st.session_state.streaming = False
            st.session_state.stop_event.set()  # signal the thread to stop
            st.success("Streaming stopped.")

            with message_placeholder.container():
                for i, msg in enumerate(st.session_state.message_log):
                    st.write(f"{i+1}. {msg}")
                    
    st.subheader("📨 Incoming Messages:")
    # Poll messages from queue and update session state message_log
    if st.session_state.streaming:
        while st.session_state.streaming:
            try:
                # Non-blocking get with timeout
                msg = st.session_state.msg_queue.get(timeout=1)
                st.session_state.message_log.append(msg)
            except queue.Empty:
                pass

            with message_placeholder.container():
                for i, msg in enumerate(st.session_state.message_log):
                    st.write(f"{i+1}. {msg}")

            time.sleep(0.5)

if __name__ == "__main__":
    main()
