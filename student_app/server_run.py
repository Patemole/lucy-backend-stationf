import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

print("Starting the correct file")
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from student_app.server_files import create_app as create_files_app
from student_app.server_academic_advisor import create_app as create_academic_advisor_app
from student_app.server_feedback import create_app as create_feedback_app
from student_app.server_analytics import create_app as create_analytics_app


# Configurer le logging
logging.basicConfig(level=logging.DEBUG)  # Passer à DEBUG pour plus de détails
logger = logging.getLogger(__name__)

print("Démarrage de l'application")
logger.info("Démarrage de l'application")

app = FastAPI()

# Configurer CORS avant de monter les sous-applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour journaliser les requêtes
@app.middleware("http")
async def log_request(request, call_next):
    print(f"Request: {request.method} {request.url}")
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    logger.info(f"Response: {response.status_code}")
    return response




# Chemins relatifs
static_dir = os.path.join(os.path.dirname(__file__), "../analytics/analytics_teacher")
static_dir_academic_advisor = os.path.join(os.path.dirname(__file__), "../analytics_academic")
#static_dir_page_test = os.path.join(os.path.dirname(__file__), "../html_page_testt")

static_dir_page_yc_popup = os.path.join(os.path.dirname(__file__), "../pop_up_page_yc")

# Assurez-vous que les répertoires existent
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

if not os.path.exists(static_dir_academic_advisor):
    os.makedirs(static_dir_academic_advisor)

# Monter les répertoires statiques
app.mount("/static/teacher", StaticFiles(directory=static_dir), name="static_teacher")
app.mount("/static/academic_advisor", StaticFiles(directory=static_dir_academic_advisor), name="static_academic_advisor")
#app.mount("/static/page_test", StaticFiles(directory=static_dir_page_test), name="static_page_test")

app.mount("/static/yc_popup", StaticFiles(directory=static_dir_page_yc_popup), name="static_yc_popup")




try:
    print("Création de l'application files")
    logger.info("Création de l'application files")

    files_app = create_files_app()
    if files_app is None:
        print("Application files n'a pas été créée")
        logger.error("Application files n'a pas été créée")

    else:
        print("Application files créée avec succès")
        logger.info("Application files créée avec succès")



    print("Création de l'application academic advisor")
    logger.info("Création de l'application academic advisor")

    chat_app = create_academic_advisor_app()
    if chat_app is None:
        print("Application academic advisor n'a pas été créée")
        logger.error("Application academic advisor n'a pas été créée")
    else:
        print("Application academic advisor créée avec succès")
        logger.info("Application academic advisor créée avec succès")


    
    print("Création de l'application feedback")
    logger.info("Création de l'application feedback")

    feedback_app = create_feedback_app()
    if feedback_app is None:
        print("Application feedback n'a pas été créée")
        logger.error("Application feedback n'a pas été créée")
    else:
        print("Application feedback créée avec succès")
        logger.info("Application feedback créée avec succès")



    print("Création de l'application analytics")
    logger.info("Création de l'application analytics")

    analytics_app = create_analytics_app()
    if analytics_app is None:
        print("Application analytics n'a pas été créée")
        logger.error("Application analytics n'a pas été créée")
    else:
        print("Application analytics créée avec succès")
        logger.info("Application analytics créée avec succès")



    print("Montage des applications")
    logger.info("Montage des applications")

    if files_app:
        app.mount("/files", files_app)

    if chat_app:
        app.mount("/chat", chat_app)

    if feedback_app:
        app.mount("/feedback", feedback_app)

    if analytics_app:
        app.mount("/analytics", analytics_app)

    print("Applications montées avec succès")
    logger.info("Applications montées avec succès")


except Exception as e:
    print(f"Erreur lors de la création ou du montage des applications: {e}")
    logger.exception("Erreur lors de la création ou du montage des applications: %s", e)
    raise e

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5001))
    print(f"Démarrage du serveur sur le port {port}")
    logger.info(f"Démarrage du serveur sur le port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")  # Passer log_level à debug pour plus de détails
