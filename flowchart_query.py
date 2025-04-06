import json
import os

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
    file_path = os.path.join(flowchart_dir, f"{major_name.lower()}.json")

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

if __name__ == "__main__":
    # Example test: get Year 1 Fall courses for Computer Science
    major = "computer_science"
    year = "Year 4"
    semester = "Fall"
    flowchart_dir = "./flowchart"  # <-- use your actual folder name

    courses = get_major_courses(major, year, semester, flowchart_dir)

    for course in courses:
        subj = course.get("subject", "N/A")  # Default to 'N/A' if subject is missing
        num = course.get("courseNumber", "N/A")  # Default to 'N/A' if course number is missing
        title = course.get("title", "Untitled")  # Always print title
        
        # For electives without a subject/course number, print only the title
        if subj == "N/A" and num == "N/A":
            print(f"{title}")  # Just print the title for electives without subject/course number
        else:
            print(f"{subj} {num} - {title}") 