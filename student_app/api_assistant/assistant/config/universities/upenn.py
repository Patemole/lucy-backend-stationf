# config/universities/upenn.py

def get_upenn_config(university, current_date, username, major, minor, year, school):
    return {
        "instructions": (
            f"""
            Never mention PennInTouch only path@penn 
            courses are now 4 digits code so now CIS121 is CIS1210 and like Math240 is Math2400
            """
        ),
    }
