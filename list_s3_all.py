import boto3
import os

# Read .env file manually
env_vars = {}
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
except:
    pass

AWS_KEY = env_vars.get('AWS_ACCESS_KEY_ID') or os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET = env_vars.get('AWS_SECRET_ACCESS_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET = env_vars.get('AWS_STORAGE_BUCKET_NAME') or os.getenv('AWS_STORAGE_BUCKET_NAME')
REGION = env_vars.get('AWS_S3_REGION_NAME') or os.getenv('AWS_S3_REGION_NAME', 'us-east-2')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name=REGION
)

print("=== LISTING ALL S3 OBJECTS (NO PREFIX LIMIT) ===\n")

paginator = s3_client.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=BUCKET)

all_objects = []
for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            all_objects.append(obj)
            print(f"{obj['Key']} - {obj['LastModified']}")

print(f"\n✓ Total objects: {len(all_objects)}")

# Check specifically for test-imagen-s3.png
test_files = [obj for obj in all_objects if 'test-imagen' in obj['Key']]
if test_files:
    print(f"\n✓ Found test image: {test_files[0]['Key']}")
else:
    print(f"\n❌ Test image NOT found in bucket")
