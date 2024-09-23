# backend/assistant/assistant_manager.py

import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def initialize_assistant():
    assistant = openai.beta.assistants.create(
        name="Course Selection Assistant",
        instructions=(
            "You are an assistant that helps students choose their classes by filtering a course database based on their queries. "
            "Use the provided filters to search the database and return only the courses that match the criteria. "
            "Do not generate or fabricate any course information. If no courses match the query, inform the user accordingly."
        ),
        model="gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_filters",
                    "description": "Converts a student's query into database filters for course selection.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Name of the course (e.g., Archaeological Field Methods)."
                            },
                            "code": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    #"pattern": "^[A-Z]{2,4} \\d{4}$",
                                    "description": """Course code is defining the department and identification number of a class. It consist of 2-4 uppercase letters followed by a space and four digits (e.g., CIS 1210). the user can state either a specific course and the assistnat will make sure it fits the right format (eg.ECON 0100)or the user will input the subject and thus the assistant will only return the letters to identify the departement (eg.CIS)
                                                        To correctly format the id letters refer to the following guide
                                                        Academic Foundations (ACFD)
                                                        Accounting (ACCT)
                                                        Africana Studies (AFRC)
                                                        American Sign Language (ASLD)
                                                        Amharic (AMHR)
                                                        Anatomy (ANAT)
                                                        Ancient History (ANCH)
                                                        Ancient Middle East Languages (AMEL)
                                                        Anthropology (ANTH)
                                                        Applied Math & Computational Science (AMCS)
                                                        Applied Positive Psychology (APOP)
                                                        Arabic (ARAB)
                                                        Architecture (ARCH)
                                                        Art & Archaeology of Mediterranean World (AAMW)
                                                        Art History (ARTH)
                                                        Asian American Studies (ASAM)
                                                        Asian Languages (ALAN)
                                                        Astronomy (ASTR)
                                                        B
                                                        Bachelor of Applied Arts & Sciences (BAAS)
                                                        Behavioral & Decision Sciences (BDS)
                                                        Bengali (BENG)
                                                        Benjamin Franklin Seminars (BENF)
                                                        Biochemistry & Molecular Biophysics (BMB)
                                                        Biochemistry (BCHE)
                                                        Bioengineering (BE)
                                                        Bioethics (BIOE)
                                                        Biology (BIOL)
                                                        Biomedical Graduate Studies (BIOM)
                                                        Biomedical Informatics (BMIN)
                                                        Biostatistics (BSTA)
                                                        Biotechnology (BIOT)
                                                        Bosnian-Croatian-Serbo (BCS)
                                                        Business Economics & Public Policy (BEPP)
                                                        C
                                                        Cell and Molecular Biology (CAMB)
                                                        Chemical & Biomolecular Engineering (CBE)
                                                        Chemistry (CHEM)
                                                        Chichewa (CHIC)
                                                        Chinese (CHIN)
                                                        Cinema (CINM)
                                                        Cinema and Media Studies (CIMS)
                                                        City and Regional Planning (CPLN)
                                                        Classical Studies (CLST)
                                                        Classics (CLSC)
                                                        Climate Change (CLCH)
                                                        Cognitive Science (COGS)
                                                        College (COLL)
                                                        Communications (COMM)
                                                        Comparative Literature (COML)
                                                        Computer and Information Science (CIS)
                                                        Computer and Information Technology (CIT)
                                                        Creative Writing (CRWR)
                                                        Criminology (CRIM)
                                                        Czech (CZCH)
                                                        D
                                                        Data Analytics (DATA)
                                                        Data Science (DATS)
                                                        Demography (DEMG)
                                                        Dental - Dental Medicine (DENT)
                                                        Dental - Graduate Advanced Dental Studies (GADS)
                                                        Dental - Graduate Core Curriculum (DADE)
                                                        Dental - Graduate Doctor of Science in Dentistry (GDSD)
                                                        Dental - Graduate Endodontics (GEND)
                                                        Dental - Graduate Oral and Population Health (GOPH)
                                                        Dental - Graduate Oral Biology (GBIO)
                                                        Dental - Graduate Oral Health Sciences (GOHS)
                                                        Dental - Graduate Oral Medicine (GOMD)
                                                        Dental - Graduate Orthodontics (GORT)
                                                        Dental - Graduate Pediatrics (GPED)
                                                        Dental - Graduate Periodontics (GPRD)
                                                        Dental - Graduate Prosthodontics (GPRS)
                                                        Design (DSGN)
                                                        Digital Culture (DIGC)
                                                        Dutch (DTCH)
                                                        E
                                                        Earth and Environmental Science (EESC)
                                                        East Asian Languages & Civilization (EALC)
                                                        Economics (ECON)
                                                        Education (EDUC)
                                                        Education - Education Entrepreneurship (EDEN)
                                                        Education - Higher Education Management (EDHE)
                                                        Education - Independent School Teaching Residency (EDPR)
                                                        Education - Medical Education (EDME)
                                                        Education - Mid-Career Educational & Organizational Leadership (EDMC)
                                                        Education - Penn Chief Learning Officer (EDCL)
                                                        Education - School & Mental Health Counseling (EDSC)
                                                        Education - School Leadership (EDSL)
                                                        Education - Urban Teaching Residency Certificate (EDTC)
                                                        Education - Urban Teaching Residency Master's (EDTF)
                                                        Electrical & Systems Engineering (ESE)
                                                        Energy Management and Policy (ENMG)
                                                        Engineering & Applied Science (EAS)
                                                        Engineering (ENGR)
                                                        Engineering Mathematics (ENM)
                                                        English (ENGL)
                                                        English Literature (ENLT)
                                                        Environmental Studies (ENVS)
                                                        Epidemiology (EPID)
                                                        Ethics (ETHC)
                                                        F
                                                        Filipino (FILP)
                                                        Finance (FNCE)
                                                        Fine Arts (FNAR)
                                                        First-Year Seminar (FRSM)
                                                        Francophone, Italian, and Germanic Studies (FIGS)
                                                        French (FREN)
                                                        G
                                                        Gender, Sexuality & Women's Studies (GSWS)
                                                        Genetic Counseling (GENC)
                                                        Genomics & Comp. Biology (GCB)
                                                        Germanic Languages (GRMN)
                                                        Global MPA (GMPA)
                                                        Global Studies (GLBS)
                                                        Government Administration (GAFL)
                                                        Graduate Arts & Sciences (GAS)
                                                        Greek (GREK)
                                                        Gujarati (GUJR)
                                                        H
                                                        Health & Societies (HSOC)
                                                        Health Care Innovation (HCIN)
                                                        Health Care Management (HCMG)
                                                        Health Policy Research (HPR)
                                                        Healthcare Quality and Safety (HQS)
                                                        Hebrew (HEBR)
                                                        Hindi (HIND)
                                                        Historic Preservation (HSPV)
                                                        History & Sociology of Science (HSSC)
                                                        History (HIST)
                                                        Hungarian (HUNG)
                                                        I
                                                        Igbo (IGBO)
                                                        Immunology (IMUN)
                                                        Implementation Science (IMP)
                                                        Indonesian (INDO)
                                                        Integrated Product Design (IPD)
                                                        Integrated Studies (INTG)
                                                        Intercultural Communication (ICOM)
                                                        International Relations (INTR)
                                                        International Studies (INSP)
                                                        Irish Gaelic (IRIS)
                                                        Italian (ITAL)
                                                        J
                                                        Japanese (JPAN)
                                                        Jewish Studies Program (JWST)
                                                        K
                                                        Kannada (KAND)
                                                        Korean (KORN)
                                                        L
                                                        Landscape Architecture & Regional Planning (LARP)
                                                        Languages (LANG)
                                                        Latin (LATN)
                                                        Latin American & Latinx Studies (LALS)
                                                        Law (LAW)
                                                        Law - Master in Law (LAWM)
                                                        Leadership and Communication (LEAD)
                                                        Legal Studies & Business Ethics (LGST)
                                                        Linguistics (LING)
                                                        Logic, Information and Computation (LGIC)
                                                        M
                                                        Malagasy (MALG)
                                                        Malayalam (MLYM)
                                                        Management (MGMT)
                                                        Marathi (MRTI)
                                                        Marketing (MKTG)
                                                        Master of Applied Positive Psychology (MAPP)
                                                        Master of Liberal Arts (MLA)
                                                        Master of Science in Social Policy (MSSP)
                                                        Master of Science in Translational Research (MTR)
                                                        Master of Urban Spatial Analytics (MUSA)
                                                        Materials Science and Engineering (MSE)
                                                        Mathematical Sciences (MTHS)
                                                        Mathematics (MATH)
                                                        Mechanical Engineering and Applied Mechanics (MEAM)
                                                        Medical Physics (MPHY)
                                                        Middle Eastern Languages & Cultures (MELC)
                                                        Military Science (MSCI)
                                                        Modern Middle East Studies (MODM)
                                                        Music (MUSC)
                                                        N
                                                        Nanotechnology (NANO)
                                                        Naval Science (NSCI)
                                                        Network and Social Systems Engineering (NETS)
                                                        Neuroscience (NEUR) - Liberal and Professional Studies
                                                        Neuroscience (NGG) - Perelman School of Medicine
                                                        Neuroscience (NRSC) - School of Arts and Sciences
                                                        Nonprofit Leadership (NPLD)
                                                        Nursing (NURS)
                                                        Nutrition Science (NUTR)
                                                        O
                                                        Operations, Information and Decisions (OIDD)
                                                        Organizational Anthropology (ORGC)
                                                        Organizational Dynamics (DYNM)
                                                        P
                                                        Pashto (PASH)
                                                        Persian (PERS)
                                                        Pharmacology (PHRM)
                                                        Philosophy (PHIL)
                                                        Philosophy, Politics, Economics (PPE)
                                                        Physical and Life Sciences (PHYL)
                                                        Physics (PHYS)
                                                        Polish (PLSH)
                                                        Political Science (PSCI)
                                                        Politics & Policy (PPOL)
                                                        Portuguese (PRTG)
                                                        Professional Writing (PROW)
                                                        Psychology (PSYC)
                                                        Psychology, Behavior & Decision Sciences (PBDS)
                                                        Public Health Studies (PUBH)
                                                        Punjabi (PUNJ)
                                                        Q
                                                        Quechua (QUEC)
                                                        R
                                                        Real Estate (REAL)
                                                        Regulatory (REG)
                                                        Religion and Culture (RELC)
                                                        Religious Studies (RELS)
                                                        Robotics (ROBO)
                                                        Romance Languages (ROML)
                                                        Russian (RUSS)
                                                        Russian and East European Studies (REES)
                                                        S
                                                        Sanskrit (SKRT)
                                                        School of Social Policy and Practice (SSPP)
                                                        Science, Technology & Society (STSC)
                                                        Scientific Computing (SCMP)
                                                        Scientific Processes (SPRO)
                                                        Social Difference, Diversity, Equity and Inclusion (SDEI)
                                                        Social Welfare (SOCW)
                                                        Social Work (SWRK)
                                                        Sociology (SOCI)
                                                        South Asia Studies (SAST)
                                                        Spanish (SPAN)
                                                        Spanish and Portuguese (SPPO)
                                                        Statistics and Data Science (STAT)
                                                        Sudanese Arabic (SARB)
                                                        Swahili (SWAH)
                                                        Swedish (SWED)
                                                        T
                                                        Tamil (TAML)
                                                        Telugu (TELU)
                                                        Thai (THAI)
                                                        Theatre Arts (THAR)
                                                        Tibetan (TIBT)
                                                        Tigrinya (TIGR)
                                                        Turkish (TURK)
                                                        Twi (TWI)
                                                        U
                                                        Ukrainian (UKRN)
                                                        Urban Studies (URBS)
                                                        Urdu (URDU)
                                                        V
                                                        Veterinary Clinical Studies - Medicine Courses (VMED)
                                                        Veterinary Clinical Studies - New Bolton Center (VCSN)
                                                        Veterinary Clinical Studies and Advanced Medicine - Philadelphia (VCSP)
                                                        Veterinary Independent Study & Research (VISR)
                                                        Veterinary Pathobiology (VPTH)
                                                        Vietnamese (VIET)
                                                        Viper (VIPR)
                                                        Visual Studies (VLST)
                                                        W
                                                        Wharton Communication Program (WHCP)
                                                        Wharton Undergraduate (WH)
                                                        Wolof (WOLF)
                                                        Y
                                                        Yiddish (YDSH)
                                                        Yoruba (YORB)
                                                        Z
                                                        Zulu (ZULU)

                                    """
                                },
                                "description": "Course code (e.g., AAMW 5231, CIS 1210). The assistant should ensure the format is correct, correcting it if necessary."
                            },
                            "Schedule Type": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Type of schedule one of the following: (('Seminar' 'Lecture' 'Varies by section' 'Recitation' 'Studio', 'Laboratory' 'N/A' 'Masters Thesis'))."
                            },
                            "Instruction Method": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Method of instruction (one of the following: [ In Class,  Active Learning,  Clinical Based Learning,  Dissertation/Masters,  Field Work,  Hybrid,  Independent Study,  Internship,  Online,  Research])."
                            },
                            "Credit": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "The number of credits a user wants, which can be specified in three ways: exact number (e.g., [1], [2]), a range of credits (e.g., 'between 2 and 4' translates to [2, 3, 4]), or exclusions (e.g., 'no 0.5 credits' translates to [1, 1.5, 2, 2.5, 3, 3.5, 4]). The assistant understands that valid credit values range from 0 to 4, including increments of 0.5. It will return a list of possible credit values based on the user's input."
                            },
                            "Course Description": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Description or topic of the course (e.g., Machine Learning, Data Structures)."
                            },
                            "Section Details": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific details about a course section."
                            },
                            "Registration Restrictions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Text explaining any registration restrictions."
                            },
                            "Section Attributes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Attributes of the section (e.g., Humanities, Electives, ARTH Ancient (AHAA), ARTH Elective Major/Minor)."
                            },
                            "Schedule and Location": {
                                "type": "object",
                                "properties": {
                                    "include_days": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": (
                                            "Days to include in the course schedule using MTWRF format (e.g., ['M', 'W'] for Monday and Wednesday). "
                                            "Each day should be a single character representing the day of the week: "
                                            "M (Monday), T (Tuesday), W (Wednesday), R (Thursday), F (Friday). "
                                            "Example: ['F'] for courses on Friday or ['MW'] for courses on Monday and Wednesday."
                                        )
                                    },
                                    "exclude_days": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": (
                                            "Days to exclude from the course schedule using MTWRF format (e.g., ['F'] to exclude Friday). "
                                            "Each day should be a single character representing the day of the week: "
                                            "M (Monday), T (Tuesday), W (Wednesday), R (Thursday), F (Friday). "
                                            "Example: ['F'] to exclude courses on Friday or ['M', 'W'] to exclude Monday and Wednesday."
                                        )
                                    },
                                    "time_slots": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": (
                                            "Time slots during which the courses are scheduled, formatted as 'Day hh:mmAM/PM-hh:mmAM/PM'. "
                                            "Days are represented by single characters: M (Monday), T (Tuesday), W (Wednesday), R (Thursday), F (Friday). "
                                            "Multiple time slots can be separated by semicolons. "
                                            "Example: ['F 8:30am-11:29am', 'MW 3:30pm-4:59pm']."
                                        )
                                    },
                                    "excluded_hours": {  # Added property
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": (
                                            "Specific hours to exclude from the course schedule, formatted as 'hh:mmAM/PM-hh:mmAM/PM'. "
                                            "Example: ['12:00pm-1:00pm'] to exclude courses during lunch hour."
                                        )
                                    },
                                    "included_hours": {  # Added property
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": (
                                            "Specific hours to include in the course schedule, formatted as 'hh:mmAM/PM-hh:mmAM/PM'. "
                                            "Example: ['9:00am-12:00pm'] to include only morning classes."
                                        )
                                    },
                                },
                                "description": (
                                    "Schedule and Location details for the courses. This includes the days of the week and the times the courses are held. "
                                    "Use the 'include_days' to specify days when you want the courses to be scheduled, 'exclude_days' to omit certain days, "
                                    "and 'time_slots' to define specific time ranges. "
                                    "All days should be represented using the MTWRF format where: "
                                    "M = Monday, T = Tuesday, W = Wednesday, R = Thursday, F = Friday."
                                )
                            },
                            "Instructors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of instructors teaching the course."
                            },
                            "Course Quality": {
                                "type": "string",
                                "description": "Quality of the course on a scale of 1 to 5 (e.g., '> 4.5')."
                            },
                            "Instructor Quality": {
                                "type": "string",
                                "description": "Quality of the instructor on a scale of 1 to 5 (e.g., '>= 4')."
                            },
                            "Work Required": {
                                "type": "string",
                                "description": "Amount of work required on a scale of 1 to 5 (e.g., '>= 3')."
                            },
                            "Difficulty": {
                                "type": "string",
                                "description": "Difficulty level on a scale of 1 to 5 (e.g., '<= 3')."
                            },
                            "Prerequisites": {
                                "type": "object",
                                "properties": {
                                    "has_prerequisites": {
                                        "type": "boolean",
                                        "description": "Indicates whether the course should have any prerequisites or none."
                                    },
                                    "prerequisites_to_include": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "description": "Courses that should be listed as prerequisites (e.g., CIS 1210)."
                                    },
                                    "prerequisites_to_exclude": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "description": "Courses that should not be listed as prerequisites (e.g., CIS 1210)."
                                    }
                                }
                            }

                        },
                        # No 'required' field to allow optional parameters
                    }
                }
            }
        ]
    )
    return assistant

