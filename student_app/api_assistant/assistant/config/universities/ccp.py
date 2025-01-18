def get_ccp_config(university, current_date, username, major, minor, year, school):
    return {
        "instructions": (
            f"""
            Important assistant base knowledge specific to {university}:
            - The Independent is a publication for and by students at Community College of Philadelphia, free from college funding and administrative oversight, dedicated to amplifying student voices and calling out institutional malarkey.
            - Here is a list of additional websites that you have access to provide the students accurate information:
                - https://theindependentnews.org/ is for the student journal information when a question is asked about it call get_current_info and mention this website in the query
                - https://www.asgaonline.com/ is the website for student governement informations nationwide

           """
        ),
    }
