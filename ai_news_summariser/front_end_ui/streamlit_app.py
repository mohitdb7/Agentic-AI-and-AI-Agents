import streamlit as st
from sseclient import SSEClient
import threading
import time
import queue
import json
import re
import html
from bs4 import BeautifulSoup
from collections import defaultdict
# The following import is crucial for binding the thread to the Streamlit context
from streamlit.runtime.scriptrunner import add_script_run_ctx 
# Assuming models.py is available
from models import WebResponseModel, SummarisedNewsArticleModel, NewsGenredSummaryModel, OutputGenreSummarisedResponseModel
from configs import FE_ConfigModel

fe_config = FE_ConfigModel.from_json_file("front_end_ui/configs/fe_config.json")

GENRES = fe_config.genres

# Genre colors for visual distinction
GENRE_COLORS = {
    "Politics": "#FF6B6B",
    "Technology": "#4ECDC4", 
    "AI": "#45B7D1",
    "Sports": "#96CEB4",
    "Business": "#FFEAA7",
    "Health": "#DDA0DD",
    "General": "#6C5CE7"
}

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

def parse_with_news_genre(nodes_result):
    """Parse genre-assigned news items into grouped dictionary."""
    result = NewsGenredSummaryModel(**nodes_result["categories"])
    
    # Convert to our internal format
    grouped_articles = {}
    for genre, articles in result.root.items():
        article_list = []
        for article in articles:
            article_dict = {
                "title": article.title if article.title else "",
                "description": clean_html_and_entities(article.summary) if article.summary else "",
                "url": article.url,
                "genre": genre
            }
            article_list.append(article_dict)
        grouped_articles[genre] = article_list
    
    return grouped_articles

def parse_final_news_summary_with_genre(nodes_result):
    final_summary = nodes_result
    items = OutputGenreSummarisedResponseModel(**final_summary)
    return items

def render_genre_timeline(grouped_articles):
    """Render articles grouped by genre in a timeline/chain view."""
    
    # Updated Timeline CSS for better alignment
    st.markdown("""
        <style>
        .timeline-container {
            max-height: 600px;
            overflow-y: auto;
            padding: 20px 0;
            margin-top: 15px; /* Add some space above the timeline */
        }
        
        /* FIX: Remove padding-left from .genre-section and use margin/positioning */
        .genre-section {
            margin-bottom: 40px;
            position: relative;
        }
        
        /* FIX: Increase header width and use margin-left to align it with content */
        .genre-header {
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding: 15px 20px;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            /* NEW: Give margin-left to push it right, aligning with the cards */
            margin-left: 30px; 
            position: relative;
        }
        
        .genre-badge {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            margin-left: 15px;
            font-size: 14px;
            font-weight: normal;
            backdrop-filter: blur(10px);
        }
        
        /* FIX: Adjust line position relative to the new header margin and content */
        .timeline-line {
            position: absolute;
            left: 36px; /* 36px to align with the dot center (30px margin + 6px center) */
            top: 70px; 
            bottom: 0;
            width: 3px;
            background: #444; 
            border-radius: 2px;
            z-index: 1; 
        }
        
        /* FIX: Keep margin-left to align with the header */
        .timeline-item {
            position: relative;
            margin-left: 60px; /* Aligns content slightly indented from the header */
            margin-bottom: 25px;
            padding: 20px 25px;
            background: #1e1e1e;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            color: #eee;
            border-left: 4px solid;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .timeline-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0,0,0,0.5);
        }
        
        /* FIX: Adjust dot position to align with the line (left: -24px from 60px margin) */
        .timeline-dot {
            position: absolute;
            left: -24px; 
            top: 25px;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #1e1e1e; 
            border: 4px solid;
            z-index: 2; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        
        .timeline-item h4 {
            margin: 0 0 12px 0;
            color: #ffffff;
            font-size: 16px;
            line-height: 1.4;
            font-weight: 600;
        }
        
        /* Description styling: NO TRUNCATION */
        .timeline-item p {
            margin: 0 0 15px 0;
            color: #ccc;
            font-size: 14px;
            line-height: 1.5;
            white-space: pre-wrap; 
        }
        
        .timeline-item a {
            color: #4da6ff;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .timeline-item a:hover {
            text-decoration: underline;
            color: #66b3ff;
        }
        
        .article-count {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 10px;
            font-style: italic;
        }

        /* Scrollbar styling */
        .timeline-container::-webkit-scrollbar {
            width: 8px;
        }

        .timeline-container::-webkit-scrollbar-track {
            background: #262730;
            border-radius: 4px;
        }

        .timeline-container::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;
        }

        .timeline-container::-webkit-scrollbar-thumb:hover {
            background: #777;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    
    for genre, articles in grouped_articles.items():
        genre_color = GENRE_COLORS.get(genre, "#6C5CE7")
        article_count = len(articles)
        
        # Genre header
        st.markdown(f"""
            <div class="genre-section">
                <div class="genre-header" style="background: {genre_color};">
                    <span>📰 {genre}</span>
                    <span class="genre-badge">{article_count} article{'s' if article_count != 1 else ''}</span>
                </div>
                <div class="timeline-line" style="background-color: {genre_color};"></div>
        """, unsafe_allow_html=True) 
        
        # Articles for this genre
        for i, article in enumerate(articles):
            title = article.get("title", "No Title")
            description = article.get("description", "")
            url = article.get("url", "")
            
            st.markdown(f"""
                <div class="timeline-item" style="border-left-color: {genre_color};">
                    <div class="timeline-dot" style="border-color: {genre_color};"></div>
                    <h4>{title}</h4>
                    <p>{description}</p>
                    {"<a href='" + url + "' target='_blank'>📖 Read full article</a>" if url else ""}
                    <div class="article-count">Article {i + 1} of {article_count}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
def stream_from_api(url, msg_queue, stop_event, params):
    """Background thread that streams data and sends it to the queue."""
    query_param = ",".join(fe_config.genres if len(params['genres']) == 0 else (params['genres'])).strip(",")
    
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
                if data.get("error"):
                    print(f"Error in stream response {data["error"]}")
                    st.session_state.streaming = False
                    st.session_state.stop_event.set()
                    st.session_state.stream_status = "idle"
                    st.rerun()
                    return
                
                node_name = data["node_name"]
                node_result = data["node_result"]
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e} with data: {msg.data}")
                continue # Skip to the next message

            # Instead of updating session_state here, send data via queue
            if node_name == "search_the_web":
                news_items = parse_news_items(node_result)
                msg_queue.put({"type": "news_item", "data": news_items})

            elif node_name == "summarise_the_news":
                news_items = parse_news_summaries(node_result)
                msg_queue.put({"type": "news_item_summary", "data": news_items})
            
            elif node_name == "assign_genre":
                genred_news_items = parse_with_news_genre(node_result)
                msg_queue.put({"type": "genre_assigned", "data": genred_news_items})                

            elif node_name == "final_genre_summary":
                final_summary = parse_final_news_summary_with_genre(node_result)
                msg_queue.put({"type" : "final_summary", "data" : final_summary})
                msg_queue.put({"type": "summary_done"})
                return

def render_final_summary():
    """
    Renders the final, aggregated summary for each genre using Streamlit expanders.
    The structure is expected to be Dict[str, OutputGenreSummaryModel] from
    st.session_state.final_summary.root.
    """
    st.subheader("Final Aggregated Summaries 📝")
    st.info("Below is the final, aggregated summary for each selected genre.")
    
    final_summary_data = st.session_state.final_summary.root
    
    if not final_summary_data:
        st.warning("No final summaries available to display.")
        return

    # Create a container for the summaries
    with st.container(border=True):
        for genre, summary_model in final_summary_data.items():
            genre_color = GENRE_COLORS.get(genre, "#6C5CE7")
            
            # Use an expander for each genre summary
            # We use an unsafe markdown with a style block to color the expander's header area
            st.markdown(
                f"""
                <style>
                .stExpander {{
                    border: 1px solid {genre_color};
                    border-radius: 8px;
                    margin-bottom: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    background-color: #262730; /* Dark background */
                }}
                .stExpander details summary {{
                    color: {genre_color}; /* Color the genre title */
                    font-weight: bold;
                    font-size: 18px;
                    padding: 10px 15px;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
            
            with st.expander(f"✨ **{genre} Summary**", expanded=True):
                # The summary is an attribute of the Pydantic model
                summary_text = summary_model.final_summary
                
                # Display the summary text in a styled box
                st.markdown(
                    f"""
                    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 5px; border-left: 5px solid {genre_color};">
                        <p style='white-space: pre-wrap;'>{summary_text}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

def main():
    st.title("🧠 AI News Summariser")

    # Genre chips
    selected_genres = st.multiselect("Select Genres", GENRES, default=GENRES[0])
    url = f"{fe_config.base_url}:{fe_config.port}{fe_config.endpoints["news_summariser"].url}"# st.text_input("Streaming API URL", "http://localhost:8080/news_summariser")

    # Session state initialization
    if "streaming" not in st.session_state:
        st.session_state.streaming = False

    if "news_items" not in st.session_state:
        st.session_state.news_items = []

    if "genre_articles" not in st.session_state:
        st.session_state.genre_articles = {}
    
    if "final_summary" not in st.session_state:
        st.session_state.final_summary = {}

    if "stream_status" not in st.session_state:
        st.session_state.stream_status = "idle"  # idle, fetching, summarizing, assigning_genre, complete

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
        st.session_state.genre_articles = {}
        st.session_state.final_summary = {}
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
        print(st.session_state.streaming, st.session_state.stream_status)
        if st.session_state.stream_status == "fetching":
            st.info("🔍 Fetching news articles...")
        elif st.session_state.stream_status == "summarizing":
            st.info("📝 Summarizing news articles...")
        elif st.session_state.stream_status == "assigning_genre":
            st.info("🏷️ Assigning genres to articles...")
        elif st.session_state.stream_status == "final_summary":
            st.info("✅ Generating final summary...")
    elif st.session_state.stream_status == "final_summary":
        st.info("")


# ----------------------------------------------------------------------
# --- CORE FIX: Process Queue Messages WITHOUT Blocking UI ---
# ----------------------------------------------------------------------

    # Poll queue and update news
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
                    st.session_state.stream_status = "assigning_genre"
                    should_rerun = True
                    
                elif msg["type"] == "genre_assigned":
                    st.session_state.genre_articles = msg["data"]
                    st.session_state.stream_status = "assigning_genre"
                    should_rerun = True
                
                elif msg["type"] == "final_summary":
                    st.session_state.final_summary = msg["data"]
                    st.session_state.stream_status = "final_summary"
                    
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

    st.subheader("🗞️ News Articles")

    if st.session_state.final_summary:
        render_final_summary()
    
    # Render genre-based articles if available
    if st.session_state.genre_articles:
        # Show genre summary metrics
        total_articles = sum(len(articles) for articles in st.session_state.genre_articles.values())
        genre_count = len(st.session_state.genre_articles)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Articles", total_articles)
        with col2:
            st.metric("Genres Covered", genre_count)
        with col3:
            if st.session_state.genre_articles:
                most_articles_genre = max(st.session_state.genre_articles.items(), key=lambda x: len(x[1]))
                st.metric("Top Genre", f"{most_articles_genre[0]} ({len(most_articles_genre[1])})")
        
        st.markdown("---")
        
        # Render timeline/chain view
        render_genre_timeline(st.session_state.genre_articles)
        
    # Fallback: Render regular news items if genre articles not ready
    elif st.session_state.news_items:
        st.info("📋 Processing articles for genre assignment...")
        
        # Inject card CSS (simplified fallback card)
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