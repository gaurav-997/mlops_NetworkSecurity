# S3 Sync Setup Guide

## Overview
The training pipeline now includes automatic syncing of artifacts and models to AWS S3 for backup and deployment.

## Features Added

### 1. `sync_artifact_dir_to_s3()`
- Syncs the entire `Artifacts/` directory to S3
- Creates timestamped backups: `s3://bucket/artifacts/NetworkSecurity/YYYYMMDD_HHMMSS/`
- Includes all pipeline outputs: data ingestion, validation, transformation, models, evaluations

### 2. `sync_saved_model_dir_to_s3()`
- Syncs the `final_model/` directory to S3
- Creates two versions:
  - Latest: `s3://bucket/models/NetworkSecurity/latest/`
  - Backup: `s3://bucket/models/NetworkSecurity/backups/YYYYMMDD_HHMMSS/`
- Contains production-ready model.pkl and preprocessor.pkl

## Setup Instructions

### Step 1: Install boto3
```bash
pip install boto3 s3fs
```

Or install from requirements.txt (boto3 is now uncommented):
```bash
pip install -r requirements.txt
```

### Step 2: Configure AWS Credentials

#### Option A: Environment Variables
Create a `.env` file in the project root (copy from `.env.example`):
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
```

#### Option B: AWS CLI Configuration
```bash
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

#### Option C: IAM Role (for EC2/ECS)
If running on AWS infrastructure, attach an IAM role with S3 permissions.

### Step 3: Update S3 Bucket Name
Edit `networksecurity/constant/training_pipeline/__init__.py`:
```python
TRAINING_BUCKET_NAME = "your-actual-bucket-name"
```

Default is: `"netwworksecurity"` (line 60, 66)

### Step 4: Create S3 Bucket
```bash
aws s3 mb s3://your-actual-bucket-name --region us-east-1
```

### Step 5: Verify IAM Permissions
Your AWS credentials need these S3 permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## Usage

### Automatic Sync (Default Behavior)
The S3 sync functions are automatically called at the end of `run_pipeline()`:
```python
from networksecurity.pipeline.training_pipeline import TrainingPipeline

pipeline = TrainingPipeline()
pipeline.run_pipeline()  # Automatically syncs to S3 after model pusher
```

### Manual Sync
You can also call the sync functions manually:
```python
from networksecurity.pipeline.training_pipeline import TrainingPipeline

pipeline = TrainingPipeline()

# Sync only artifacts
pipeline.sync_artifact_dir_to_s3()

# Sync only final model
pipeline.sync_saved_model_dir_to_s3()
```

## S3 Directory Structure

After running the pipeline, your S3 bucket will have:

```
s3://your-bucket-name/
├── artifacts/
│   └── NetworkSecurity/
│       ├── 20260314_143022/      # Timestamped artifact backup
│       │   ├── data_ingestion/
│       │   ├── data_validation/
│       │   ├── data_transformation/
│       │   ├── model_trainer/
│       │   ├── model_evaluation/
│       │   └── final_model/
│       └── 20260314_150045/      # Another run
│
└── models/
    └── NetworkSecurity/
        ├── latest/                # Current production model
        │   ├── model.pkl
        │   └── preprocessor.pkl
        └── backups/
            ├── 20260314_143022/   # Model backup 1
            │   ├── model.pkl
            │   └── preprocessor.pkl
            └── 20260314_150045/   # Model backup 2
```

## Optional Mode (Skip S3 Sync)

If boto3 is not installed, the pipeline will:
- Log a warning message
- Continue running without S3 sync
- Complete successfully

This allows local-only development without requiring AWS credentials.

## Troubleshooting

### Error: "boto3 is not installed"
```bash
pip install boto3 s3fs
```

### Error: "Unable to locate credentials"
Check:
1. `.env` file exists with AWS credentials
2. AWS CLI configured: `aws configure list`
3. Environment variables set: `echo $AWS_ACCESS_KEY_ID`

### Error: "Access Denied"
- Verify IAM permissions include `s3:PutObject` and `s3:GetObject`
- Check bucket policy allows your IAM user/role

### Error: "NoSuchBucket"
```bash
aws s3 mb s3://your-bucket-name --region us-east-1
```

### Slow Upload
- Use S3 Transfer Acceleration (requires bucket configuration)
- Consider using `s3fs` for large files

## Downloading Models from S3

To download a model for deployment:
```python
from networksecurity.cloud.s3_syncer import S3Sync

s3_sync = S3Sync()
s3_sync.sync_folder_from_s3(
    folder_path="./downloaded_model",
    bucket_name="your-bucket-name",
    s3_folder_name="models/NetworkSecurity/latest"
)
```

Or using AWS CLI:
```bash
aws s3 sync s3://your-bucket-name/models/NetworkSecurity/latest ./final_model/
```

## Next Steps

1. Set up versioning on S3 bucket for production safety
2. Configure S3 lifecycle policies to archive old backups to Glacier
3. Set up cross-region replication for disaster recovery
4. Use S3 event notifications to trigger deployment pipelines
5. Integrate with CI/CD for automated model deployment

## Cost Considerations

- S3 Standard storage: ~$0.023/GB/month
- Typical model size: 1-10 MB
- Artifacts per run: 10-100 MB
- Monthly cost for 100 runs: ~$0.25

Use lifecycle policies to move old backups to cheaper storage classes.
