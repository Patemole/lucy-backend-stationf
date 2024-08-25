import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from botocore.exceptions import ClientError
from typing import List
import uvicorn
#from your_aws_module import fetch_request_data_from_dynamo  # Import the function that interacts with AWS DynamoDB
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

'''
# Endpoint to handle the filtered request data
@app.post("/requests_filtered", response_model=RequestDataResponseModel)
async def get_filtered_request_data(request_data: RequestDataModel):
    try:
        # Call the AWS DynamoDB handler function
        response_data = await fetch_request_data(request_data.timeFilter)#, request_data.universityFilter)
        
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
'''



# Start the FastAPI app
def create_app():
    return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)




'''
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError, EmailStr
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import uvicorn
from student_app.database.dynamo_db.feedback import store_feedback_async
from student_app.database.dynamo_db.academic_advisor_email import store_academic_advisor_email_async


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

# Environment variables
load_dotenv()

# AWS configuration (not used directly in this example, but kept for reference)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# FastAPI app configuration
app = FastAPI(
    title="Chat Service",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for requests
class FeedbackWrongAnswerModel(BaseModel):
    userId: str
    chatId: str
    aiMessageContent: str
    humanMessageContent: str
    feedback: str

    
class GeneralFeedbackModel(BaseModel):
    userId: str
    feedback: str
    courseId: str


class AcademicAdvisorEmailModel(BaseModel):
    email: EmailStr
    uid: str



@app.post("/wrong_answer")
async def submit_feedback_wrong_answer(feedback: FeedbackWrongAnswerModel):
    try:
       
        await store_feedback_async(uid=feedback.userId, feedback=feedback.feedback,chat_id=feedback.chatId, ai_message=feedback.aiMessageContent,human_message=feedback.humanMessageContent)
        return {"message": "Feedback on wrong answer received successfully"}
    
    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logging.error(f"Error inserting message into feedback database: {error_code} - {error_message}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





@app.post("/feedback_answer")
async def submit_feedback_answer(feedback: GeneralFeedbackModel):
    try:
        #logging.info(f"User: {feedback.userId}")
        #logging.info(f"Page {feedback.courseId}")
        #logging.info(f"Feedback: {feedback.feedback}")
        
        await store_feedback_async(feedback.userId,feedback.feedback,feedback.courseId)
        return {"message": "General feedback received successfully"}
    

    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logging.error(f"Error inserting message into feedback database: {error_code} - {error_message}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





@app.post("/academic_advisor/email")
async def submit_academic_advisor_email(data: AcademicAdvisorEmailModel):
    try:
        # Here, integrate the logic to process the academic advisor's email and uid
        logging.info(f"Academic advisor email received: {data.email}")
        logging.info(f"User ID received: {data.uid}")

        await store_academic_advisor_email_async(data.uid, data.email)
        return {"message": "Academic advisor email received successfully"}
    
    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())



def create_app():
    return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
'''