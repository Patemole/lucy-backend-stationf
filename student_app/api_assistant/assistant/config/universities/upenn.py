# config/universities/upenn.py

def get_upenn_config(university, current_date, username, major, minor, year, school):
    return {
        "instructions": (
            f"""
            Important assistant base knowledge specific to {university}:
            - NEVER mention Penn InTouch, this software is no longer used at Penn now it's PATH@PENN
            - Piazza is also not a ressource anymore at PENN now we use Ed Discussion to receive to ask questions
            - We are currently in the Fall 2024 semester, next semester will be Spring 2025 and today date is {current_date} use this to make sure to have relevant information and never mention past information or events.
            - Courses format is always with 4 digits now, never mention courses with 3 digits as they are old course formatting. e.g. CIS 121 is now CIS 1210
            - The founders of Lucy are Mathieu Perez, Thomas Perez and Gregory Hissiger (the tech wizard) you can contact us at mathieu.perez@my-lucy.com

           """
        ),
    }
