import streamlit as st
from sseclient import SSEClient
import threading
import time
import queue
import json
import re
import html
from bs4 import BeautifulSoup
# The following import is crucial for binding the thread to the Streamlit context
from streamlit.runtime.scriptrunner import add_script_run_ctx 
from models import WebResponseModel, SummarisedNewsArticleModel


GENRES = ["Politics", "Technology", "AI", "Sports", "Business", "Health"]

# At the top of your script, outside any function
msg_queue = queue.Queue()
stop_event = threading.Event()

def clean_html_and_entities(text):
    # Remove HTML using BeautifulSoup (better than regex for real HTML)
    soup = BeautifulSoup(text, "html.parser")
    text_no_html = soup.get_text(separator=' ')
    
    # Decode HTML entities (e.g., &amp;, &#39;)
    text_unescaped = html.unescape(text_no_html)
    
    # Remove unicode control characters, excess whitespace
    text_cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text_unescaped)  # remove control chars
    text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()  # normalize whitespace

    return text_cleaned

def parse_news_items(nodes_result):
    """Parse API response into list of news item dicts."""
    # Assuming nodes_result is a dictionary that can be unpacked into WebResponseModel
    node_search = WebResponseModel(**nodes_result) 
    items = []
    print(f"Total News items - {len(node_search.results)}")
    for item in node_search.results:
        item_node_dict = {
            "title": getattr(item, 'title', "") if hasattr(item, 'title') else "",
            "description": clean_html_and_entities(getattr(item, 'content', "")) if hasattr(item, 'content') else "",
            "url": getattr(item, 'url', "") if hasattr(item, 'url') else ""
        }
        items.append(item_node_dict)
    return items

def parse_news_summaries(nodes_result):
    """Parse API response into list of news item dicts with Summaries."""
    # Assuming nodes_result is a list of dictionaries for SummarisedNewsArticleModel
    node_search = [SummarisedNewsArticleModel(**item) for item in nodes_result]

    items = []
    print(f"Total News summary items - {len(node_search)}")
    for item in node_search:
        item_node_dict = {
            "title": item.title if item.title else "",
            "description": clean_html_and_entities(item.summary) if item.summary else "",
            "url": item.url
        }
        items.append(item_node_dict)
    return items


def stream_from_api(url, msg_queue, stop_event, params):
    """Background thread that streams data and sends it to the queue."""
    query_param = ",".join(params['genres']).strip(",")
    
    # Use a try-except block to handle connection errors gracefully
    try:
        messages = SSEClient(url + f"?query={query_param}")
    except Exception as e:
        print(f"Error connecting to SSE stream: {e}")
        # Put an error message into the queue to alert the main thread
        msg_queue.put({"type": "error", "data": f"Connection Error: {e}"})
        return

    for msg in messages:
        if stop_event.is_set():
            print("Stop event set, exiting stream_from_api")
            return

        if msg.data:
            try:
                data = json.loads(msg.data)
                node_name = data["node_name"]
                node_result = data["node_result"]
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e} with data: {msg.data}")
                continue # Skip to the next message

            # Instead of updating session_state here, send data via queue
            if node_name == "search_the_web":
                news_items = parse_news_items(node_result)
                msg_queue.put({"type": "news_item", "data": news_items})

            if node_name == "summarise_the_news":
                news_items = parse_news_summaries(node_result)
                msg_queue.put({"type": "news_item_summary", "data": news_items})

            elif node_name == "final_genre_summary":
                msg_queue.put({"type": "summary_done"})
                return


def main():
    st.title("🧠 AI News Summariser")

    # Genre chips
    selected_genres = st.multiselect("Select Genres", GENRES, default=["AI"])
    url = st.text_input("Streaming API URL", "http://localhost:8080/news_summariser")

    # Session state initialization
    if "streaming" not in st.session_state:
        st.session_state.streaming = False

    if "news_items" not in st.session_state:
        st.session_state.news_items = []

    if "stream_status" not in st.session_state:
        st.session_state.stream_status = "idle"  # idle, fetching, summarizing, complete

    # Use the global queue objects
    if "msg_queue" not in st.session_state:
        st.session_state.msg_queue = msg_queue

    if "stop_event" not in st.session_state:
        st.session_state.stop_event = stop_event

    # Start streaming
    if st.button("Search & Stream") and not st.session_state.streaming:
        st.session_state.streaming = True
        st.session_state.stop_event.clear()
        st.session_state.news_items = []
        st.session_state.stream_status = "fetching"
        
        # Clear the queue from any previous runs
        while not st.session_state.msg_queue.empty():
            st.session_state.msg_queue.get_nowait()

        params = {"genres": selected_genres}
        thread = threading.Thread(
            target=stream_from_api,
            args=(url, st.session_state.msg_queue, st.session_state.stop_event, params),
            daemon=True
        )
        add_script_run_ctx(thread)  # Binds thread to Streamlit context
        thread.start()
        st.rerun() # Immediately rerun to start the polling loop

    # Stop streaming
    if st.session_state.streaming and st.button("Stop Streaming"):
        st.session_state.streaming = False
        st.session_state.stop_event.set()
        st.session_state.stream_status = "idle"
        st.success("✅ Streaming stopped.")
        st.rerun()

    # Display status
    if st.session_state.streaming:
        if st.session_state.stream_status == "fetching":
            st.info("🔍 Fetching news articles...")
        elif st.session_state.stream_status == "summarizing":
            st.info("📝 Summarizing news articles...")

# ----------------------------------------------------------------------
# --- CORE FIX: Process Queue Messages WITHOUT Blocking UI ---
# ----------------------------------------------------------------------

    # Poll queue and update news (NO SPINNER - this was blocking the UI)
    if st.session_state.streaming:
        messages_processed = 0
        should_rerun = False
        
        try:
            # Process all available messages without blocking
            while True:
                msg = st.session_state.msg_queue.get_nowait()
                print(f"Processing message: {msg['type']}")
                messages_processed += 1
                
                if msg["type"] == "news_item":
                    st.session_state.news_items = msg["data"]
                    st.session_state.stream_status = "summarizing"
                    should_rerun = True
                    
                elif msg["type"] == "news_item_summary":
                    st.session_state.news_items = msg["data"]
                    should_rerun = True
                    
                elif msg["type"] == "summary_done":
                    st.success("✅ Summary generation complete.")
                    st.session_state.streaming = False
                    st.session_state.stream_status = "complete"
                    should_rerun = True
                    break
                    
                elif msg["type"] == "error":
                    st.error(f"Streaming Error: {msg['data']}")
                    st.session_state.streaming = False
                    st.session_state.stream_status = "idle"
                    should_rerun = True
                    break
                    
        except queue.Empty:
            # No messages available right now
            pass

# ----------------------------------------------------------------------
# --- UI Rendering (Always Happens) ---
# ----------------------------------------------------------------------

    st.subheader("🗞️ News Items")
    
    # Always render the news items container
    if st.session_state.news_items:
        # Inject card CSS
        st.markdown("""
            <style>
            .news-card {
                border: 1px solid #444;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 15px;
                background-color: #1e1e1e;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.5);
                color: #eee;
            }
            .news-card h4 {
                margin: 0 0 10px;
                color: #ffffff;
            }
            .news-card p {
                margin: 0 0 10px;
                color: #ccc;
            }
            .news-card a {
                color: #4da6ff;
                text-decoration: none;
                font-weight: bold;
            }
            .news-card a:hover {
                text-decoration: underline;
            }
            </style>
        """, unsafe_allow_html=True)
        # Start the scrollable container
        st.markdown('<div class="scrollable-news">', unsafe_allow_html=True)

        # Render each news item as a card
        for item in st.session_state.news_items:
            title = item.get("title", "No Title")
            description = item.get("description", "")
            url = item.get("url")

            st.markdown(f"""
                <div class="news-card">
                    <h4>{title}</h4>
                    <p>{description}</p>
                    {"<a href='" + url + "' target='_blank'>Read full article</a>" if url else ""}
                </div>
            """, unsafe_allow_html=True)

        # End the scrollable container
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        if not st.session_state.streaming:
            st.info("Click 'Search & Stream' to start fetching news articles.")
        else:
            st.info("Waiting for news articles...")

# ----------------------------------------------------------------------
# --- Rerun Logic (After UI Rendering) ---
# ----------------------------------------------------------------------

    # Handle rerun logic AFTER UI rendering
    if st.session_state.streaming:
        if should_rerun or messages_processed > 0:
            print(f"Rerunning due to {messages_processed} processed messages")
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
            st.rerun()
        else:
            # Continue polling even when no messages
            print("Continuing to poll for messages...")
            time.sleep(0.5)  # Longer delay when no messages
            st.rerun()


if __name__ == "__main__":
    main()