import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
import logging
import os

'''
# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Définir le chemin du fichier JSON du compte de service Firebase
SERVICE_ACCOUNT_FILE = "FireStoreServiceAccountKeyProd.json"

# Vérifier si Firebase est déjà initialisé
if not firebase_admin._apps:
    try:
        # Vérifier si le fichier JSON existe
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logging.error(f"❌ Erreur : Le fichier '{SERVICE_ACCOUNT_FILE}' est introuvable. Vérifie son emplacement.")
            raise FileNotFoundError(f"Le fichier {SERVICE_ACCOUNT_FILE} est introuvable.")

        logging.info(f"✅ Fichier {SERVICE_ACCOUNT_FILE} trouvé. Initialisation de Firebase...")

        # Charger le fichier JSON et initialiser Firebase
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)

        logging.info("✅ Firebase initialisé avec succès.")

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'initialisation de Firebase : {str(e)}")
        raise
else:
    logging.info("ℹ️ Firebase est déjà initialisé.")

# Connexion à Firestore
db = firestore.client()


def fetch_user_data_from_firestore(uid: str):
    """
    Récupère toutes les informations d'un étudiant à partir des collections 'users' et 'chatsessions' dans Firestore,
    ainsi que ses informations d'authentification depuis Firebase Authentication.

    :param uid: L'identifiant unique de l'étudiant
    :return: Un dictionnaire contenant toutes les informations utilisateur et ses sessions de chat détaillées
    """
    user_data = {}

    # 🔹 1. Récupérer les informations d'authentification (Firebase Authentication)
    try:
        user_auth = auth.get_user(uid)
        auth_info = {
            "email": user_auth.email,
            "email_verified": user_auth.email_verified,
            "phone_number": user_auth.phone_number,
            "provider_id": user_auth.provider_id,
            "photo_url": user_auth.photo_url,
            "created_at": datetime.fromtimestamp(user_auth.user_metadata.creation_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S") if user_auth.user_metadata.creation_timestamp else "Inconnu",
            "last_login": datetime.fromtimestamp(user_auth.user_metadata.last_sign_in_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S") if user_auth.user_metadata.last_sign_in_timestamp else "Jamais connecté"
        }
        logging.info(f"✅ Informations d'auth récupérées pour UID {uid}")
    except firebase_admin.auth.UserNotFoundError:
        logging.error(f"❌ Utilisateur Firebase Auth non trouvé pour UID {uid}")
        auth_info = {"error": f"Aucune information d'authentification trouvée pour l'UID {uid}"}
    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération des informations d'authentification : {str(e)}")
        auth_info = {"error": "Erreur interne lors de la récupération des informations d'authentification"}

    # 🔹 2. Récupérer les informations depuis la collection 'users' (Firestore)
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            # Convertir les timestamps en format lisible
            if "createdAt" in user_data and isinstance(user_data["createdAt"], datetime):
                user_data["createdAt"] = user_data["createdAt"].strftime("%Y-%m-%d %H:%M:%S")
            if "updatedAt" in user_data and isinstance(user_data["updatedAt"], datetime):
                user_data["updatedAt"] = user_data["updatedAt"].strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"✅ Données utilisateur récupérées pour UID {uid}")
        else:
            logging.error(f"❌ Utilisateur avec UID {uid} non trouvé dans Firestore.")
            return {"error": f"Utilisateur avec UID {uid} non trouvé dans Firestore."}
    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération des données utilisateur : {str(e)}")
        return {"error": "Erreur interne lors de la récupération des données utilisateur"}

    # 🔹 3. Récupérer les sessions de chat référencées dans user_data["chatsessions"]
    chat_sessions = []
    if "chatsessions" in user_data and isinstance(user_data["chatsessions"], list):
        for chat_id in user_data["chatsessions"]:
            try:
                chat_ref = db.collection("chatsessions").document(chat_id)
                chat_doc = chat_ref.get()

                if chat_doc.exists:
                    chat_data = chat_doc.to_dict()
                    # Convertir les timestamps en format lisible
                    if "created_at" in chat_data and isinstance(chat_data["created_at"], datetime):
                        chat_data["created_at"] = chat_data["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                    if "modified_at" in chat_data and isinstance(chat_data["modified_at"], datetime):
                        chat_data["modified_at"] = chat_data["modified_at"].strftime("%Y-%m-%d %H:%M:%S")
                    chat_sessions.append(chat_data)
                    logging.info(f"✅ Session de chat récupérée : {chat_id}")
                else:
                    logging.warning(f"⚠️ Session de chat {chat_id} non trouvée.")
            except Exception as e:
                logging.error(f"❌ Erreur lors de la récupération de la session de chat {chat_id} : {str(e)}")

    # 🔹 4. Ajouter les sessions de chat et les données d'authentification aux données utilisateur
    user_data["chat_sessions"] = chat_sessions
    user_data["auth_info"] = auth_info  # Ajout des données Firebase Auth

    logging.info(f"✅ Récupération complète des données utilisateur pour UID {uid}")

    logging.info(f"✅ Réponse prête à être envoyée : {user_data}")
    return user_data



def count_users_by_university(university_name: str):
    """
    Compte le nombre d'utilisateurs dans Firestore qui ont une université spécifique.

    :param university_name: Nom de l'université à rechercher.
    :return: Nombre d'utilisateurs trouvés.
    """
    try:
        # Requête pour récupérer tous les utilisateurs ayant l'université spécifiée
        users_query = db.collection("users").where("university", "==", university_name).stream()
        
        # Compter le nombre d'utilisateurs
        user_count = sum(1 for _ in users_query)

        logging.info(f"✅ Nombre d'utilisateurs trouvés pour {university_name} : {user_count}")
        return {"university": university_name, "user_count": user_count}

    except Exception as e:
        logging.error(f"❌ Erreur lors du comptage des utilisateurs pour {university_name} : {str(e)}")
        return {"error": "Erreur interne lors du comptage des utilisateurs"}





from datetime import datetime
import logging

def analyze_conversations(since_date: str):
    """
    Analyse les conversations stockées dans Firestore dans la collection 'chatsessions',
    en filtrant uniquement celles créées après une date donnée.

    :param since_date: Date de filtrage sous forme de chaîne "YYYY-MM-DD"
    :return: Un dictionnaire contenant :
        - Nombre total de conversations après la date donnée.
        - Proportion de conversations privées, publiques et sans info.
        - Proportion de conversations selon le champ 'topic'.
        - Proportion des conversations ayant 'New Chat' comme nom ou un autre titre.
    """
    try:
        # Vérification et conversion de la date
        try:
            filter_date = datetime.strptime(since_date, "%Y-%m-%d")
        except ValueError:
            logging.error("❌ Format de date invalide. Utiliser 'YYYY-MM-DD'.")
            return {"error": "Format de date invalide. Utiliser 'YYYY-MM-DD'."}

        logging.info(f"📅 Filtrage des conversations après {since_date}")

        # Requête Firestore pour récupérer les conversations après la date donnée
        chat_sessions = db.collection("chatsessions").where("created_at", ">=", filter_date).stream()

        total_conversations = 0
        private_count = 0
        public_count = 0
        no_info_privacy = 0

        topic_counts = {
            "Event": 0,
            "Policies": 0,
            "Chitchat": 0,
            "Courses": 0,
            "Financial Aids": 0,
            "No info": 0
        }

        new_chat_count = 0
        other_name_count = 0

        for chat in chat_sessions:
            total_conversations += 1
            chat_data = chat.to_dict()

            # Analyse du type de conversation (privé/public/pas d'infos)
            if "thread_type" in chat_data:
                if chat_data["thread_type"] == "Private":
                    private_count += 1
                elif chat_data["thread_type"] == "Public":
                    public_count += 1
                else:
                    no_info_privacy += 1
            else:
                no_info_privacy += 1

            # Analyse du sujet de conversation (topic)
            topic = chat_data.get("topic", "No info")
            if topic in topic_counts:
                topic_counts[topic] += 1
            else:
                topic_counts["No info"] += 1

            # Analyse du champ 'name' (New Chat ou autre titre)
            if chat_data.get("name") == "New Chat":
                new_chat_count += 1
            else:
                other_name_count += 1

        # Calcul des proportions sur 100%
        def compute_percentage(count):
            return round((count / total_conversations * 100), 2) if total_conversations > 0 else 0

        privacy_distribution = {
            "Private": compute_percentage(private_count),
            "Public": compute_percentage(public_count),
            "No info": compute_percentage(no_info_privacy)
        }

        topic_distribution = {key: compute_percentage(value) for key, value in topic_counts.items()}

        name_distribution = {
            "New Chat": compute_percentage(new_chat_count),
            "Autre titre": compute_percentage(other_name_count)
        }

        results = {
            "total_conversations": total_conversations,
            "privacy_distribution": privacy_distribution,
            "topic_distribution": topic_distribution,
            "name_distribution": name_distribution
        }

        logging.info(f"✅ Analyse des conversations après {since_date} terminée : {results}")
        return results

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'analyse des conversations : {str(e)}")
        return {"error": "Erreur interne lors de l'analyse des conversations"}
    



def analyze_users(since_date: str):
    """
    Analyse les utilisateurs stockés dans Firestore dans la collection 'users',
    en filtrant uniquement ceux créés après une date donnée.

    :param since_date: Date de filtrage sous forme de chaîne "YYYY-MM-DD"
    :return: Un dictionnaire contenant :
        - Nombre total d'utilisateurs après la date donnée.
        - Proportion des universités ("upenn", "harvard", "ccp", "holyfamily", "berkeley", "purdue", "other").
        - Proportion par année d'étude ("Freshman", "Sophomore", "Junior", "Senior", "Grad 1", "Grad 2", "other").
        - Statistiques sur le nombre de sessions de chat (moyenne, max, min).
        - Proportion des utilisateurs inscrits à un club ("yes" vs "no").
    """
    try:
        # Vérification et conversion de la date
        try:
            filter_date = datetime.strptime(since_date, "%Y-%m-%d")
        except ValueError:
            logging.error("❌ Format de date invalide. Utiliser 'YYYY-MM-DD'.")
            return {"error": "Format de date invalide. Utiliser 'YYYY-MM-DD'."}

        logging.info(f"📅 Filtrage des utilisateurs après {since_date}")

        # Requête Firestore pour récupérer les utilisateurs après la date donnée
        users_query = db.collection("users").where("createdAt", ">=", filter_date).stream()

        total_users = 0
        university_counts = {
            "upenn": 0,
            "harvard": 0,
            "ccp": 0,
            "holyfamily": 0,
            "berkeley": 0,
            "purdue": 0,
            "other": 0
        }
        year_counts = {
            "Freshman": 0,
            "Sophomore": 0,
            "Junior": 0,
            "Senior": 0,
            "Grad 1": 0,
            "Grad 2": 0,
            "other": 0
        }
        registered_club_counts = {"yes": 0, "no": 0}

        chat_sessions_counts = []

        for user in users_query:
            total_users += 1
            user_data = user.to_dict()

            # Analyse de l'université
            university = user_data.get("university", "").lower()
            if university in university_counts:
                university_counts[university] += 1
            else:
                university_counts["other"] += 1

            # Analyse de l'année d'étude
            year = user_data.get("year", "").capitalize()
            if year in year_counts:
                year_counts[year] += 1
            else:
                year_counts["other"] += 1

            # Analyse du statut registered_club_status
            club_status = user_data.get("registered_club_status", "").lower()
            if club_status == "yes":
                registered_club_counts["yes"] += 1
            else:
                registered_club_counts["no"] += 1

            # Analyse du nombre de sessions de chat
            chat_sessions = user_data.get("chatsessions", [])
            chat_sessions_counts.append(len(chat_sessions))

        # Calcul des proportions sur 100%
        def compute_percentage(count):
            return round((count / total_users * 100), 2) if total_users > 0 else 0

        university_distribution = {key: compute_percentage(value) for key, value in university_counts.items()}
        year_distribution = {key: compute_percentage(value) for key, value in year_counts.items()}
        club_status_distribution = {key: compute_percentage(value) for key, value in registered_club_counts.items()}

        # Calcul des statistiques sur les sessions de chat
        avg_chatsessions = round(sum(chat_sessions_counts) / total_users, 2) if total_users > 0 else 0
        max_chatsessions = max(chat_sessions_counts) if chat_sessions_counts else 0
        min_chatsessions = min(chat_sessions_counts) if chat_sessions_counts else 0

        results = {
            "total_users": total_users,
            "university_distribution": university_distribution,
            "year_distribution": year_distribution,
            "chat_sessions_stats": {
                "average": avg_chatsessions,
                "max": max_chatsessions,
                "min": min_chatsessions
            },
            "registered_club_status_distribution": club_status_distribution
        }

        logging.info(f"✅ Analyse des utilisateurs après {since_date} terminée : {results}")
        return results

    except Exception as e:
        logging.error(f"❌ Erreur lors de l'analyse des utilisateurs : {str(e)}")
        return {"error": "Erreur interne lors de l'analyse des utilisateurs"}

'''
