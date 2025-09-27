
import asyncio
from typing import List, Dict
from rest_api.models import NewsSummaryResult
# Import your custom logger
from rest_api.utils import (
    cleanup_old_logs,
    log_node,
    log_with_context
)
from news_agent_flow import create_news_agent_with_final_summary_flow
from rest_api.storage import StorageManager
import json
from datetime import datetime, timezone
import time

class NewsSummarizer:
    def __init__(self, be_config):
        try:
            self.be_config = be_config
            log_with_context("app_init", {"event": "Loaded backend config successfully"}, source="undecided", request_id="NewsSummarizer_init")
        except Exception as e:
            log_with_context("app_init", {"event": "Failed to load backend config"}, source="undecided", request_id="NewsSummarizer_init", error=str(e))
            raise e

        self.in_progress_queries: Dict[str, asyncio.Lock] = {}  # query -> Lock
        self.partial_results: Dict[str, List[NewsSummaryResult]] = {}  # query -> partial results list
        self.complete_results: Dict[str, List[NewsSummaryResult]] = {}  # query -> complete results list

        try:
            StorageManager.initialize()
            log_with_context("app_init", {"event": "StorageManager initialized successfully"}, source="undecided", request_id="NewsSummarizer_init")
        except Exception as e:
            log_with_context("app_init", {"event": "Failed to initialize StorageManager"}, source="undecided", request_id="NewsSummarizer_init", error=str(e))
            raise e

        try:
            self.graph_final_summary = create_news_agent_with_final_summary_flow()
            log_with_context("app_init", {"event": "News agent flow created successfully"}, source="undecided", request_id="NewsSummarizer_init")
        except Exception as e:
            log_with_context("app_init", {"event": "Failed to create news agent flow"}, source="undecided", request_id="NewsSummarizer_init", error=str(e))
            raise e

    async def startup_setup(self):
        try:
            await StorageManager.startup_setup()
            log_with_context("app_init", {"event": "StorageManager startup setup completed"}, source="undecided", request_id="NewsSummarizer_init")
        except Exception as e:
            log_with_context("app_init", {"event": "StorageManager startup setup failed"}, source="undecided", request_id="NewsSummarizer_init", error=str(e))
            raise e


    @log_node("news_agent_stream")
    async def news_agent_stream(self, state: dict):
        outer_stream_lit = "news_agent_stream"
        query = state.get("query", "")
        request_id = state.get("request_id", "")
        query_key = ",".join(sorted(query.split(","))).strip(",").strip(' ')
        event_node_map = self.be_config.stream_events
        result_key_flow = self.be_config.stream_sequence

        log_with_context(outer_stream_lit, {"event": "Processing query", "query_key": query_key}, source="undecided", request_id=request_id)

        if query_key not in self.in_progress_queries:
            self.in_progress_queries[query_key] = asyncio.Lock()
        lock = self.in_progress_queries[query_key]

        try:
            is_all_values_present = await StorageManager.get_all_documents_count(f"{query_key}")
            print(f"Returned {is_all_values_present} {is_all_values_present and is_all_values_present == len(result_key_flow)}")
        except Exception as e:
            log_with_context(outer_stream_lit, {"event": "Error fetching stored documents", "query_key": query_key}, source="undecided", request_id=request_id, error=str(e))
            is_all_values_present = False

        if is_all_values_present and is_all_values_present == len(result_key_flow):
            log_with_context(outer_stream_lit, {"event": "Serving cached results", "query_key": query_key}, source="storage", request_id=request_id)
            for keys_flow in result_key_flow:
                try:
                    result = await StorageManager.get_document(f"{query_key}_{keys_flow}")
                    if result:
                        output = {
                            "node_name": keys_flow,
                            "node_result": result.result
                        }
                        yield f"data:{json.dumps(output)}\n\n"
                        log_with_context(outer_stream_lit, {"event": "Yielded streaming data", "query_key": query_key}, source="storage", request_id=request_id)
                        time.sleep(5)
                except Exception as e:
                    log_with_context(outer_stream_lit, {"event": "Error streaming cached document", "key": keys_flow, "query_key": query_key}, source="storage", request_id=request_id, error=str(e))
            return

        async with lock:
            self.partial_results[query_key] = []
            self.complete_results[query_key] = []

            streaming_completed = False
            streaming_error = None

            try:
                await StorageManager.cleanup(f"{query_key}")
                log_with_context(outer_stream_lit, {"event": "Cleaned up old data", "query_key": query_key}, source="live", request_id=request_id)

                events = self.graph_final_summary.stream({"query": f"latest news on {query_key}"}, stream_mode="updates")
                log_with_context(outer_stream_lit, {"event": "Started streaming news agent flow", "query_key": query_key}, source="live", request_id=request_id)

                for event in events:
                    for key, value in event.items():
                        log_with_context(outer_stream_lit, {"event": "Received event key", "key": key}, source="live", request_id=request_id)

                        if key == "__end__":
                            streaming_completed = True
                            log_with_context(outer_stream_lit, {"event": "Reached end of stream", "query_key": query_key}, source="live", request_id=request_id)
                            break

                        if value.get("has_error"):
                            streaming_error = str(value["error_message"])
                            error = {"error": streaming_error}
                            log_with_context(outer_stream_lit, {"event": "Streaming error", "query_key": query_key}, source="live", request_id=request_id, error=streaming_error)
                            yield f"data:{json.dumps(error)}\n\n"
                            break

                        if key in event_node_map:
                            try:
                                result_value = (
                                    [item if isinstance(item, dict) else item.model_dump()
                                     for item in value[event_node_map[key]]]
                                    if isinstance(value[event_node_map[key]], list)
                                    else value[event_node_map[key]].model_dump()
                                )
                            except Exception as e:
                                log_with_context(outer_stream_lit, {"event": "Error extracting result value", "key": key}, source="live", request_id=request_id, error=str(e))
                                result_value = None

                            output = {
                                "node_name": key,
                                "node_result": result_value if key != "crawl_the_news" else ""
                            }

                            yield f"data:{json.dumps(output)}\n\n"
                            log_with_context(outer_stream_lit, {"event": "Yielded streaming data", "node": key}, source="live", request_id=request_id)

                            if key != "crawl_the_news" and result_value is not None:
                                try:
                                    document = {
                                        "genre": f"{query_key}_{key}",
                                        "result": result_value,
                                        "createdAt": datetime.now(timezone.utc)
                                    }
                                    obj = NewsSummaryResult(**document)
                                    self.partial_results[query_key].append(obj)
                                    self.complete_results[query_key].append(obj)
                                except Exception as e:
                                    log_with_context(outer_stream_lit, {"event": "Failed to create/store NewsSummaryResult", "key": key}, source="live", request_id=request_id, error=str(e))

                            if key == "final_genre_summary":
                                streaming_completed = True
                                log_with_context(outer_stream_lit, {"event": "streaming is completed successfully", "node": key}, source="live", request_id=request_id)

                        await asyncio.sleep(0.5)

                    if streaming_completed or streaming_error:
                        break

            except Exception as e:
                streaming_error = str(e)
                error = {"error": streaming_error}
                yield f"data:{json.dumps(error)}\n\n"
                log_with_context(outer_stream_lit, {"event": "Streaming error", "query_key": query_key}, source="live", request_id=request_id, error=streaming_error)
                try:
                    await StorageManager.cleanup(f"{query_key}")
                    log_with_context(outer_stream_lit, {"event": "Cleanup after streaming error", "query_key": query_key}, source="undecided", request_id=request_id)
                except Exception as cleanup_err:
                    log_with_context(outer_stream_lit, {"event": "Cleanup failed after streaming error", "query_key": query_key}, source="undecided", request_id=request_id , error=str(cleanup_err))

            finally:
                if streaming_completed and not streaming_error and (query_key in self.complete_results):
                    try:
                        for obj in self.complete_results[query_key]:
                            await StorageManager.insert_document(obj)
                        
                        log_with_context(outer_stream_lit, {"event": "Successfully saved results", "count": len(self.complete_results[query_key]), "query_key": query_key}, source="undecided", request_id=request_id)
                    except Exception as e:
                        log_with_context(outer_stream_lit, {"event": "Failed to store results", "query_key": query_key}, source="undecided", request_id=request_id , error=str(e))
                else:
                    if streaming_error:
                        log_with_context(outer_stream_lit, {"event": "Not saving results due to streaming error", "query_key": query_key}, source="undecided", 
                                         request_id=request_id , error=streaming_error)
                    else:
                        log_with_context(outer_stream_lit, {"event": "Not saving results - streaming incomplete", "query_key": query_key}, source="undecided", request_id=request_id)

                self.partial_results.pop(query_key, None)
                self.complete_results.pop(query_key, None)
                self.in_progress_queries.pop(query_key, None)
                log_with_context(outer_stream_lit, {"event": "Cleaned up internal state", "query_key": query_key}, source="undecided", request_id=request_id)