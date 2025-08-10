import json
import threading
import time
import csv
import os
from openai import OpenAI
import ollama 
import re

client = OpenAI(api_key="")

def check_for_event_file():
    if not os.path.exists("reminders.csv"):
        with open("reminders.csv", "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Event Name", "Time"])

def set_timer(seconds):
    def timer_thread():
        print(f"⏳ Timer set for {seconds} seconds.")
        time.sleep(seconds)
        print("⏰ Timer finished!")
    t = threading.Thread(target=timer_thread)
    t.start()
    
def add_event(name, time):
    check_for_event_file()
    
    with open("reminders.csv", "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([name, time])
        
    print("Added reminder to list")

def chat_with_gpt(user_input):
    seconds = time.time()
    current_date = time.ctime(seconds)
    
    prompt = """
            You are a voice assistant command parser. If the user says something like 'set a timer for 5 minutes', 
            respond with JSON like this: {\"function\": \"set_timer\", \"args\": [300]} or if they say something like 'set a reminder for a doctor's appointment on May 19th at 10 am',
            respond with JSON like this: {\"function\": \"add_event\", \"args\": ["Doctors Appointment", "May 19 10:00:00 2025"]}. If no day is provided, use the current date, and if no time is provided, use 12pm, 
            but always ensure you use the same time format.
            If the input is a question or a general prompt, respond with a short and direct sentence that includes the original phrasing from the user's input.

            For example:
            - Input: "What is 2 + 2?" → Output: "2 + 2 is 4."
            - Input: "What's the capital of France?" → Output: "The capital of France is Paris."
            - Input: "How many seconds are in a minute?" → Output: "There are 60 seconds in a minute."

            Avoid adding extra commentary or explanation. Only rephrase the input question as a complete sentence with the correct answer inserted.
        """ + f"\n Current Date is: {current_date}"
    response = client.chat.completions.create(
        model ="gpt-3.5-turbo",  
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
    )

    result = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(result)
        function_name = parsed.get("function")
        args = parsed.get("args", [])

        if function_name == "set_timer":
            set_timer(*args)
            return "Timer function called"
        elif function_name == "add_event":
            add_event(*args)
            return "Reminder function called"
        else:
            print(f"Unknown function: {function_name}")
    except json.JSONDecodeError:
        return result
    
def chat_with_deepseek(user_input):
    seconds = time.time()
    current_date = time.ctime(seconds)
    
    prompt = """
            You are a voice assistant command parser. If the user says something like 'set a timer for 5 minutes', 
            respond with JSON like this: {\"function\": \"set_timer\", \"args\": [300]} or if they say something like 'set a reminder for a doctor's appointment on May 19th at 10 am',
            respond with JSON like this: {\"function\": \"add_event\", \"args\": ["Doctors Appointment", "May 19 10:00:00 2025"]}. If no day is provided, use the current date, and if no time is provided, use 12pm, 
            but always ensure you use the same time format.
            If the input is a question or a general prompt, respond with a short and direct sentence that includes the original phrasing from the user's input.

            For example:
            - Input: "What is 2 + 2?" → Output: "2 + 2 is 4."
            - Input: "What's the capital of France?" → Output: "The capital of France is Paris."
            - Input: "How many seconds are in a minute?" → Output: "There are 60 seconds in a minute."

            Avoid adding extra commentary or explanation. Only rephrase the input question as a complete sentence with the correct answer inserted.
        """ + f"\n Current Date is: {current_date}"
    try:
        response = ollama.chat(
            model ='deepseek-r1',
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ]
        )
    except Exception as e:
        return f"Error contacting DeepSeek: {e}"

    result = response['message']['content']
    result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()


    try:
        parsed = json.loads(result)
        function_name = parsed.get("function")
        args = parsed.get("args", [])

        if function_name == "set_timer":
            set_timer(*args)
            return "Timer function called"
        elif function_name == "add_event":
            add_event(*args)
            return "Reminder function called"
        else:
            print(f"Unknown function: {function_name}")
    except json.JSONDecodeError:
        return result

    
  

if __name__ == "__main__":
    user_input = input("You: ")
    result = chat_with_gpt(user_input)

    try:
        parsed = json.loads(result)
        function_name = parsed.get("function")
        args = parsed.get("args", [])

        if function_name == "set_timer":
            set_timer(*args)
        elif function_name == "add_event":
            add_event(*args)
        else:
            print(f"Unknown function: {function_name}")
    except json.JSONDecodeError:
        print("🤖 GPT:", result)
