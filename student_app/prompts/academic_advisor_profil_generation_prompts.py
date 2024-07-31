profile_generation_prompt = """
Create a profile sentence for the student using the provided details. Ensure to include their username, university, faculty, major, minor, year, and academic advisor.
example of profile:
The student {username} is enrolled at {university} in the {faculty} school. She/he is  are majoring in {major} and minoring in {minor}. Currently in his {year} year, He/she is guided by academic advisor: {academic_advisor}.
[Instruction]
NEVER PUT ANYTHING ELSE THAN THE PROFILE, no greetings or introduction or conclusion of the response just the profile
"""