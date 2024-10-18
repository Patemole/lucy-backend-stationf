def LLM_profile_generation(username: str, academic_advisor: str, year: str, university: str, faculty: str, major: str, minor: str):

    print("\n")
    print("\n")
    print(f"Profiling of the user")
    print(f"username: {username}, year: {year}, university: {university}, School: {faculty}, major: {major}, minor: {minor}, academic_advisor: {academic_advisor}")

    try:
        student_profile = f"My name is {username}. I am enrolled at {university} in the {faculty} school. I am majoring in {major} and minoring in {minor}. Currently in my {year} year, I am guided by academic advisor: {academic_advisor}."
        return student_profile
    except Exception as e:
        print(e)