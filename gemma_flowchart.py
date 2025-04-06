import requests
import time
import subprocess
import json
import os
import re

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

def extract_json_from_text(text):
    """Extract JSON from text that might have additional content around it"""
    # Try to find JSON between curly braces
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    match = re.search(json_pattern, text)
    
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    return None

def get_major_courses(major_name, year, semester, flowchart_dir="./flowchart"):
    """
    Load flowchart data for a given major and return subject+courseNumber
    for a specific year and semester.

    Parameters:
    - major_name: e.g., "computer_science" make sure it is in a similar format 
    - year: e.g., "Year 1" 
    - semester: e.g., "Fall"
    - flowchart_dir: path to JSON major files

    Returns: List of dictionaries with { subject, courseNumber, title }
    """
    # Format the major name (replace spaces with underscores and lowercase)
    major_name = major_name.lower().replace(" ", "_")
    
    file_path = os.path.join(flowchart_dir, f"{major_name}.json")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No flowchart data found for {major_name}")

    with open(file_path, "r") as f:
        flowchart = json.load(f)

    courses = flowchart.get(year, {}).get(semester, [])

    # Include electives even without subject/courseNumber
    valid_courses = [
        {
            "subject": c.get("subject", "N/A"),  # Default to 'N/A' if missing
            "courseNumber": c.get("courseNumber", "N/A"),  # Default to 'N/A' if missing
            "title": c["title"]
        }
        for c in courses
    ]

    return valid_courses

def process_user_query(user_query):
    """Process a user query using the LLM and get recommended courses"""
    
    extraction_prompt = f"""
    only respond with the json. do not say your reasoning
    
    Extract the following information from the student query:
    1. Academic year (1st year, 2nd year, 3rd year, 4th year as 1, 2, 3, 4 respectively) -> Integer
    2. Major (whatever they input try to figure out the real name) -> string
    3. Semester (fall, spring, summer) ->string
    
    Query: {user_query}

    if no relevant information can be extracted for a specific part, then set that field to null.

    Format your response as JSON:
    {{
      "year": 2,
      "major": "computer science",
      "semester": "fall"
    }}
    
    only respond with the json. do not say anything else or add any additional text.
    """
    
    # Get the LLM response
    start_ollama()
    llm_response = query_deepseek(extraction_prompt)
    
    # For debugging: print the raw response
    print(f"\nRaw LLM response:\n{llm_response}\n")
    
    # Try to parse the JSON
    try:
        # First try direct parsing
        parsed_info = json.loads(llm_response)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from text
        parsed_info = extract_json_from_text(llm_response)
        
        if not parsed_info:
            print("Failed to parse JSON from response")
            return "Sorry, I couldn't understand the information. Please provide your academic year, major, and the semester you're interested in clearly."
    
    # Debug the parsed info
    print(f"Parsed info: {parsed_info}")
    
    # Convert year to "Year X" format for the flowchart
    year_num = parsed_info.get("year")
    major = parsed_info.get("major")
    semester = parsed_info.get("semester")
    
    # Check if we have all required information
    if not year_num or not major or not semester:
        missing = []
        if not year_num: missing.append("year")
        if not major: missing.append("major")
        if not semester: missing.append("semester")
        return f"Missing information: {', '.join(missing)}. Please provide your academic year, major, and semester you're interested in."
    
    # Format year for the flowchart lookup
    year_str = f"Year {year_num}"
    
    # Capitalize the first letter of semester
    semester = semester.capitalize()
    
    # Get the courses
    try:
        courses = get_major_courses(major, year_str, semester)
        
        # Format the response
        result = f"Recommended courses for {year_str} {semester} semester in {major}:\n\n"
        
        for course in courses:
            subj = course.get("subject", "N/A")
            num = course.get("courseNumber", "N/A")
            title = course.get("title", "Untitled")
            
            if subj == "N/A" and num == "N/A":
                result += f"- {title}\n"
            else:
                result += f"- {subj} {num} - {title}\n"
        
        return result
        
    except FileNotFoundError as e:
        return f"Error: {str(e)}. Please check if your major is supported or try a different spelling."

# Example usage
if __name__ == "__main__":
    # Test with a sample query
    user_input = "i am a second year student in computer science spring semester i need help signing up for fall semester"
    result = process_user_query(user_input)
    print(result)

    