import requests
import time
import subprocess
import json
import os
import re
#python -m venv test    creates virtual environment 
#.\test\Scripts\Activate.ps1   activates the virutal environment 
#pip install langchain langchain_ollama ollama    installs libraries for virtual environment 


def start_ollama():
    """Starts the Ollama server if not already running."""
    try:
        response = requests.get("http://localhost:11434")
        if response.status_code == 200:
            print("Ollama is already running.")
            return
    except requests.exceptions.ConnectionError:
        pass

    print("Starting Ollama...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    """Sends a prompt to Ollama model and returns the response."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("response", "")
    print(f"Error: {response.status_code}")
    return None

def extract_json_from_text(text):
    """Attempts to extract JSON from a raw text response."""
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    match = re.search(json_pattern, text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def find_matching_sections(flowchart_courses, live_schedule):
    """Finds available sections in the live schedule that match flowchart courses."""
    matches = []
    for course in flowchart_courses:
        course_subject = course.get("subject", "").upper()
        course_title = course.get("title", "").lower()
        for section in live_schedule:
            section_subject = section.get("subjectDescription", "").split(":")[0].strip().upper()
            section_title = section.get("courseTitle", "").lower()
            if course_subject in section_subject and course_title in section_title:
                matches.append(section)
    return matches

def get_major_courses(major_name, year, semester, flowchart_dir="./flowchart"):
    """Loads the recommended courses for a major from flowchart data."""
    file_path = os.path.join(flowchart_dir, f"{major_name.lower().replace(' ', '_')}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No flowchart data found for {major_name}")
    with open(file_path, "r") as f:
        flowchart = json.load(f)
    courses = flowchart.get(year, {}).get(semester, [])
    return [
        {
            "subject": c.get("subject", "N/A"),
            "courseNumber": c.get("courseNumber", "N/A"),
            "title": c.get("title", "N/A")
        }
        for c in courses
    ]

def parse_days(day_list):
    """Parses a list of weekday names into human-readable format."""
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Ensure days are in a consistent format (capitalize the first letter)
    day_list = [day.capitalize() for day in day_list]
    
    # Filter days that exist in the list
    return [day for day in days_of_week if day in day_list]

def process_user_query(user_query, live_schedule):
    """Processes a user's query to extract academic info and return matching course sections."""
    prompt = f"""
    only respond with the json. do not say your reasoning

    Extract the following information from the student query:
    1. Academic year (1st year, 2nd year, 3rd year, 4th year as 1, 2, 3, 4 respectively) -> Integer
    2. Major (whatever they input try to figure out the real name) -> string
    3. Semester (fall, spring, summer) ->string

    Query: {user_query}

    if no relevant information can be extracted for a specific part, then set that field to null.

    Format your response as JSON:
    {{
      "year": ,
      "major": ,
      "semester":
    }}
    """

    start_ollama()
    llm_response = query_deepseek(prompt)
    print(f"\nRaw LLM response:\n{llm_response}\n")

    try:
        parsed_info = json.loads(llm_response)
    except json.JSONDecodeError:
        parsed_info = extract_json_from_text(llm_response)

    if not parsed_info:
        return "Sorry, I couldn't understand the information. Please provide your academic year, major, and the semester you're interested in clearly."

    print(f"Parsed info: {parsed_info}")

    year = parsed_info.get("year")
    major = parsed_info.get("major")
    semester = parsed_info.get("semester")

    if not year or not major or not semester:
        missing = [key for key in ["year", "major", "semester"] if not parsed_info.get(key)]
        return f"Missing information: {', '.join(missing)}. Please provide your academic year, major, and semester."

    try:
        courses = get_major_courses(major, f"Year {year}", semester.capitalize())
        matching_sections = find_matching_sections(courses, live_schedule)
        if not matching_sections:
            return "I found your recommended courses, but couldn't find any current class sections in the USF registry."

        result = f"Available class sections for Year {year} {semester.capitalize()} in {major}:\n"
        for sec in matching_sections:
            days = ", ".join(parse_days(sec.get("days", [])))  # Pass list directly here
            result += (
                f"- {sec.get('courseTitle')} ({sec.get('courseReferenceNumber')}): {days} "
                f"{sec.get('start')}-{sec.get('end')} in {sec.get('building')} {sec.get('room')}, "
                f"{sec.get('seatsAvailable')} seats available. Email: {sec.get('email')}\n"
            )
        return result
    except FileNotFoundError as e:
        return f"Error: {str(e)}. Please check if your major is supported or try a different spelling."

if __name__ == "__main__":
    live_schedule = []
    subject_json_folder = "./subject_jsons"

    for filename in os.listdir(subject_json_folder):
        if filename.endswith(".json"):
            with open(os.path.join(subject_json_folder, filename), "r") as f:
                try:
                    data = json.load(f)
                    live_schedule.extend(data)
                except json.JSONDecodeError:
                    print(f"Warning: Failed to load {filename}")

    print("Welcome to the USF Course Assistant! Type 'quit' to exit.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        if not user_input:
            continue
        result = process_user_query(user_input, live_schedule)
        print("\nAssistant:", result)
