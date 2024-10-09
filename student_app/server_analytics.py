import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from botocore.exceptions import ClientError
from typing import List
import uvicorn
from student_app.database.dynamo_db.analytics import fetch_request_data_from_dynamo  # Import the function that interacts with AWS DynamoDB
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




# Start the FastAPI app
def create_app():
    return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)



