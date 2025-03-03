import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from botocore.exceptions import ClientError
from typing import List
import uvicorn
from datetime import datetime, timedelta  # Ajoutez cette ligne pour importer datetime et timedelta
from student_app.database.dynamo_db.analytics import fetch_request_data_from_dynamo  # Import the function that interacts with AWS DynamoDB
from student_app.database.dynamo_db.chat import get_conversations_from_chat_ids, count_active_users, count_returning_users, calculate_churn, sessions_per_user, rolling_retention, get_date_or_default, simple_count_active_users_in_window, strict_count_active_users 


from student_app.database.firebase.user_analytics import fetch_user_data_from_firestore  # Import the function that interacts with AWS DynamoDB
from student_app.database.firebase.user_analytics import count_users_by_university  # Import the function that interacts with AWS DynamoDB
from student_app.database.firebase.user_analytics import analyze_conversations  # Import the function that interacts with AWS DynamoDB
from student_app.database.firebase.user_analytics import analyze_users  # Import the function that interacts with AWS DynamoDB



#from student_app.database.dynamo_db.analytics import fetch_request_data


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("file_server.log")
    ]
)

# FastAPI app configuration
app = FastAPI(
    title="Request Data Service",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model for the incoming request data
class RequestDataModel(BaseModel):
    timeFilter: str  # 'Today', 'Last Week', 'Last Month', 'Last Year'
    #universityFilter: str  # 'All', 'Harvard', etc.


# Pydantic model for the response data
class RequestDataResponseModel(BaseModel):
    count: int
    dates: List[str]  # List of dates in string format for the response


# Modèle Pydantic pour la requête (entrée)
class UserAnalyticsRequest(BaseModel):
    uid: str

# Modèle Pydantic pour la réponse (sortie)
class UserAnalyticsResponse(BaseModel):
    user_info: dict
    auth_info: dict
    chat_sessions: list


# Endpoint to handle the filtered request data
@app.post("/requests_filtered", response_model=RequestDataResponseModel)
async def get_filtered_request_data(request_data: RequestDataModel):
    try:
        # Call the AWS DynamoDB handler function
        university = "all"

        print(university)
        print(request_data.timeFilter)

        count, timestamps = fetch_request_data_from_dynamo(university, request_data.timeFilter)#, request_data.universityFilter)

        response_data = {
            "count": count,
            "dates": timestamps  # Assuming 'timestamps' are in ISO format
        }
        
        return response_data

    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())
    
    except ClientError as e:
        logging.error(f"AWS ClientError: {str(e)}")
        raise HTTPException(status_code=500, detail="AWS Error occurred")

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    


# Endpoint to handle the filtered request data
@app.post("/user_analytics")
async def get_user_analytics(request_data: UserAnalyticsRequest):
    """
    Endpoint FastAPI pour récupérer les données analytiques d'un utilisateur depuis Firestore et Firebase Auth.

    :param request_data: Données envoyées par le frontend avec l'UID de l'utilisateur
    :return: Informations complètes de l'utilisateur sous forme JSON
    """
    try:
        # Appel de la fonction pour récupérer les données utilisateur
        user_data = fetch_user_data_from_firestore(request_data.uid)

        logging.info(f"✅ Réponse API : {user_data}")

        # Vérifier si une erreur a été retournée par la fonction
        if "error" in user_data:
            raise HTTPException(status_code=404, detail=user_data["error"])
        
        # Récupérer les conversations associées aux chat_ids de l'utilisateur
        chat_ids = user_data.get("chatsessions", [])
        conversations = await get_conversations_from_chat_ids(chat_ids)
        
        # Ajouter les conversations aux données utilisateur
        user_data["conversations"] = conversations
        
        logging.info(f"✅ Réponse API avec conversations : {user_data}")

        return user_data

    except Exception as e:
        # Log l'erreur et retourne une erreur 500
        print(f"Erreur lors de la récupération des données pour UID {request_data.uid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue lors du traitement de la requête.")
    

class UniversityRequest(BaseModel):
    university: str

@app.post("/university_user_count")
async def get_university_user_count(request_data: UniversityRequest):
    """
    Endpoint FastAPI pour récupérer le nombre d'utilisateurs dans Firestore ayant une université spécifique.

    :param request_data: Nom de l'université sous forme JSON
    :return: Nombre d'utilisateurs trouvés
    """
    try:
        # Appel de la fonction qui compte les utilisateurs
        result = count_users_by_university(request_data.university)

        logging.info(f"✅ Réponse API : {result}")

        # Vérifier si une erreur est retournée
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result

    except Exception as e:
        logging.error(f"❌ Erreur lors du traitement de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue.")
    

class ConversationRequest(BaseModel):
    since_date: str  # Format attendu : "YYYY-MM-DD"


@app.post("/conversation_statistics")
async def get_conversation_statistics(request_data: ConversationRequest):
    """
    Endpoint FastAPI pour récupérer les statistiques des conversations après une date donnée.

    :param request_data: Date sous format "YYYY-MM-DD".
    :return: Statistiques des conversations après la date spécifiée.
    """
    try:
        # Vérification de la présence de la date
        if not request_data.since_date:
            raise HTTPException(status_code=400, detail="Le champ 'since_date' est requis.")

        # Appel de la fonction d'analyse des conversations avec filtrage temporel
        result = analyze_conversations(request_data.since_date)

        logging.info(f"✅ Réponse API : {result}")

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        logging.error(f"❌ Erreur lors du traitement de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue.")
    


class UserStatisticsRequest(BaseModel):
    since_date: str  # Format attendu : "YYYY-MM-DD"

@app.post("/user_statistics")
async def get_user_statistics(request_data: UserStatisticsRequest):
    """
    Endpoint FastAPI pour récupérer les statistiques des utilisateurs après une date donnée.

    :param request_data: Date sous format "YYYY-MM-DD".
    :return: Statistiques des utilisateurs après la date spécifiée.
    """
    try:
        # Vérification de la présence de la date
        if not request_data.since_date:
            raise HTTPException(status_code=400, detail="Le champ 'since_date' est requis.")

        # Appel de la fonction d'analyse des utilisateurs avec filtrage temporel
        result = analyze_users(request_data.since_date)

        logging.info(f"✅ Réponse API : {result}")

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        logging.error(f"❌ Erreur lors du traitement de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue.")





class ActiveUsersRequest(BaseModel):
    since_date: str = None  # Optionnel, si absent, on prend la date du jour


@app.post("/active_users")
async def get_active_users(request_data: ActiveUsersRequest):
    """
    Endpoint FastAPI pour récupérer les métriques d'Active Users stricts.
    Un utilisateur est considéré actif s'il a envoyé au moins un message chaque jour dans la période DAU.
    Pour WAU, MAU et SAU, l'utilisateur est actif s'il a envoyé au moins un message pendant la fenêtre de 7, 30 ou 180 jours.
    Si la période entre la date fournie et aujourd'hui est insuffisante pour la fenêtre, la valeur renvoyée sera "N/A".
    
    :param request_data: Date de référence (YYYY-MM-DD). Si absente, la date du jour est utilisée.
    :return: Statistiques d'Active Users stricts.
    """
    try:
        # Utilisation de la date fournie ou, sinon, la date du jour
        ref_date = get_date_or_default(request_data.since_date, 0)
        logging.info(f"📊 Calcul des Active Users stricts avec référence {ref_date}")
        
        # Calcul de la durée totale de la période (en jours)
        ref_dt = datetime.strptime(ref_date, "%Y-%m-%d").date()
        today = datetime.utcnow().date()
        total_days = (today - ref_dt).days + 1
        
        # DAU strict : utilisateurs actifs chaque jour depuis ref_date
        dau = strict_count_active_users(ref_date)
        
        # WAU simple : uniquement si la période est d'au moins 7 jours, sinon "N/A"
        wau = simple_count_active_users_in_window(ref_date, 7)
        
        # MAU simple : uniquement si la période est d'au moins 30 jours, sinon "N/A"
        mau = simple_count_active_users_in_window(ref_date, 30)
        
        # SAU simple : uniquement si la période est d'au moins 180 jours, sinon "N/A"
        sau = simple_count_active_users_in_window(ref_date, 180)
        
        # Pour returning_users, churn_rate, avg_sessions et rolling_retention, on utilise la date ref_date
        returning_users = count_returning_users(get_date_or_default(ref_date, 30),
                                                 get_date_or_default(ref_date, 7))
        churn_rate = calculate_churn(ref_date)
        avg_sessions = sessions_per_user(ref_date)
        rolling_retention_14 = rolling_retention(14, ref_date)
        
        results = {
            "period_days": total_days,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "sau": sau,
            "returning_users": returning_users,
            "churn_rate": churn_rate,
            "avg_sessions_per_user": avg_sessions,
            "rolling_retention_14_days": rolling_retention_14
        }
        
        logging.info(f"✅ Active Users stricts métriques calculées : {results}")
        return results
    except Exception as e:
        logging.error(f"❌ Erreur lors du calcul des Active Users stricts : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du calcul des Active Users stricts")


# Start the FastAPI app
def create_app():
    return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
