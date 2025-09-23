run the agent directly 
`uv run -m news_agent_flow.flow_graph`

run the rest service
`uv run run.py`

Run Streamlit
`streamlit run front_end_ui/streamlit_app.py`

MongoDB setup
```
brew tap mongodb/brew
brew update
brew search mongodb
```

`brew install mongodb/brew/mongodb-community@7.0`

Start MongoDB
`brew services start mongodb/brew/mongodb-community@7.0`
`brew services restart mongodb-community@7.0`

Check the MongoDB
`brew services list`

Run the command
`mongosh`
Should result something like:
```
Current Mongosh Log ID:	68d23cf369ed84faa2d482a8
Connecting to:		mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.5.8
Using MongoDB:		7.0.24
Using Mongosh:		2.5.8
```
