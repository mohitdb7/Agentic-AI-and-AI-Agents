
import streamlit as st
from sseclient import SSEClient
import threading
import time
import queue
import json
import requests


GENRES = ["Politics", "Technology", "AI", "Sports", "Business", "Health"]

def stream_from_api(url, msg_queue, stop_event, params):

    queryParam = ",".join(params['genres']).strip(",")

    # Optionally, append params to URL as query string
    messages = SSEClient(url + f"?query={queryParam}")

    
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
    st.title("AI News Summariser")

    # Genre chips
    selected_genres = st.multiselect("Select Genres", GENRES, default=["AI"])
    search_query = st.text_input("Search News", "")

    url = st.text_input("Streaming API URL", "http://localhost:8080/news_summariser")

    if "streaming" not in st.session_state:
        st.session_state.streaming = False

    if "news_items" not in st.session_state:
        st.session_state.news_items = []

    if "msg_queue" not in st.session_state:
        st.session_state.msg_queue = queue.Queue()

    if "stop_event" not in st.session_state:
        st.session_state.stop_event = threading.Event()

    # Start streaming
    if st.button("Search & Stream") and not st.session_state.streaming:
        st.session_state.streaming = True
        st.session_state.stop_event.clear()
        st.session_state.news_items = []

        # Pass genres and search to API if needed
        params = {"genres": selected_genres, "search": search_query}
        thread = threading.Thread(target=stream_from_api, args=(url, st.session_state.msg_queue, st.session_state.stop_event, params), daemon=True)
        thread.start()

    # Stop streaming
    if st.session_state.streaming and st.button("Stop Streaming"):
        st.session_state.streaming = False
        st.session_state.stop_event.set()
        st.success("Streaming stopped.")

    st.subheader("🗞️ News Items")
    news_placeholder = st.empty()

    # Poll messages and update news list
    if st.session_state.streaming:
        while st.session_state.streaming:
            try:

                msg = st.session_state.msg_queue.get(timeout=1)
                # Update or add news item
                if msg.get("type") == "news_item":
                    st.session_state.news_items.append(msg)
                elif msg.get("type") == "news_summary":
                    # Find and update the news item with summary
                    for item in st.session_state.news_items:
                        if item.get("id") == msg.get("id"):
                            item["summary"] = msg.get("summary")
                            break
            except queue.Empty:
                pass

            with news_placeholder.container():
                for i, item in enumerate(st.session_state.news_items):
                    st.markdown(f"**{item.get('title', 'No Title')}**")
                    st.write(item.get("description", ""))
                    if item.get("url"):
                        st.write(f"[Read more]({item.get('url')})")
                    if item.get("summary"):
                        st.success(f"Summary: {item['summary']}")
                    st.write("---")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
