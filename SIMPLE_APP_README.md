# Network Security Phishing Detection - Simple FastAPI Application

## 🚀 Quick Start (No MongoDB Required!)

This application works with **local CSV files** and doesn't require MongoDB Atlas.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

The application will start at: **http://127.0.0.1:8000/**

---

## 📋 API Endpoints

### 1. **GET /** - API Documentation
```bash
curl http://127.0.0.1:8000/
```
- Automatically redirects to `/docs` (Swagger UI)

### 2. **GET /train** - Train the Model
```bash
curl http://127.0.0.1:8000/train
```
- Reads data from `Network_data/phisingData.csv`
- Runs complete training pipeline
- Saves model to `final_model/model.pkl`
- Saves preprocessor to `final_model/preprocessor.pkl`
- Returns: "Training is successful"

### 3. **POST /predict** - Batch Prediction
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -F "file=@sample_input.csv"
```
- Upload CSV file with features (without Result column)
- Returns: HTML table with predictions
- Saves output to `prediction_output/output.csv`

---

## 📁 Project Structure

```
mlops_NetworkSecurity/
├── app.py                              # FastAPI application (NO MongoDB!)
├── main.py                             # Training pipeline runner
├── requirements.txt                    # Dependencies (no pymongo needed)
│
├── templates/
│   └── table.html                      # Prediction results template
│
├── Network_data/
│   └── phisingData.csv                 # Your training data (local CSV)
│
├── final_model/
│   ├── model.pkl                       # Trained model (created after training)
│   └── preprocessor.pkl                # Preprocessing pipeline
│
├── prediction_output/
│   └── output.csv                      # Prediction results
│
├── networksecurity/
│   ├── pipeline/
│   │   └── training_pipeline.py        # Training orchestrator
│   ├── components/                     # ML components
│   ├── utils/
│   │   └── ml_utils/
│   │       └── model/
│   │           └── estimator.py        # NetworkModel class
│   └── constant/
│       └── training_pipeline/
│           └── __init__.py             # Constants (no MongoDB config)
│
└── Artifacts/                          # Training artifacts
```

---

## 🎯 Usage Examples

### Example 1: Train Model
```bash
# Start training with local CSV file
curl http://127.0.0.1:8000/train

# Or visit in browser:
# http://127.0.0.1:8000/train
```

**Training reads from:** `Network_data/phisingData.csv` (your local file)

### Example 2: Make Predictions
```bash
# Upload CSV and get predictions
curl -X POST http://127.0.0.1:8000/predict \
  -F "file=@sample_input.csv" \
  -o predictions.html

# Open predictions.html in browser
```

### Example 3: Python Client
```python
import requests

# Train model
response = requests.get('http://127.0.0.1:8000/train')
print(response.text)  # "Training is successful"

# Batch prediction
with open('sample_input.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://127.0.0.1:8000/predict',
        files=files
    )

# Save HTML results
with open('predictions.html', 'wb') as f:
    f.write(response.content)
```

---

## 📊 Input Data Format

### Training Data (Network_data/phisingData.csv)
- **31 columns**: 30 features + 1 Result column
- **CSV format** with header
- Place your data in `Network_data/phisingData.csv`

### Prediction Data (for /predict endpoint)
- **30 feature columns** (NO Result column)
- **CSV format** with header
- Values: -1, 0, or 1

### Required Features:
```
having_IP_Address, URL_Length, Shortining_Service, having_At_Symbol,
double_slash_redirecting, Prefix_Suffix, having_Sub_Domain, SSLfinal_State,
Domain_registeration_length, Favicon, port, HTTPS_token, Request_URL,
URL_of_Anchor, Links_in_tags, SFH, Submitting_to_email, Abnormal_URL,
Redirect, on_mouseover, RightClick, popUpWidnow, Iframe, age_of_domain,
DNSRecord, web_traffic, Page_Rank, Google_Index, Links_pointing_to_page,
Statistical_report
```

---

## 🗂️ Optional: Using S3 for Data Storage

If you want to use S3 instead of local files:

### 1. Install boto3
```bash
pip install boto3 s3fs
```
(Already commented in requirements.txt - just uncomment)

### 2. Set up AWS credentials
Create `.env` file:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

### 3. Modify DataIngestion component
Update `networksecurity/components/dataingestion.py` to read from S3:
```python
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# In your data ingestion:
s3 = boto3.client('s3')
bucket = os.getenv('S3_BUCKET_NAME')
s3.download_file(bucket, 'phisingData.csv', 'Network_data/phisingData.csv')
```

---

## 🔧 Key Features

### ✅ **No MongoDB Required**
- Works with local CSV files
- Simple file-based storage
- Easy to test and develop

### ✅ **NetworkModel Class**
Located: `networksecurity/utils/ml_utils/model/estimator.py`

Wraps preprocessor and model:
```python
from networksecurity.utils.ml_utils.model.estimator import NetworkModel

network_model = NetworkModel(
    preprocessor=preprocessor,
    model=model
)
predictions = network_model.predict(dataframe)
```

### ✅ **Model Files**
After training, two files are saved to `final_model/`:
- `model.pkl` - Trained ML model
- `preprocessor.pkl` - Data preprocessing pipeline

---

## 🐛 Troubleshooting

### Issue: "No module named 'fastapi'"
```bash
pip install fastapi uvicorn[standard] python-multipart jinja2
```

### Issue: "Model not found"
```bash
# Train the model first
curl http://127.0.0.1:8000/train

# Or run training pipeline directly
python main.py
```

### Issue: "Network_data/phisingData.csv not found"
- Make sure your training data is in the correct location
- File should be: `Network_data/phisingData.csv`
- Must have 31 columns (30 features + Result)

### Issue: Port 8000 already in use
Edit `app.py` last line:
```python
app_run(app, host="0.0.0.0", port=8080)  # Change to 8080
```

### Issue: CSV upload fails
- Ensure CSV has 30 feature columns (no Result column)
- Check file is valid CSV format
- Verify feature names match exactly

---

## 📈 Interactive API Documentation

### Swagger UI
Visit: **http://127.0.0.1:8000/docs**

FastAPI provides automatic interactive API documentation where you can:
- View all endpoints
- Test API calls directly from browser
- See request/response schemas
- Upload files and test predictions

---

## 🚀 Deployment Options

### Option 1: Local Development
```bash
python app.py
```

### Option 2: Production with Gunicorn
```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 3: Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

```bash
docker build -t phishing-detection .
docker run -p 8000:8000 phishing-detection
```

---

## 📦 Data Storage Options

### Option 1: Local Files (Default - Current Setup)
✅ Simple and easy
✅ No configuration needed
✅ Good for development
```
Network_data/phisingData.csv (your local file)
```

### Option 2: S3 Storage (Optional)
- Install: `pip install boto3 s3fs`
- Configure AWS credentials in `.env`
- Modify data ingestion to read from S3
- Upload training data to S3 bucket

### Option 3: Other Cloud Storage
- **Google Cloud Storage**: Use `gcsfs`
- **Azure Blob Storage**: Use `azure-storage-blob`
- Adapt data ingestion component accordingly

---

## 🎉 You're Ready!

### Quick Test:
```bash
# 1. Start the app
python app.py

# 2. Train model
curl http://127.0.0.1:8000/train

# 3. Make predictions
curl -X POST http://127.0.0.1:8000/predict -F "file=@sample_input.csv" -o results.html

# 4. Open results.html in browser
```

### What You Have:
✅ FastAPI web application  
✅ No MongoDB dependency  
✅ Works with local CSV files  
✅ Option to use S3 if needed  
✅ Interactive API docs at /docs  
✅ HTML prediction results  
✅ NetworkModel wrapper class  

Enjoy! 🔒✨
