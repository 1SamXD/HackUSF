import requests
import time
import subprocess

import json
import os
def start_ollama():
    try:
        # Try to see if Ollama is already running
        response = requests.get("http://localhost:11434")
        if response.status_code == 200:
            print("Ollama is already running.")
            return
    except requests.exceptions.ConnectionError:
        pass  # Not running, so we start it

    # Start Ollama as a background process
    print("Starting Ollama...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait a few seconds to let it boot up
    for _ in range(10):
        try:
            response = requests.get("http://localhost:11434")
            if response.status_code == 200:
                print("Ollama started.")
                return
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    raise RuntimeError("Failed to start Ollama.")

def query_deepseek(prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "gemma3",  # or whatever tag/version you downloaded
        "prompt": prompt,
        "stream": False # Set to True for streaming responses
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['response']
    else:
        print(f"Error: {response.status_code}")
        return None

# Example usage
user_input = '''    only respond with the json. do not say your reasoning
    
    
    Extract the following information from the student query:
    1. Academic year (1st year, 2nd year, 3rd year, 4th year as 1, 2, 3, 4 respectively) -> Integer
    2. Major (whatever they input try to figure out the real name) -> string
    3. Semester (fall, spring, summer) ->string
    
    Query: i am a second year student in computer science spring semester i need help signing up for fall semester

    if no relevant information can be extracted for a specific part, then ignore that section and put in null there

    Format your response as JSON:
    {{
      "year": "...",
      "major": "...",
      "semester": "..."
    }}
    
    only respond with the json. do not say anything else.'''


start_ollama()
response = query_deepseek(user_input)
print(response)
