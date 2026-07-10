import os
import requests
import json
import streamlit as st
from datetime import datetime
import pytz

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SHEETY_BEARER_TOKEN = os.environ.get('SHEETY_BEARER_TOKEN')
GEMINI_ENDPOINT = (f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?"
                   f"key={GEMINI_API_KEY}")
SHEETY_ENDPOINT = "https://api.sheety.co/07c36683a7b1d8e6c41890211ffa1d84/personalExpenseTracker/apiInput"

gemini_headers = {'Content-Type': 'application/json'}
sheety_headers = {'Content-Type': 'application/json', 'Authorization': SHEETY_BEARER_TOKEN}

# --- Streamlit UI ---
st.title("💸 Personal Expense Tracker")

# Replace standard input() with Streamlit's web text input
user_input = st.text_input("Enter the details of your expense:")

# Only run the API logic IF the user clicks the button
if st.button("Log Expense"):
    
    if user_input: # Ensure the input isn't empty
        with st.spinner("Analyzing and logging your expense..."):
            tehran = pytz.timezone("Asia/Tehran")
            date = datetime.now(tehran)
            today_date = date.strftime("%m/%d/%Y")

            prompt_text = f"""
            You are a highly accurate financial data extractor. 
            Read the following text describing an expense: '{user_input}'.
            Extract the expense details and return the data EXACTLY as a valid JSON array of objects. 

            Each object must contain the following keys:
            - 'date': The date of the expense in MM/DD/YYYY format.
            If the text does not specify a date, strictly use today's date: {today_date}.
            - 'description': A short, concise name for the expense.
            - 'category': You MUST categorize the expense into EXACTLY one of these specific options:
            'Food', 'Transportation', 'Debt Repayment', 'Subscriptions/Software', 'Healthcare', 'Housing', 'Shopping', or 'Other'.
            - 'amount': The numerical cost of the expense as a raw integer. Do not include currency symbols, commas, or decimals.
            - 'notes': Any additional context or details mentioned in the text. If no extra details are provided, leave as an empty string.

            Do not include any markdown formatting, backticks, or conversational text. Just output the raw JSON array.
            """

            gemini_payload = {
                "contents": [{
                    "parts": [{"text": prompt_text}]
                }]
            }

            try:
                # 1. Ask Gemini to extract the data
                gemini_response = requests.post(url=GEMINI_ENDPOINT, json=gemini_payload, headers=gemini_headers)
                gemini_response.raise_for_status()
                data = gemini_response.json()
                
                raw_string_from_gemini = data['candidates'][0]['content']['parts'][0]['text']
                gemini_response_json = json.loads(raw_string_from_gemini)

                # 2. Format data for Sheety
                row_data = {
                    'apiInput': {
                        'date': gemini_response_json[0]["date"],
                        'description': gemini_response_json[0]["description"].title(),
                        'category': gemini_response_json[0]["category"].title(),
                        'amount': gemini_response_json[0]["amount"],
                        'notes': gemini_response_json[0]["notes"]
                    }
                }

                # 3. Post to Google Sheets
                sheety_response = requests.post(url=SHEETY_ENDPOINT, json=row_data, headers=sheety_headers)
                sheety_response.raise_for_status()
                
                st.success("Expense successfully added to your Google Sheet!")
                st.json(row_data) # Displays the formatted data neatly on the screen
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please type an expense before clicking the button!")
