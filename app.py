import sys
import os
import pandas as pd

from networksecurity.exception.exception import CustomException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse

from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="./templates")

@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    try:
        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is successful")
    except Exception as e:
        raise CustomException(e, sys)
    
@app.post("/predict")
async def predict_route(request: Request, file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        
        # Load preprocessor and model
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")
        
        # Create network model
        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)
        
        print(df.iloc[0])
        y_pred = network_model.predict(df)
        print(y_pred)
        
        df['predicted_column'] = y_pred
        print(df['predicted_column'])
        
        # Replace -1 with 0 for better readability (optional)
        # df['predicted_column'].replace(-1, 0, inplace=True)
        
        # Save predictions to output directory
        os.makedirs('prediction_output', exist_ok=True)
        df.to_csv('prediction_output/output.csv', index=False)
        
        # Convert dataframe to HTML table
        table_html = df.to_html(classes='table table-striped')
        
        return templates.TemplateResponse("table.html", {"request": request, "table": table_html})
        
    except Exception as e:
        raise CustomException(e, sys)

    
if __name__ == "__main__":
    app_run(app, host="0.0.0.0", port=8000)
