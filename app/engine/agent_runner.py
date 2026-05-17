import json
from datetime import datetime
from typing import Any

from app.ai.client import complete
from app.engine.tools.http_tool import fetch_url, http_post
from app.engine.tools.extract_tool import ai_extract, ai_analyze
from app.engine.tools.memory_tool import store, retrieve, compare_with_last
from app.engine.tools.sms_tool import send_sms, send_whatsapp
from app.engine.tools.slack_tool import (send_slack_message, send_slack_channel,
                                          read_slack_channel, read_slack_thread, post_slack_reply)
from app.engine.tools.discord_tool import send_discord_message
from app.engine.tools.gmail_tool import (send_email, reply_email, read_emails,
                                          search_emails, mark_read)
from app.engine.tools.google_calendar_tool import (list_events, create_event,
                                                    update_event, delete_event, check_availability)
from app.engine.tools.google_drive_tool import (list_files, upload_file, read_file,
                                                  delete_file, share_file)
from app.engine.tools.google_sheets_tool import (
    read_sheet, append_rows, update_cell, create_sheet, delete_rows, find_and_replace,
    batch_update, format_range, sort_sheet, get_sheet_list, copy_sheet,
)
from app.engine.tools.excel_tool import read_excel, write_excel, create_excel, excel_formula, excel_chart
from app.engine.tools.csv_tool import read_csv, write_csv, filter_csv, sort_csv, aggregate_csv, join_csv
from app.engine.tools.data_tool import summarize_data, detect_anomalies, pivot_table
from app.engine.tools.google_docs_tool import read_doc, create_doc, append_to_doc
from app.engine.tools.github_tool import (github_get_repo, github_list_issues,
                                           github_create_issue, github_comment_issue,
                                           github_get_commits, github_list_prs,
                                           github_get_pr, github_get_pr_status)
from app.engine.tools.notion_tool import (notion_get_page, notion_create_page,
                                           notion_update_page, notion_query_database,
                                           notion_create_database_item)
from app.engine.tools.linear_tool import (linear_list_issues, linear_get_issue,
                                           linear_create_issue, linear_update_issue)
from app.engine.tools.jira_tool import (jira_list_issues, jira_create_issue,
                                         jira_update_issue, jira_add_comment, jira_transition_issue)
from app.engine.tools.twitter_tool import (twitter_search_tweets, twitter_get_mentions,
                                            twitter_post_tweet)
from app.engine.tools.airtable_tool import (airtable_list_records, airtable_create_record,
                                             airtable_update_record, airtable_delete_record)
from app.engine.tools.zoom_tool import zoom_list_meetings, zoom_create_meeting, zoom_get_recording
from app.engine.tools.weather_tool import get_weather, get_forecast
from app.engine.tools.search_tool import tavily_search, perplexity_ask, web_search
from app.engine.tools.scraper_tool import scrape_url, fetch_rss

MAX_ITERATIONS = 15

TOOL_SCHEMAS = [
    # ── Web ──────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "fetch_url", "description": "HTTP GET a URL, returns raw text (max 8000 chars)", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "headers": {"type": "object"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "http_post", "description": "HTTP POST to a URL with a JSON body", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "body": {"type": "object"}, "headers": {"type": "object"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "scrape_url", "description": "Fetch a URL and extract clean readable text (strips HTML)", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "fetch_rss", "description": "Parse an RSS/Atom feed and return entries", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["url"]}}},
    # ── AI / Search ───────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "ai_extract", "description": "Extract structured data from text using AI", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "instruction": {"type": "string"}}, "required": ["text", "instruction"]}}},
    {"type": "function", "function": {"name": "ai_analyze", "description": "Answer a question about text using AI", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "question": {"type": "string"}}, "required": ["text", "question"]}}},
    {"type": "function", "function": {"name": "tavily_search", "description": "Search the web using Tavily", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "api_key": {"type": "string"}, "max_results": {"type": "integer", "default": 5}}, "required": ["query", "api_key"]}}},
    {"type": "function", "function": {"name": "perplexity_ask", "description": "Ask Perplexity AI a question and get an answer with citations", "parameters": {"type": "object", "properties": {"question": {"type": "string"}, "api_key": {"type": "string"}}, "required": ["question", "api_key"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the web (provider: tavily or perplexity)", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "api_key": {"type": "string"}, "provider": {"type": "string", "enum": ["tavily", "perplexity"]}}, "required": ["query", "api_key"]}}},
    # ── Memory ────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "store", "description": "Save a value to agent's persistent memory", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {}}, "required": ["key", "value"]}}},
    {"type": "function", "function": {"name": "retrieve", "description": "Read a value from agent's persistent memory", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "compare_with_last", "description": "Compare current value to last stored value, detect changes", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {}}, "required": ["key", "value"]}}},
    # ── SMS / WhatsApp ────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "send_sms", "description": "Send an SMS text message via Twilio", "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "message": {"type": "string"}, "account_sid": {"type": "string"}, "auth_token": {"type": "string"}, "from_number": {"type": "string"}}, "required": ["to", "message", "account_sid", "auth_token", "from_number"]}}},
    {"type": "function", "function": {"name": "send_whatsapp", "description": "Send a WhatsApp message via Twilio", "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "message": {"type": "string"}, "account_sid": {"type": "string"}, "auth_token": {"type": "string"}, "from_number": {"type": "string"}}, "required": ["to", "message", "account_sid", "auth_token", "from_number"]}}},
    # ── Slack ─────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "send_slack_message", "description": "Send a Slack message via incoming webhook URL", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "webhook_url": {"type": "string"}}, "required": ["text", "webhook_url"]}}},
    {"type": "function", "function": {"name": "send_slack_channel", "description": "Post a message to a Slack channel using a bot token", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "channel": {"type": "string"}, "bot_token": {"type": "string"}}, "required": ["text", "channel", "bot_token"]}}},
    {"type": "function", "function": {"name": "read_slack_channel", "description": "Read recent messages from a Slack channel", "parameters": {"type": "object", "properties": {"channel": {"type": "string"}, "bot_token": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["channel", "bot_token"]}}},
    {"type": "function", "function": {"name": "read_slack_thread", "description": "Read replies in a Slack thread", "parameters": {"type": "object", "properties": {"channel": {"type": "string"}, "thread_ts": {"type": "string"}, "bot_token": {"type": "string"}}, "required": ["channel", "thread_ts", "bot_token"]}}},
    {"type": "function", "function": {"name": "post_slack_reply", "description": "Reply to a Slack thread", "parameters": {"type": "object", "properties": {"channel": {"type": "string"}, "thread_ts": {"type": "string"}, "text": {"type": "string"}, "bot_token": {"type": "string"}}, "required": ["channel", "thread_ts", "text", "bot_token"]}}},
    # ── Discord ───────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "send_discord_message", "description": "Send a message to a Discord channel via webhook", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "webhook_url": {"type": "string"}}, "required": ["text", "webhook_url"]}}},
    # ── Gmail ─────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "send_email", "description": "Send a new email via Gmail SMTP", "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}, "gmail_user": {"type": "string"}, "app_password": {"type": "string"}}, "required": ["to", "subject", "body", "gmail_user", "app_password"]}}},
    {"type": "function", "function": {"name": "reply_email", "description": "Reply to an email in-thread via Gmail SMTP", "parameters": {"type": "object", "properties": {"message_id": {"type": "string"}, "reply_body": {"type": "string"}, "gmail_user": {"type": "string"}, "app_password": {"type": "string"}, "to": {"type": "string"}, "subject": {"type": "string"}}, "required": ["message_id", "reply_body", "gmail_user", "app_password"]}}},
    {"type": "function", "function": {"name": "read_emails", "description": "Read emails from Gmail inbox via IMAP", "parameters": {"type": "object", "properties": {"gmail_user": {"type": "string"}, "app_password": {"type": "string"}, "folder": {"type": "string", "default": "INBOX"}, "limit": {"type": "integer", "default": 10}, "unread_only": {"type": "boolean", "default": False}}, "required": ["gmail_user", "app_password"]}}},
    {"type": "function", "function": {"name": "search_emails", "description": "Search Gmail using IMAP query syntax", "parameters": {"type": "object", "properties": {"gmail_user": {"type": "string"}, "app_password": {"type": "string"}, "query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["gmail_user", "app_password", "query"]}}},
    {"type": "function", "function": {"name": "mark_read", "description": "Mark a Gmail message as read", "parameters": {"type": "object", "properties": {"gmail_user": {"type": "string"}, "app_password": {"type": "string"}, "message_id": {"type": "string"}}, "required": ["gmail_user", "app_password", "message_id"]}}},
    # ── Google Calendar ───────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "list_events", "description": "List Google Calendar events", "parameters": {"type": "object", "properties": {"calendar_id": {"type": "string"}, "days_ahead": {"type": "integer", "default": 7}, "service_account_json": {"type": "string"}}, "required": ["calendar_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "create_event", "description": "Create a Google Calendar event", "parameters": {"type": "object", "properties": {"calendar_id": {"type": "string"}, "title": {"type": "string"}, "start_datetime": {"type": "string", "description": "ISO format: 2024-01-15T10:00:00Z"}, "end_datetime": {"type": "string"}, "description": {"type": "string"}, "attendees": {"type": "array", "items": {"type": "string"}}, "service_account_json": {"type": "string"}}, "required": ["calendar_id", "title", "start_datetime", "end_datetime", "service_account_json"]}}},
    {"type": "function", "function": {"name": "update_event", "description": "Update a Google Calendar event", "parameters": {"type": "object", "properties": {"calendar_id": {"type": "string"}, "event_id": {"type": "string"}, "updates": {"type": "object"}, "service_account_json": {"type": "string"}}, "required": ["calendar_id", "event_id", "updates", "service_account_json"]}}},
    {"type": "function", "function": {"name": "delete_event", "description": "Delete a Google Calendar event", "parameters": {"type": "object", "properties": {"calendar_id": {"type": "string"}, "event_id": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["calendar_id", "event_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "check_availability", "description": "Check if a calendar is free/busy in a time range", "parameters": {"type": "object", "properties": {"calendar_id": {"type": "string"}, "start_datetime": {"type": "string"}, "end_datetime": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["calendar_id", "start_datetime", "end_datetime", "service_account_json"]}}},
    # ── Google Drive ──────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "list_files", "description": "List files in a Google Drive folder", "parameters": {"type": "object", "properties": {"folder_id": {"type": "string", "default": "root"}, "service_account_json": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["service_account_json"]}}},
    {"type": "function", "function": {"name": "upload_file", "description": "Upload text content as a file to Google Drive", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "content": {"type": "string"}, "folder_id": {"type": "string", "default": "root"}, "mime_type": {"type": "string", "default": "text/plain"}, "service_account_json": {"type": "string"}}, "required": ["name", "content", "service_account_json"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file from Google Drive (exports Docs/Sheets as text)", "parameters": {"type": "object", "properties": {"file_id": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["file_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "delete_file", "description": "Delete a file from Google Drive", "parameters": {"type": "object", "properties": {"file_id": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["file_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "share_file", "description": "Share a Google Drive file with a user", "parameters": {"type": "object", "properties": {"file_id": {"type": "string"}, "email": {"type": "string"}, "role": {"type": "string", "enum": ["reader", "writer", "owner"], "default": "reader"}, "service_account_json": {"type": "string"}}, "required": ["file_id", "email", "service_account_json"]}}},
    # ── Google Sheets ─────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "read_sheet", "description": "Read rows from a Google Sheet", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "range_": {"type": "string", "description": "e.g. Sheet1!A1:D10"}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "range_", "service_account_json"]}}},
    {"type": "function", "function": {"name": "append_rows", "description": "Append rows to a Google Sheet", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "range_": {"type": "string"}, "rows": {"type": "array", "items": {"type": "array"}}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "range_", "rows", "service_account_json"]}}},
    {"type": "function", "function": {"name": "update_cell", "description": "Update a single cell in a Google Sheet", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "range_": {"type": "string"}, "value": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "range_", "value", "service_account_json"]}}},
    {"type": "function", "function": {"name": "create_sheet", "description": "Create a new Google Spreadsheet with optional headers", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "headers": {"type": "array", "items": {"type": "string"}}, "service_account_json": {"type": "string"}}, "required": ["title", "service_account_json"]}}},
    {"type": "function", "function": {"name": "delete_rows", "description": "Delete rows by index from a Google Sheet", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "start_index": {"type": "integer"}, "end_index": {"type": "integer"}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "sheet_id", "start_index", "end_index", "service_account_json"]}}},
    {"type": "function", "function": {"name": "find_and_replace", "description": "Find and replace text in a Google Sheet", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "find": {"type": "string"}, "replace": {"type": "string"}, "all_sheets": {"type": "boolean", "default": True}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "find", "replace", "service_account_json"]}}},
    {"type": "function", "function": {"name": "batch_update", "description": "Update multiple ranges in a Google Sheet at once", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "updates": {"type": "array", "items": {"type": "object", "properties": {"range": {"type": "string"}, "values": {"type": "array"}}}}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "updates", "service_account_json"]}}},
    {"type": "function", "function": {"name": "format_range", "description": "Apply formatting (bold, background color) to a Google Sheet range", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "range_": {"type": "string"}, "bold": {"type": "boolean"}, "bg_color": {"type": "string", "description": "Hex color e.g. #FF0000"}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "sheet_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "sort_sheet", "description": "Sort a Google Sheet by a column", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "column_index": {"type": "integer"}, "ascending": {"type": "boolean", "default": True}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "sheet_id", "column_index", "service_account_json"]}}},
    {"type": "function", "function": {"name": "get_sheet_list", "description": "List all tab names and IDs in a Google Spreadsheet", "parameters": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["spreadsheet_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "copy_sheet", "description": "Copy a sheet tab to another Google Spreadsheet", "parameters": {"type": "object", "properties": {"source_spreadsheet_id": {"type": "string"}, "dest_spreadsheet_id": {"type": "string"}, "sheet_id": {"type": "integer"}, "service_account_json": {"type": "string"}}, "required": ["source_spreadsheet_id", "dest_spreadsheet_id", "sheet_id", "service_account_json"]}}},
    # ── Excel ─────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "read_excel", "description": "Read rows from an Excel .xlsx file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "sheet_name": {"type": "string"}, "max_rows": {"type": "integer", "default": 1000}}, "required": ["file_path"]}}},
    {"type": "function", "function": {"name": "write_excel", "description": "Write list of dicts to an Excel .xlsx file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "data": {"type": "array", "items": {"type": "object"}}, "sheet_name": {"type": "string", "default": "Sheet1"}}, "required": ["file_path", "data"]}}},
    {"type": "function", "function": {"name": "create_excel", "description": "Create a multi-sheet Excel workbook", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "sheets": {"type": "object", "description": "Dict of sheet_name → list of row dicts"}}, "required": ["file_path", "sheets"]}}},
    {"type": "function", "function": {"name": "excel_formula", "description": "Write a formula to a cell in an Excel file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "cell": {"type": "string"}, "formula": {"type": "string"}, "sheet_name": {"type": "string"}}, "required": ["file_path", "cell", "formula"]}}},
    {"type": "function", "function": {"name": "excel_chart", "description": "Create a chart in an Excel sheet", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "sheet_name": {"type": "string"}, "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]}, "data_range": {"type": "string"}, "title": {"type": "string"}, "position": {"type": "string", "default": "E1"}}, "required": ["file_path", "sheet_name", "chart_type"]}}},
    # ── CSV ───────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "read_csv", "description": "Read rows from a CSV file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "delimiter": {"type": "string", "default": ","}, "encoding": {"type": "string", "default": "utf-8-sig"}, "max_rows": {"type": "integer", "default": 10000}}, "required": ["file_path"]}}},
    {"type": "function", "function": {"name": "write_csv", "description": "Write list of dicts to a CSV file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "data": {"type": "array", "items": {"type": "object"}}, "headers": {"type": "array", "items": {"type": "string"}}}, "required": ["file_path", "data"]}}},
    {"type": "function", "function": {"name": "filter_csv", "description": "Filter rows in a CSV by column value", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "column": {"type": "string"}, "value": {"type": "string"}, "operator": {"type": "string", "enum": ["eq", "ne", "contains", "gt", "lt", "gte", "lte"], "default": "eq"}}, "required": ["file_path", "column", "value"]}}},
    {"type": "function", "function": {"name": "sort_csv", "description": "Sort CSV rows by a column", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "column": {"type": "string"}, "ascending": {"type": "boolean", "default": True}}, "required": ["file_path", "column"]}}},
    {"type": "function", "function": {"name": "aggregate_csv", "description": "Group-by aggregation on a CSV (sum, mean, count, min, max)", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "group_by": {"type": "string"}, "agg_column": {"type": "string"}, "func": {"type": "string", "enum": ["sum", "mean", "count", "min", "max"], "default": "sum"}}, "required": ["file_path", "group_by", "agg_column"]}}},
    {"type": "function", "function": {"name": "join_csv", "description": "Join two CSV files on a common column", "parameters": {"type": "object", "properties": {"file1": {"type": "string"}, "file2": {"type": "string"}, "on_column": {"type": "string"}}, "required": ["file1", "file2", "on_column"]}}},
    # ── Data Analysis ─────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "summarize_data", "description": "Compute min/max/mean/median/std/unique stats for each column", "parameters": {"type": "object", "properties": {"data": {"type": "array", "items": {"type": "object"}}, "columns": {"type": "array", "items": {"type": "string"}}}, "required": ["data"]}}},
    {"type": "function", "function": {"name": "detect_anomalies", "description": "Find outlier rows in a column using z-score", "parameters": {"type": "object", "properties": {"data": {"type": "array", "items": {"type": "object"}}, "column": {"type": "string"}, "threshold": {"type": "number", "default": 2.5}}, "required": ["data", "column"]}}},
    {"type": "function", "function": {"name": "pivot_table", "description": "Create a pivot table from a list of dicts", "parameters": {"type": "object", "properties": {"data": {"type": "array", "items": {"type": "object"}}, "index": {"type": "string"}, "columns": {"type": "string"}, "values": {"type": "string"}, "aggfunc": {"type": "string", "enum": ["sum", "mean", "count", "min", "max"], "default": "sum"}}, "required": ["data", "index", "columns", "values"]}}},
    # ── Google Docs ───────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "read_doc", "description": "Read a Google Doc as plain text", "parameters": {"type": "object", "properties": {"document_id": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["document_id", "service_account_json"]}}},
    {"type": "function", "function": {"name": "create_doc", "description": "Create a new Google Doc", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["title", "service_account_json"]}}},
    {"type": "function", "function": {"name": "append_to_doc", "description": "Append text to an existing Google Doc", "parameters": {"type": "object", "properties": {"document_id": {"type": "string"}, "text": {"type": "string"}, "service_account_json": {"type": "string"}}, "required": ["document_id", "text", "service_account_json"]}}},
    # ── GitHub ────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "github_get_repo", "description": "Get GitHub repository info", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "token": {"type": "string"}}, "required": ["owner", "repo", "token"]}}},
    {"type": "function", "function": {"name": "github_list_issues", "description": "List GitHub issues", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "token": {"type": "string"}, "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"}}, "required": ["owner", "repo", "token"]}}},
    {"type": "function", "function": {"name": "github_create_issue", "description": "Create a GitHub issue", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "token": {"type": "string"}}, "required": ["owner", "repo", "title", "body", "token"]}}},
    {"type": "function", "function": {"name": "github_comment_issue", "description": "Add a comment to a GitHub issue or PR", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "issue_number": {"type": "integer"}, "body": {"type": "string"}, "token": {"type": "string"}}, "required": ["owner", "repo", "issue_number", "body", "token"]}}},
    {"type": "function", "function": {"name": "github_get_commits", "description": "Get recent commits from a GitHub repo", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "token": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["owner", "repo", "token"]}}},
    {"type": "function", "function": {"name": "github_list_prs", "description": "List pull requests in a GitHub repo", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "token": {"type": "string"}, "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"}}, "required": ["owner", "repo", "token"]}}},
    {"type": "function", "function": {"name": "github_get_pr", "description": "Get GitHub PR details", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}, "token": {"type": "string"}}, "required": ["owner", "repo", "pr_number", "token"]}}},
    {"type": "function", "function": {"name": "github_get_pr_status", "description": "Get CI check status for a GitHub PR", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}, "token": {"type": "string"}}, "required": ["owner", "repo", "pr_number", "token"]}}},
    # ── Notion ────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "notion_get_page", "description": "Get a Notion page", "parameters": {"type": "object", "properties": {"page_id": {"type": "string"}, "token": {"type": "string"}}, "required": ["page_id", "token"]}}},
    {"type": "function", "function": {"name": "notion_create_page", "description": "Create a Notion page", "parameters": {"type": "object", "properties": {"parent_id": {"type": "string"}, "title": {"type": "string"}, "content": {"type": "string"}, "token": {"type": "string"}}, "required": ["parent_id", "title", "token"]}}},
    {"type": "function", "function": {"name": "notion_update_page", "description": "Update Notion page properties", "parameters": {"type": "object", "properties": {"page_id": {"type": "string"}, "properties": {"type": "object"}, "token": {"type": "string"}}, "required": ["page_id", "properties", "token"]}}},
    {"type": "function", "function": {"name": "notion_query_database", "description": "Query a Notion database", "parameters": {"type": "object", "properties": {"database_id": {"type": "string"}, "filter_json": {"type": "object"}, "token": {"type": "string"}}, "required": ["database_id", "token"]}}},
    {"type": "function", "function": {"name": "notion_create_database_item", "description": "Create a new item in a Notion database", "parameters": {"type": "object", "properties": {"database_id": {"type": "string"}, "properties": {"type": "object"}, "token": {"type": "string"}}, "required": ["database_id", "properties", "token"]}}},
    # ── Linear ────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "linear_list_issues", "description": "List Linear issues for a team", "parameters": {"type": "object", "properties": {"team_id": {"type": "string"}, "state": {"type": "string", "default": "started"}, "token": {"type": "string"}}, "required": ["team_id", "token"]}}},
    {"type": "function", "function": {"name": "linear_get_issue", "description": "Get a Linear issue by ID", "parameters": {"type": "object", "properties": {"issue_id": {"type": "string"}, "token": {"type": "string"}}, "required": ["issue_id", "token"]}}},
    {"type": "function", "function": {"name": "linear_create_issue", "description": "Create a Linear issue", "parameters": {"type": "object", "properties": {"team_id": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "integer", "default": 0}, "token": {"type": "string"}}, "required": ["team_id", "title", "token"]}}},
    {"type": "function", "function": {"name": "linear_update_issue", "description": "Update a Linear issue", "parameters": {"type": "object", "properties": {"issue_id": {"type": "string"}, "updates": {"type": "object"}, "token": {"type": "string"}}, "required": ["issue_id", "updates", "token"]}}},
    # ── Jira ──────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "jira_list_issues", "description": "Search Jira issues with JQL", "parameters": {"type": "object", "properties": {"jql": {"type": "string"}, "base_url": {"type": "string"}, "email": {"type": "string"}, "api_token": {"type": "string"}}, "required": ["jql", "base_url", "email", "api_token"]}}},
    {"type": "function", "function": {"name": "jira_create_issue", "description": "Create a Jira issue", "parameters": {"type": "object", "properties": {"project_key": {"type": "string"}, "summary": {"type": "string"}, "description": {"type": "string"}, "issue_type": {"type": "string", "default": "Task"}, "base_url": {"type": "string"}, "email": {"type": "string"}, "api_token": {"type": "string"}}, "required": ["project_key", "summary", "base_url", "email", "api_token"]}}},
    {"type": "function", "function": {"name": "jira_add_comment", "description": "Add a comment to a Jira issue", "parameters": {"type": "object", "properties": {"issue_key": {"type": "string"}, "comment": {"type": "string"}, "base_url": {"type": "string"}, "email": {"type": "string"}, "api_token": {"type": "string"}}, "required": ["issue_key", "comment", "base_url", "email", "api_token"]}}},
    {"type": "function", "function": {"name": "jira_transition_issue", "description": "Move a Jira issue to a new status (e.g. Done, In Progress)", "parameters": {"type": "object", "properties": {"issue_key": {"type": "string"}, "transition_name": {"type": "string"}, "base_url": {"type": "string"}, "email": {"type": "string"}, "api_token": {"type": "string"}}, "required": ["issue_key", "transition_name", "base_url", "email", "api_token"]}}},
    # ── Twitter/X ─────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "twitter_search_tweets", "description": "Search recent tweets", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "bearer_token": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query", "bearer_token"]}}},
    {"type": "function", "function": {"name": "twitter_get_mentions", "description": "Get recent mentions of the authenticated Twitter user", "parameters": {"type": "object", "properties": {"bearer_token": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["bearer_token"]}}},
    {"type": "function", "function": {"name": "twitter_post_tweet", "description": "Post a tweet", "parameters": {"type": "object", "properties": {"text": {"type": "string", "maxLength": 280}, "bearer_token": {"type": "string"}, "api_key": {"type": "string"}, "api_secret": {"type": "string"}, "access_token": {"type": "string"}, "access_secret": {"type": "string"}}, "required": ["text", "bearer_token", "api_key", "api_secret", "access_token", "access_secret"]}}},
    # ── Airtable ──────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "airtable_list_records", "description": "List records from an Airtable table", "parameters": {"type": "object", "properties": {"base_id": {"type": "string"}, "table_name": {"type": "string"}, "api_key": {"type": "string"}, "filter_formula": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["base_id", "table_name", "api_key"]}}},
    {"type": "function", "function": {"name": "airtable_create_record", "description": "Create a record in an Airtable table", "parameters": {"type": "object", "properties": {"base_id": {"type": "string"}, "table_name": {"type": "string"}, "fields": {"type": "object"}, "api_key": {"type": "string"}}, "required": ["base_id", "table_name", "fields", "api_key"]}}},
    {"type": "function", "function": {"name": "airtable_update_record", "description": "Update an Airtable record", "parameters": {"type": "object", "properties": {"base_id": {"type": "string"}, "table_name": {"type": "string"}, "record_id": {"type": "string"}, "fields": {"type": "object"}, "api_key": {"type": "string"}}, "required": ["base_id", "table_name", "record_id", "fields", "api_key"]}}},
    {"type": "function", "function": {"name": "airtable_delete_record", "description": "Delete an Airtable record", "parameters": {"type": "object", "properties": {"base_id": {"type": "string"}, "table_name": {"type": "string"}, "record_id": {"type": "string"}, "api_key": {"type": "string"}}, "required": ["base_id", "table_name", "record_id", "api_key"]}}},
    # ── Zoom ──────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "zoom_list_meetings", "description": "List upcoming Zoom meetings", "parameters": {"type": "object", "properties": {"account_id": {"type": "string"}, "client_id": {"type": "string"}, "client_secret": {"type": "string"}}, "required": ["account_id", "client_id", "client_secret"]}}},
    {"type": "function", "function": {"name": "zoom_create_meeting", "description": "Create a Zoom meeting", "parameters": {"type": "object", "properties": {"topic": {"type": "string"}, "start_time": {"type": "string", "description": "ISO format"}, "duration": {"type": "integer", "description": "minutes"}, "account_id": {"type": "string"}, "client_id": {"type": "string"}, "client_secret": {"type": "string"}}, "required": ["topic", "start_time", "duration", "account_id", "client_id", "client_secret"]}}},
    {"type": "function", "function": {"name": "zoom_get_recording", "description": "Get recordings for a Zoom meeting", "parameters": {"type": "object", "properties": {"meeting_id": {"type": "string"}, "account_id": {"type": "string"}, "client_id": {"type": "string"}, "client_secret": {"type": "string"}}, "required": ["meeting_id", "account_id", "client_id", "client_secret"]}}},
    # ── Weather ───────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "get_weather", "description": "Get current weather for a location", "parameters": {"type": "object", "properties": {"location": {"type": "string"}, "api_key": {"type": "string"}, "units": {"type": "string", "enum": ["metric", "imperial"], "default": "metric"}}, "required": ["location", "api_key"]}}},
    {"type": "function", "function": {"name": "get_forecast", "description": "Get weather forecast for a location", "parameters": {"type": "object", "properties": {"location": {"type": "string"}, "days": {"type": "integer", "default": 5}, "api_key": {"type": "string"}, "units": {"type": "string", "default": "metric"}}, "required": ["location", "api_key"]}}},
    # ── Finish ────────────────────────────────────────────────────────────────
    {"type": "function", "function": {"name": "finish", "description": "Complete the task and return a summary of what was accomplished", "parameters": {"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]}}},
]


async def run_agent(agent_data: dict, input_data: dict = None) -> dict:
    goal = agent_data.get("goal") or agent_data.get("description", "Complete the task")
    memory = agent_data.get("memory", {}).copy()
    credentials = agent_data.get("credentials", {})

    system_msg = f"""You are an autonomous AI agent.

Goal: {goal}

{f'Input: {json.dumps(input_data)}' if input_data else ''}

Use tools to accomplish your goal. Pass credentials from agent config when tools require them.
When done, call finish() with a clear summary. Be efficient — avoid redundant tool calls."""

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "Complete your goal now."},
    ]

    steps = []
    result = None
    status = "success"

    for _ in range(MAX_ITERATIONS):
        response = await complete(messages, tools=TOOL_SCHEMAS)

        if response["content"]:
            messages.append({"role": "assistant", "content": response["content"]})

        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            result = response["content"] or "Task completed."
            break

        for tc in tool_calls:
            tool_name = tc["name"]
            args = tc["arguments"]
            step = {"tool": tool_name, "input": args, "output": None, "ok": True}

            try:
                output = await _dispatch_tool(tool_name, args, memory, credentials)
                step["output"] = output

                if tool_name == "finish":
                    result = args.get("result", "Done")
                    steps.append(step)
                    return {"steps": steps, "result": result, "status": "success", "memory": memory}

            except Exception as e:
                step["output"] = f"Error: {e}"
                step["ok"] = False

            steps.append(step)

            tool_result = json.dumps(step["output"]) if not isinstance(step["output"], str) else step["output"]
            messages.append({"role": "user", "content": f"Tool '{tool_name}' result: {tool_result[:4000]}"})

    if result is None:
        result = "Max iterations reached."
        status = "failed"

    return {"steps": steps, "result": result, "status": status, "memory": memory}


async def _dispatch_tool(name: str, args: dict, memory: dict, credentials: dict) -> Any:
    # ── Web ──────────────────────────────────────────────────────────────────
    if name == "fetch_url":
        return await fetch_url(args["url"], args.get("headers"))
    elif name == "http_post":
        return await http_post(args["url"], args.get("body"), args.get("headers"))
    elif name == "scrape_url":
        return await scrape_url(args["url"])
    elif name == "fetch_rss":
        return await fetch_rss(args["url"], args.get("limit", 10))
    # ── AI / Search ──────────────────────────────────────────────────────────
    elif name == "ai_extract":
        return await ai_extract(args["text"], args["instruction"])
    elif name == "ai_analyze":
        return await ai_analyze(args["text"], args["question"])
    elif name == "tavily_search":
        return await tavily_search(args["query"], args["api_key"], args.get("max_results", 5))
    elif name == "perplexity_ask":
        return await perplexity_ask(args["question"], args["api_key"])
    elif name == "web_search":
        return await web_search(args["query"], args["api_key"], args.get("provider", "tavily"))
    # ── Memory ────────────────────────────────────────────────────────────────
    elif name == "store":
        return store(memory, args["key"], args["value"])
    elif name == "retrieve":
        return retrieve(memory, args["key"])
    elif name == "compare_with_last":
        return compare_with_last(memory, args["key"], args["value"])
    # ── SMS / WhatsApp ────────────────────────────────────────────────────────
    elif name == "send_sms":
        return await send_sms(args["to"], args["message"], args["account_sid"],
                              args["auth_token"], args["from_number"])
    elif name == "send_whatsapp":
        return await send_whatsapp(args["to"], args["message"], args["account_sid"],
                                   args["auth_token"], args["from_number"])
    # ── Slack ─────────────────────────────────────────────────────────────────
    elif name == "send_slack_message":
        return await send_slack_message(args["text"], args["webhook_url"])
    elif name == "send_slack_channel":
        return await send_slack_channel(args["text"], args["channel"], args["bot_token"])
    elif name == "read_slack_channel":
        return await read_slack_channel(args["channel"], args["bot_token"], args.get("limit", 20))
    elif name == "read_slack_thread":
        return await read_slack_thread(args["channel"], args["thread_ts"], args["bot_token"])
    elif name == "post_slack_reply":
        return await post_slack_reply(args["channel"], args["thread_ts"], args["text"], args["bot_token"])
    # ── Discord ───────────────────────────────────────────────────────────────
    elif name == "send_discord_message":
        return await send_discord_message(args["text"], args["webhook_url"])
    # ── Gmail ─────────────────────────────────────────────────────────────────
    elif name == "send_email":
        return await send_email(args["to"], args["subject"], args["body"],
                                args["gmail_user"], args["app_password"])
    elif name == "reply_email":
        return await reply_email(args["message_id"], args["reply_body"],
                                 args["gmail_user"], args["app_password"],
                                 args.get("to", ""), args.get("subject", ""))
    elif name == "read_emails":
        return await read_emails(args["gmail_user"], args["app_password"],
                                 args.get("folder", "INBOX"), args.get("limit", 10),
                                 args.get("unread_only", False))
    elif name == "search_emails":
        return await search_emails(args["gmail_user"], args["app_password"],
                                   args["query"], args.get("limit", 10))
    elif name == "mark_read":
        return await mark_read(args["gmail_user"], args["app_password"], args["message_id"])
    # ── Google Calendar ───────────────────────────────────────────────────────
    elif name == "list_events":
        return await list_events(args["calendar_id"], args.get("days_ahead", 7),
                                 args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "create_event":
        return await create_event(args["calendar_id"], args["title"], args["start_datetime"],
                                  args["end_datetime"], args.get("description", ""),
                                  args.get("attendees", []),
                                  args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "update_event":
        return await update_event(args["calendar_id"], args["event_id"], args["updates"],
                                  args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "delete_event":
        return await delete_event(args["calendar_id"], args["event_id"],
                                  args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "check_availability":
        return await check_availability(args["calendar_id"], args["start_datetime"],
                                        args["end_datetime"],
                                        args.get("service_account_json", credentials.get("google_service_account", "")))
    # ── Google Drive ──────────────────────────────────────────────────────────
    elif name == "list_files":
        return await list_files(args.get("folder_id", "root"),
                                args.get("service_account_json", credentials.get("google_service_account", "")),
                                args.get("limit", 20))
    elif name == "upload_file":
        return await upload_file(args["name"], args["content"], args.get("folder_id", "root"),
                                 args.get("mime_type", "text/plain"),
                                 args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "read_file":
        return await read_file(args["file_id"],
                               args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "delete_file":
        return await delete_file(args["file_id"],
                                 args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "share_file":
        return await share_file(args["file_id"], args["email"], args.get("role", "reader"),
                                args.get("service_account_json", credentials.get("google_service_account", "")))
    # ── Google Sheets ─────────────────────────────────────────────────────────
    elif name == "read_sheet":
        return await read_sheet(args["spreadsheet_id"], args["range_"],
                                args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "append_rows":
        return await append_rows(args["spreadsheet_id"], args["range_"], args["rows"],
                                 args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "update_cell":
        return await update_cell(args["spreadsheet_id"], args["range_"], args["value"],
                                 args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "create_sheet":
        return await create_sheet(args["title"], args.get("headers", []),
                                  args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "delete_rows":
        return await delete_rows(args["spreadsheet_id"], args["sheet_id"],
                                 args["start_index"], args["end_index"],
                                 args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "find_and_replace":
        return await find_and_replace(args["spreadsheet_id"], args["find"], args["replace"],
                                      args.get("all_sheets", True),
                                      args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "batch_update":
        return await batch_update(args["spreadsheet_id"], args["updates"],
                                  args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "format_range":
        return await format_range(args["spreadsheet_id"], args["sheet_id"],
                                  args.get("range_", "A1"), args.get("bold", False),
                                  args.get("bg_color", ""),
                                  args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "sort_sheet":
        return await sort_sheet(args["spreadsheet_id"], args["sheet_id"], args["column_index"],
                                args.get("ascending", True),
                                args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "get_sheet_list":
        return await get_sheet_list(args["spreadsheet_id"],
                                    args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "copy_sheet":
        return await copy_sheet(args["source_spreadsheet_id"], args["dest_spreadsheet_id"],
                                args["sheet_id"],
                                args.get("service_account_json", credentials.get("google_service_account", "")))
    # ── Excel ─────────────────────────────────────────────────────────────────
    elif name == "read_excel":
        return await read_excel(args["file_path"], args.get("sheet_name", ""), args.get("max_rows", 1000))
    elif name == "write_excel":
        return await write_excel(args["file_path"], args["data"], args.get("sheet_name", "Sheet1"))
    elif name == "create_excel":
        return await create_excel(args["file_path"], args["sheets"])
    elif name == "excel_formula":
        return await excel_formula(args["file_path"], args["cell"], args["formula"], args.get("sheet_name", ""))
    elif name == "excel_chart":
        return await excel_chart(args["file_path"], args["sheet_name"], args["chart_type"],
                                 args.get("data_range", ""), args.get("title", ""), args.get("position", "E1"))
    # ── CSV ───────────────────────────────────────────────────────────────────
    elif name == "read_csv":
        return await read_csv(args["file_path"], args.get("delimiter", ","),
                              args.get("encoding", "utf-8-sig"), args.get("max_rows", 10000))
    elif name == "write_csv":
        return await write_csv(args["file_path"], args["data"], args.get("headers"))
    elif name == "filter_csv":
        return await filter_csv(args["file_path"], args["column"], args["value"], args.get("operator", "eq"))
    elif name == "sort_csv":
        return await sort_csv(args["file_path"], args["column"], args.get("ascending", True))
    elif name == "aggregate_csv":
        return await aggregate_csv(args["file_path"], args["group_by"], args["agg_column"], args.get("func", "sum"))
    elif name == "join_csv":
        return await join_csv(args["file1"], args["file2"], args["on_column"])
    # ── Data Analysis ─────────────────────────────────────────────────────────
    elif name == "summarize_data":
        return await summarize_data(args["data"], args.get("columns"))
    elif name == "detect_anomalies":
        return await detect_anomalies(args["data"], args["column"], args.get("threshold", 2.5))
    elif name == "pivot_table":
        return await pivot_table(args["data"], args["index"], args["columns"],
                                 args["values"], args.get("aggfunc", "sum"))
    # ── Google Docs ───────────────────────────────────────────────────────────
    elif name == "read_doc":
        return await read_doc(args["document_id"],
                              args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "create_doc":
        return await create_doc(args["title"], args.get("content", ""),
                                args.get("service_account_json", credentials.get("google_service_account", "")))
    elif name == "append_to_doc":
        return await append_to_doc(args["document_id"], args["text"],
                                   args.get("service_account_json", credentials.get("google_service_account", "")))
    # ── GitHub ────────────────────────────────────────────────────────────────
    elif name == "github_get_repo":
        return await github_get_repo(args["owner"], args["repo"], args["token"])
    elif name == "github_list_issues":
        return await github_list_issues(args["owner"], args["repo"], args["token"], args.get("state", "open"))
    elif name == "github_create_issue":
        return await github_create_issue(args["owner"], args["repo"], args["title"], args["body"], args["token"])
    elif name == "github_comment_issue":
        return await github_comment_issue(args["owner"], args["repo"], args["issue_number"], args["body"], args["token"])
    elif name == "github_get_commits":
        return await github_get_commits(args["owner"], args["repo"], args["token"], args.get("limit", 10))
    elif name == "github_list_prs":
        return await github_list_prs(args["owner"], args["repo"], args["token"], args.get("state", "open"))
    elif name == "github_get_pr":
        return await github_get_pr(args["owner"], args["repo"], args["pr_number"], args["token"])
    elif name == "github_get_pr_status":
        return await github_get_pr_status(args["owner"], args["repo"], args["pr_number"], args["token"])
    # ── Notion ────────────────────────────────────────────────────────────────
    elif name == "notion_get_page":
        return await notion_get_page(args["page_id"], args["token"])
    elif name == "notion_create_page":
        return await notion_create_page(args["parent_id"], args["title"], args.get("content", ""), args["token"])
    elif name == "notion_update_page":
        return await notion_update_page(args["page_id"], args["properties"], args["token"])
    elif name == "notion_query_database":
        return await notion_query_database(args["database_id"], args.get("filter_json"), args["token"])
    elif name == "notion_create_database_item":
        return await notion_create_database_item(args["database_id"], args["properties"], args["token"])
    # ── Linear ────────────────────────────────────────────────────────────────
    elif name == "linear_list_issues":
        return await linear_list_issues(args["team_id"], args.get("state", "started"), args["token"])
    elif name == "linear_get_issue":
        return await linear_get_issue(args["issue_id"], args["token"])
    elif name == "linear_create_issue":
        return await linear_create_issue(args["team_id"], args["title"],
                                         args.get("description", ""), args.get("priority", 0), args["token"])
    elif name == "linear_update_issue":
        return await linear_update_issue(args["issue_id"], args["updates"], args["token"])
    # ── Jira ──────────────────────────────────────────────────────────────────
    elif name == "jira_list_issues":
        return await jira_list_issues(args["jql"], args["base_url"], args["email"], args["api_token"])
    elif name == "jira_create_issue":
        return await jira_create_issue(args["project_key"], args["summary"],
                                       args.get("description", ""), args.get("issue_type", "Task"),
                                       args["base_url"], args["email"], args["api_token"])
    elif name == "jira_add_comment":
        return await jira_add_comment(args["issue_key"], args["comment"],
                                      args["base_url"], args["email"], args["api_token"])
    elif name == "jira_transition_issue":
        return await jira_transition_issue(args["issue_key"], args["transition_name"],
                                           args["base_url"], args["email"], args["api_token"])
    # ── Twitter/X ─────────────────────────────────────────────────────────────
    elif name == "twitter_search_tweets":
        return await twitter_search_tweets(args["query"], args["bearer_token"], args.get("limit", 10))
    elif name == "twitter_get_mentions":
        return await twitter_get_mentions(args["bearer_token"], args.get("limit", 10))
    elif name == "twitter_post_tweet":
        return await twitter_post_tweet(args["text"], args["bearer_token"], args["api_key"],
                                        args["api_secret"], args["access_token"], args["access_secret"])
    # ── Airtable ──────────────────────────────────────────────────────────────
    elif name == "airtable_list_records":
        return await airtable_list_records(args["base_id"], args["table_name"], args["api_key"],
                                           args.get("filter_formula", ""), args.get("limit", 20))
    elif name == "airtable_create_record":
        return await airtable_create_record(args["base_id"], args["table_name"], args["fields"], args["api_key"])
    elif name == "airtable_update_record":
        return await airtable_update_record(args["base_id"], args["table_name"],
                                            args["record_id"], args["fields"], args["api_key"])
    elif name == "airtable_delete_record":
        return await airtable_delete_record(args["base_id"], args["table_name"],
                                            args["record_id"], args["api_key"])
    # ── Zoom ──────────────────────────────────────────────────────────────────
    elif name == "zoom_list_meetings":
        return await zoom_list_meetings(args["account_id"], args["client_id"], args["client_secret"])
    elif name == "zoom_create_meeting":
        return await zoom_create_meeting(args["topic"], args["start_time"], args["duration"],
                                         args["account_id"], args["client_id"], args["client_secret"])
    elif name == "zoom_get_recording":
        return await zoom_get_recording(args["meeting_id"], args["account_id"],
                                        args["client_id"], args["client_secret"])
    # ── Weather ───────────────────────────────────────────────────────────────
    elif name == "get_weather":
        return await get_weather(args["location"], args["api_key"], args.get("units", "metric"))
    elif name == "get_forecast":
        return await get_forecast(args["location"], args.get("days", 5),
                                  args["api_key"], args.get("units", "metric"))
    elif name == "finish":
        return args.get("result", "Done")
    else:
        raise ValueError(f"Unknown tool: {name}")
