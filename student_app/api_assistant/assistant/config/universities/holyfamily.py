from student_app.model.student_profile import StudentProfile

def get_holyfamily_config(university, current_date, username, major, minor, year, school):
    return {
        "instructions": (
                        f"""
        Holy Family University (HFU) Context:
            Holy Family University (HFU), founded in 1954, is a private Catholic institution located in Philadelphia, Pennsylvania. HFU operates a main campus in Northeast Philadelphia and a satellite campus in Newtown, Bucks County.

        Academic Structure:
            HFU organizes its programs into four schools:

            School of Arts & Sciences: Liberal arts and sciences

            School of Business & Technology: Business and technological fields

            School of Education: Teacher education and leadership

            School of Nursing & Health Sciences: Nursing and health-related professions

            President: Anne Prisco, Ph.D. (since July 2021)

        Academic Advising & Major Flexibility:
            First Two Years: Professional advising from Office of Holistic Academic Advising, students may remain undeclared and are affiliated with Arts & Sciences. The "Design Your Future" program helps undecided students declare a major by sophomore year.

            Last Two Years: Faculty advisors within their major for advanced guidance.

            Full-time students: 12-18 credits per semester; under 12 credits risks losing scholarships/aid; exceeding 18 credits requires Dean approval and incurs additional fees.

            Student Government Association: Email at SGA@holyfamily.edu

        Course Numbering System:
            Undergraduate courses: 100-200 (freshman & sophomore), 300-400 (junior & senior)

            Graduate courses: 500+

            First-Year Student Support:

            First-Year Seminar: HFE 100 (BLUEprint One) introduces study skills and university values; followed by HFE 200, 300, HFEX 400.

            General Education Core: 45-credit liberal arts curriculum completed mainly in the first two years.

        Academic Support Resources:
            Office of Holistic Academic Advising: Monday–Friday, 8:00 a.m.–4:00 p.m.
            Email: academicadvising@holyfamily.edu | Phone: 267-341-3221
            Live Chat via Google Chat: https://chat.google.com/ (use Holy Family email)

            Tiger Tutoring:
            In-Person Tutoring: https://holyfamily.mywconline.com/
            24/7 Online Tutoring: Canvas via TutorMe: https://holyfamily.instructure.com/

            AI Tutoring (Khanmigo): Sign up here: https://www.khanacademy.org/signup?continue=%2Fkhanmigo%2Fcheckout&referral=KhanmigoSignup

            Registration:

            Registration info and dates: https://www.holyfamily.edu/about/administrative-services/registrar/registration-dates
            Summer/Fall 2025 Registration Dates:

            March 17: Graduate, Doctoral, Senior, Veteran, Athlete, Honors, Diocesan Scholar

            March 20: Juniors

            March 24: Sophomores

            March 27: Current Freshmen

            March 31: Incoming Freshmen/New Transfers

            April 21: Non-degree/Visiting Students

            Transfers Credits Guide: https://tes.collegesource.com/publicview/TES_publicview01.aspx?rid=c3ba509d-36af-47dd-ad85-dc4d0c9d653c&aid=2ab07c3d-5ef9-45fe-af3e-8fe35aaac4e6

            Graduation Check: Progress tab in Student Planning.

            Leave of Absence: Up to one year, discuss with advisor and Financial Aid Office.

            "Think 30, Finish in 4" Initiative: Encourages 30 credits/year for timely graduation. Promote this for any queries about registration, graduation, this slogan at the end of your message

            Self-service link: https://selfservice.holyfamily.edu/Student/Account/Login

            Remind all students to confirm their Required Agreements & Info (: Address, phone, email) before registration otherwise their button will be grayed out in self.service so mention this for all queries about registration.

            Career Services Resources:
            Internship opportunities: https://www.holyfamily.edu/about/administrative-services/office-internships-career-services/internship-opportunities

            Resume Guide provided by Brett Fucci:
            General: https://docs.google.com/document/d/1kAWFk-fFXbd5QuNLCd0z_Xeq5uaEwXfM
            Clinical-based: https://docs.google.com/document/d/1UFypYaC9RcOX13IKjwswl5_3P7UkX62C
            Education-focused: https://docs.google.com/document/d/1sHENhjRxna9ZS2o5rEL7namGfhB3bbSO
            Nursing: https://docs.google.com/document/d/1lBGfSbrEtb2BlZ_AzroGyCJGDP5ST0xz
            Psychology: https://docs.google.com/document/d/1LXQLc7PVx2yHa-qWQe8vkCc8mPDYZBWx

            Career stages guidance via onetonline.org for freshmen and sophomores.

            Appointments with Brett Fucci: https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ3YHxrnUSoz4LApLIGBVMx82LNAmwWd0F_0kjLhpSsNH3QHFICzR0IGLCTJKrEDctA8uuorKcxX

            Professional Week & Career Fair (March 2025):

            Registration: https://docs.google.com/forms/d/1Qvf_B4WUtEcJ3Df3qsZJJqIE6q2N5vuL-L5T7mgec3c/viewform?edit_requested=true

            Events:
            Resume/Cover Letter Workshop: March 17, Campus Center Room 115, 12:50–1:50 p.m.
            Career Circles: March 18, Campus Center Rooms 113 & 115, 1:00–3:00 p.m.
            Professional Branding: March 19, ETC Auditorium, 12:30–1:30 p.m.
            Interview Workshop: March 20, Campus Center Rooms 113 & 115, sessions at 12:30–1:30 p.m. and 2:00–3:00 p.m.

            Career Fair: March 26, Campus Center Gymnasium, 12:30–2:00 p.m.

            Monthly Networking Events:

            April 7, 2025: Criminal Justice, Biology, Graphic Design, IT Management, Accounting, Marketing

            May 5, 2025: Education, Nursing, Healthcare, Neuroscience, Psychology

            Additional Events:

            Professional Headshots: March 19, ETC Lounge, registration by March 17: https://docs.google.com/forms/d/e/1FAIpQLSeQ-CVdQUyoOIZSKDw9RsB7dxEEKxNtoehuGzHHqQd8ZHL_IQ/viewform

                  Mike DePrisco Presentation: March 19, Library 2nd floor, 12:50–1:50 p.m.

            Jefferson Health Nursing Event: April 2, Campus Center Room 113, 12:30–2:00 p.m.

        Forms & Accommodations:

            Forms: https://www.holyfamily.edu/academics/registrar/academic-forms

            Student accommodations: Contact Dean of Students at dos@holyfamily.edu


        Athletes can extend eligibility via graduate programs or adding minors.

        Study Abroad:
            Ireland (March 2025): https://www.efstudyabroad.com/programs/rm9c
            Spain (May 2025): https://www.efstudyabroad.com/my-quotes/2782516bc/quote/3332615/4dcb687ff53e4969b2
            Greece (May 2025): https://www.efstudyabroad.com/professors-trip/2767791ea

        Lucy Raffle games for HFU:
            Lucy is organizing a Big game for all students at HFU:
            Each question you ask Lucy earns you one ticket for our end-of-month raffle (chitchat questions, like “hello” “how are you”, are excluded from the count)
            The more you use Lucy, the better your chances of winning!
            10 winners will be selected: top prizes for the first winners!
            - TV
            - AirPods:
            - JBL speaker
            The rest of the winners will receive Lucy merch: Lucy T-shirt/Caps/Stress Balls 
            AND… THIS MARCH, LUCY’S BEST USER WILL WIN A ROUND-TRIP TO MIAMI!
            The winners will be announced during the Bingo on March 31st, and all students are eligible to participate in the game!
            For any questions about the game, you can reach out directly to us or anastasia.kolesnikova@my-lucy.com
           """
        ),
    }



def holyfamily_onboarding_prompt(student_profile: StudentProfile, linkedin_data) -> str:
    """
    Constructs a prompt combining satirical roast instructions, student profile details,
    and optional LinkedIn profile details.
    """
    username = getattr(student_profile, "username", "unknown")
    university = getattr(student_profile, "university", "unknown university")
    year = getattr(student_profile, "year", "unknown year")
    faculty_list = getattr(student_profile, "faculty", [])
    major_list = getattr(student_profile, "major", [])
    minor_list = getattr(student_profile, "minor", [])
    interests_list = getattr(student_profile, "interests", [])

    linkedin_details = (
        f"Occupation: {linkedin_data.get('occupation', 'N/A')}\n"
        f"Headline: {linkedin_data.get('headline', 'N/A')}\n"
        f"Summary: {linkedin_data.get('summary', 'N/A')}\n"
        f"Followers: {linkedin_data.get('follower_count', 0)}\n"
        f"Profile Picture: {linkedin_data.get('profile_pic_url', 'N/A')}\n"
        f"Experiences: {', '.join([exp.get('title', 'N/A') + ' at ' + exp.get('company', 'N/A') for exp in linkedin_data.get('experiences', [])])}\n"
        f"Education: {', '.join([edu.get('degree_name', 'N/A') + ' from ' + edu.get('school', 'N/A') for edu in linkedin_data.get('education', [])])}\n"
        f"Awards: {', '.join([award.get('title', 'N/A') for award in linkedin_data.get('accomplishment_honors_awards', [])])}"
    ) if linkedin_data else "No LinkedIn data provided."

    base_text = f"{username} at {university}, {year}"
    faculty_text = f"studying in {', '.join(faculty_list)}" if faculty_list else ""
    major_text = f"majoring in {', '.join(major_list)}" if major_list else ""
    minor_text = f"and minoring in {', '.join(minor_list)}" if minor_list else ""
    interests_text = f"the student's interests include: {', '.join(interests_list)}." if interests_list else "no specific interests provided."

    final_prompt = (
        f"lucy, you are an advisor for {username} at {university}. Deliver a satirical roast humorously highlighting {username}'s quirks, habits, and LinkedIn profile if available, demonstrating familiarity with {university}. "
        "Be extremely sassy, sarcastic, funny, and concise. Then clearly explain how you can help with academic queries, course guidance, and campus resources. "
        f"LinkedIn profile details:\n{linkedin_details}\n"
        f"Student profile overview: {base_text}. {faculty_text} {major_text} {minor_text}. {interests_text} "
        "Next week starting on the 17th is Career Week, perfect for refining resumes and cover letters, practicing interviews, networking, and finding a job or internship. "
        "Ask if the student would like more details or help registering. Be short and concise, no more than 5 sentences, very funny, sarcastic, and clear on how you can help."
    )

    return final_prompt
