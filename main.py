import json
import os
import requests
from datetime import datetime
import pytz

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SHEETY_BEARER_TOKEN = os.environ.get('SHEETY_BEARER_TOKEN')
GEMINI_ENDPOINT = (f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?"
                   f"key={GEMINI_API_KEY}")
SHEETY_ENDPOINT = "https://api.sheety.co/07c36683a7b1d8e6c41890211ffa1d84/personalExpenseTracker/apiInput"
gemini_headers = {'Content-Type': 'application/json'}
sheety_headers = {'Content-Type': 'application/json', 'Authorization': SHEETY_BEARER_TOKEN}
user_input = input("Enter the details of your expense: ")

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
- 'description': A short, concise name for the expense (e.g., 'Coffee', 'Snapp', 'Internet Bill').
- 'category': You MUST categorize the expense into EXACTLY one of these specific options:
'Food', 'Transportation', 'Debt Repayment', 'Subscriptions/Software', 'Healthcare', 'Housing', 'Shopping', or 'Other'.
- 'amount': The numerical cost of the expense as a raw integer. Do not include currency symbols, commas, or decimals.
- 'notes': Any additional context or details mentioned in the text
(e.g., 'from the terminal to the house', 'lunch with friends').
If no extra details are provided, leave as an empty string.

Do not include any markdown formatting, backticks, or conversational text. Just output the raw JSON array.
"""

gemini_payload = {
    "contents": [{
        "parts": [{"text": prompt_text}]
    }]
}

gemini_response = requests.post(url=GEMINI_ENDPOINT, json=gemini_payload, headers=gemini_headers)
data = gemini_response.json()
# data = {'candidates': [{'content': {'parts': [{'text': '[{"date": "07/10/2026", "description": "Burger",
# "category": "Food", "amount": 200000, "notes": ""}]'}], 'role': 'model'}, 'finishReason': 'STOP', 'index': 0}],
# 'usageMetadata': {'promptTokenCount': 285, 'candidatesTokenCount': 44, 'totalTokenCount': 524, 'promptTokensDetails':
# [{'modality': 'TEXT', 'tokenCount': 285}], 'thoughtsTokenCount': 195, 'serviceTier': 'standard'}, 'modelVersion': 'gemini-2.5-flash',
# 'responseId': '-MBQasWBNK3oz7IPvqy0oQ4'}
gemini_response_json = data['candidates'][0]['content']['parts'][0]['text']
# gemini_response_json = [{"date": "07/10/2026", "description": "Burger", "category": "Food", "amount": 200000, "notes": ""}]
expense = json.loads(gemini_response_json)
row_data = {
    'apiInput': {
        'date': expense[0]["date"],
        'description': expense[0]["description"].title(),
        'category': expense[0]["category"].title(),
        'amount': expense[0]["amount"],
        'notes': expense[0]["notes"]
    }
}

sheety_response = requests.post(url=SHEETY_ENDPOINT, json=row_data, headers=sheety_headers)
sheety_response.raise_for_status()
print(sheety_response.json())
