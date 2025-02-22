import google.generativeai as genai
import yaml
import json
from datetime import datetime

# Load API key from config.yaml
api_key = None
CONFIG_PATH = r"config.yaml"

with open(CONFIG_PATH) as file:
    data = yaml.load(file, Loader=yaml.FullLoader)
    api_key = data['GEMINI_API_KEY']

# Configure Gemini API
genai.configure(api_key=api_key)

def ats_extractor(resume_data):
    prompt = '''
    You are an AI bot designed to act as a professional for parsing resumes. You are given a resume, and your job is to extract the following information:
    1. Full name
    2. Email ID
    3. GitHub portfolio
    4. LinkedIn ID
    5. Employment details (include company, position, duration, and key responsibilities)
    6. Education details (include institution, degree, graduation year)
    7. Technical skills (categorize by proficiency if possible)
    8. Soft skills
    9. Certifications and courses
    10. Projects (with brief descriptions)
    
    IMPORTANT: You must respond with VALID JSON only, with no additional text before or after. Format your response as follows:
    {
      "full_name": "Example Name",
      "email": "example@email.com",
      "github": "github.com/example",
      "linkedin": "linkedin.com/in/example",
      "employment": [
        {"company": "Example Corp", "position": "Software Engineer", "duration": "2020-2022", "responsibilities": ["Developed web applications", "Led team of 3 developers"]}
      ],
      "education": [
        {"institution": "Example University", "degree": "Bachelor of Science in Computer Science", "year": "2019"}
      ],
      "technical_skills": {
        "expert": ["Python", "JavaScript"],
        "intermediate": ["SQL", "React"],
        "beginner": ["Docker", "AWS"]
      },
      "soft_skills": ["Communication", "Leadership", "Problem Solving"],
      "certifications": ["AWS Certified Developer", "Scrum Master Certification"],
      "projects": [
        {"name": "E-commerce Platform", "description": "Built full-stack e-commerce site using React and Node.js"}
      ]
    }
    '''

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"{prompt}\n\nResume:\n{resume_data}")
    
    try:
        response_text = response.text
        # Validate JSON by parsing it
        json.loads(response_text)
        return response_text
    except (json.JSONDecodeError, AttributeError):
        # Fallback JSON structure
        fallback_response = {
            "parsing_error": True,
            "message": "Could not extract structured information from resume",
            "raw_response": getattr(response, 'text', str(response))
        }
        return json.dumps(fallback_response)

def job_match_analysis(resume_data, job_title, job_description):
    # Input validation
    if not all([resume_data, job_title, job_description]):
        return json.dumps({
            "error": "Missing required input data",
            "match_score": 0,
            "detailed_scoring": {
                "must_have_requirements": [],
                "important_requirements": [],
                "nice_to_have_requirements": []
            },
            "key_matches": [],
            "missing_skills": [],
            "resume_improvement": [],
            "keyword_optimization": [],
            "interview_prep": []
        })

    prompt = f'''
    Analyze this resume against the job requirements and provide a JSON response with no additional text:
    {{
        "match_score": <number 0-100>,
        "detailed_scoring": {{
            "must_have_requirements": [
                {{
                    "skill": "required skill",
                    "points_earned": 6,
                    "points_possible": 6,
                    "explanation": "why this score"
                }}
            ],
            "important_requirements": [
                {{
                    "skill": "important skill",
                    "points_earned": 4,
                    "points_possible": 4,
                    "explanation": "why this score"
                }}
            ],
            "nice_to_have_requirements": [
                {{
                    "skill": "nice to have skill",
                    "points_earned": 2,
                    "points_possible": 2,
                    "explanation": "why this score"
                }}
            ]
        }},
        "key_matches": ["matching skill 1", "matching skill 2"],
        "missing_skills": [
            {{
                "skill": "missing skill",
                "importance": "high/medium/low",
                "course_recommendation": "course name"
            }}
        ],
        "resume_improvement": [
            {{
                "section": "section name",
                "recommendation": "improvement suggestion"
            }}
        ],
        "keyword_optimization": [
            {{
                "current": "current term",
                "suggested": "better term"
            }}
        ],
        "interview_prep": ["prep tip 1", "prep tip 2"]
    }}

    Resume:
    {resume_data}

    Job Title: {job_title}
    Job Description: {job_description}
    '''

    try:
        # Generate response using Gemini
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        
        if not response or not hasattr(response, 'text'):
            raise ValueError("Invalid response from Gemini API")

        # Clean the response text
        response_text = response.text.strip()
        
        # Try to find JSON in the response if it's not already valid JSON
        if not response_text.startswith('{'):
            import re
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
        # Parse the response
        parsed_response = json.loads(response_text)
        
        # Ensure match_score exists and is valid
        if 'match_score' not in parsed_response:
            total_points = 0
            total_possible = 0
            
            for category in ['must_have_requirements', 'important_requirements', 'nice_to_have_requirements']:
                if category in parsed_response.get('detailed_scoring', {}):
                    for req in parsed_response['detailed_scoring'][category]:
                        total_points += req.get('points_earned', 0)
                        total_possible += req.get('points_possible', 0)
            
            parsed_response['match_score'] = round((total_points / total_possible) * 100) if total_possible > 0 else 0

        return json.dumps(parsed_response)

    except Exception as e:
        print(f"Error in job match analysis: {str(e)}")
        return json.dumps({
            "error": f"Analysis failed: {str(e)}",
            "match_score": 0,
            "detailed_scoring": {
                "must_have_requirements": [],
                "important_requirements": [],
                "nice_to_have_requirements": []
            },
            "key_matches": [],
            "missing_skills": [],
            "resume_improvement": [],
            "keyword_optimization": [],
            "interview_prep": []
        })

# Example inputs
resume_data = "Experienced Python developer with a background in web development and UI/UX design. Proficient in JavaScript, React, and front-end frameworks. Passionate about building interactive user experiences."
job_title = "Data Scientist"
job_description = "We are looking for a skilled data scientist with expertise in Python, data analysis, machine learning, and cloud computing."

# Run the analysis
result = job_match_analysis(resume_data, job_title, job_description)

# Convert response to JSON format
try:
    parsed_result = json.loads(result)
    print(json.dumps(parsed_result, indent=4))
except json.JSONDecodeError:
    print("Error: Response could not be converted to JSON. Raw output below:")
    print(result)

def generate_career_path(resume_data, target_role=None):
    prompt = f'''
    You are a career development expert. Based on the provided resume data, suggest potential career paths 
    and growth opportunities. {f"The candidate is specifically interested in progressing toward a {target_role} role." if target_role else ""}
    
    Resume data:
    {resume_data}
    
    Provide guidance in the following JSON format:
    {{
      "current_level": "Mid-level Software Engineer",
      "potential_paths": [
        {{
          "path": "Technical Leadership Track",
          "next_role": "Senior Software Engineer",
          "timeline": "1-2 years",
          "required_skills": ["System design", "Mentoring", "Project management"],
          "recommended_resources": [
            {{
              "type": "course",
              "name": "System Design Interview",
              "link": "https://www.educative.io/courses/grokking-the-system-design-interview"
            }}
          ]
        }}
      ],
      "skill_development_plan": {{
        "technical": [
          {{
            "skill": "Cloud Architecture",
            "resources": ["AWS Solutions Architect course", "Hands-on projects with serverless"]
          }}
        ],
        "soft_skills": [
          {{
            "skill": "Leadership",
            "resources": ["Join Toastmasters", "Take on team lead responsibilities in current role"]
          }}
        ]
      }}
    }}
    
    IMPORTANT: Return VALID JSON only with no preamble or additional text.
    '''

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    
    try:
        response_text = response.text
        # Validate JSON by parsing it
        json.loads(response_text)
        return response_text
    except (json.JSONDecodeError, AttributeError):
        # Fallback JSON structure
        fallback_response = {
            "analysis_error": True,
            "message": "Could not generate career path analysis",
            "raw_response": getattr(response, 'text', str(response))
        }
        return json.dumps(fallback_response)

def generate_resume_suggestions(resume_data):
    prompt = f'''
    You are an expert resume writer and career coach. Analyze the provided resume data and provide specific, actionable 
    suggestions to improve its effectiveness for modern ATS systems and hiring managers.
    
    Resume data:
    {resume_data}
    
    Provide detailed improvement suggestions in the following JSON format:
    {{
      "overall_assessment": "The resume is structured well but lacks quantifiable achievements",
      "content_improvements": [
        {{
          "section": "Professional Summary",
          "issue": "Too generic and lacks specific expertise highlights",
          "suggestion": "Begin with '10+ years experienced software engineer specializing in financial systems and machine learning applications'",
          "example": "Senior Software Engineer with 10+ years of experience building high-performance financial systems that process $10M+ in daily transactions. Specialized in ML-driven fraud detection systems that reduced false positives by 35%."
        }}
      ],
      "formatting_suggestions": [
        {{
          "issue": "Dense text blocks are difficult to scan",
          "suggestion": "Use bullet points limited to 2 lines each for achievements"
        }}
      ],
      "ats_optimization": [
        {{
          "issue": "Missing key industry keywords",
          "suggestion": "Include terms like 'CI/CD', 'Agile methodology', and 'microservices' where relevant"
        }}
      ],
      "general_tips": [
        "Tailor your resume for each application by mirroring key terms from the job description",
        "Move most relevant experience to the top of each section"
      ]
    }}
    
    IMPORTANT: Return VALID JSON only with no preamble or additional text.
    '''

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    
    try:
        response_text = response.text
        # Validate JSON by parsing it
        json.loads(response_text)
        return response_text
    except (json.JSONDecodeError, AttributeError):
        # Fallback JSON structure
        fallback_response = {
            "analysis_error": True,
            "message": "Could not generate resume improvement suggestions",
            "raw_response": getattr(response, 'text', str(response))
        }
        return json.dumps(fallback_response)