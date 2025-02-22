# Test the job matching
from resumeparser import job_match_analysis
import json
resume_data = "Experienced Python developer with a background in web development and UI/UX design. Proficient in JavaScript, React, and front-end frameworks."
job_title = "Data Scientist"
job_description = "We are looking for a skilled data scientist with expertise in Python, data analysis, machine learning, and cloud computing."

result = job_match_analysis(resume_data, job_title, job_description)
print(json.dumps(json.loads(result), indent=2))