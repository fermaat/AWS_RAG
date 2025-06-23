# AWS RAG System with PDF Processing

A serverless RAG (Retrieval-Augmented Generation) system built on AWS that automatically processes PDF documents and provides intelligent question-answering capabilities.

## Architecture

```
PDF Upload → S3 → Lambda (Processing) → OpenSearch
                                            ↓
API Gateway → Lambda (Query) ← OpenSearch (Vector Search)
                ↓
          Bedrock (Claude) → Response
```

## Components

### 1. PDF Processing Lambda (`pdf_processor_lambda.py`)
- **Trigger**: S3 bucket upload events
- **Function**: 
  - Downloads PDF from S3
  - Extracts text using PyMuPDF
  - Splits text into chunks
  - Generates embeddings with Bedrock
  - Stores vectors in OpenSearch

### 2. Query Lambda (`query_lambda.py`)
- **Trigger**: API Gateway HTTP requests
- **Function**:
  - Receives user questions via API
  - Searches relevant documents in OpenSearch
  - Uses Bedrock Claude for answer generation
  - Returns structured JSON response

## Prerequisites

- AWS Account with appropriate permissions
- Bedrock access enabled in your region
- OpenSearch cluster configured
- S3 bucket for PDF storage

## AWS Services Used

- **AWS Lambda**: Serverless compute
- **Amazon S3**: PDF document storage
- **Amazon Bedrock**: 
  - Embeddings: `amazon.titan-embed-text-v1`
  - LLM: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Amazon OpenSearch**: Vector database
- **API Gateway**: HTTP API interface

## Setup Instructions

### 1. Create S3 Bucket
```bash
aws s3 mb s3://your-pdf-bucket-name
```

### 2. Deploy PDF Processing Lambda

#### Dependencies
Create `requirements.txt`:
```txt
langchain==0.1.0
langchain-aws==0.1.0
langchain-community==0.0.10
langchain-core==0.1.0
boto3==1.34.0
pymupdf==1.23.0
opensearch-py==2.4.0
pydantic==2.5.0
```

#### Package and Deploy
```bash
# Create deployment package
mkdir lambda_package
cd lambda_package
pip install -r requirements.txt -t .
cp ../pdf_processor_lambda.py .
zip -r lambda_package.zip .

# Upload to S3 (packages > 50MB)
aws s3 cp lambda_package.zip s3://your-deployment-bucket/

# Create Lambda function
aws lambda create-function \
  --function-name pdf-processor \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler pdf_processor_lambda.lambda_handler \
  --code S3Bucket=your-deployment-bucket,S3Key=lambda_package.zip
```

### 3. Configure S3 Trigger
```bash
aws lambda add-permission \
  --function-name pdf-processor \
  --principal s3.amazonaws.com \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --source-arn arn:aws:s3:::your-pdf-bucket-name

aws s3api put-bucket-notification-configuration \
  --bucket your-pdf-bucket-name \
  --notification-configuration file://s3-notification.json
```

### 4. Setup OpenSearch Cluster
- Create OpenSearch domain via AWS Console
- Configure security settings
- Note the endpoint URL

### 5. Deploy Query Lambda
```bash
# Set environment variables
aws lambda update-function-configuration \
  --function-name query-processor \
  --environment Variables='{
    "OPENSEARCH_ENDPOINT":"https://your-domain.region.es.amazonaws.com"
  }'
```

### 6. Create API Gateway
```bash
# Create REST API
aws apigateway create-rest-api --name pdf-query-api

# Configure POST method and integration
# Deploy API
```

## Usage

### Upload PDF
```bash
aws s3 cp document.pdf s3://your-pdf-bucket-name/
```

### Query Documents
```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the document?"}'
```

### Example Response
```json
{
  "answer": "Based on the uploaded document, the main topic discusses artificial intelligence applications in healthcare, specifically focusing on machine learning algorithms for medical diagnosis."
}
```

## IAM Permissions

### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-pdf-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpGet"
      ],
      "Resource": "arn:aws:es:*:*:domain/your-opensearch-domain/*"
    }
  ]
}
```

## Monitoring

- **CloudWatch Logs**: Lambda execution logs
- **CloudWatch Metrics**: Function performance metrics
- **X-Ray**: Distributed tracing (optional)

## Limitations

- PDF file size limit: 250MB (Lambda temp storage)
- Lambda timeout: 15 minutes max
- OpenSearch index size depends on cluster configuration
- Bedrock model rate limits apply

## Cost Optimization

- Use Lambda provisioned concurrency for consistent performance
- Implement OpenSearch index lifecycle management
- Monitor Bedrock token usage
- Use S3 storage classes for document archival

## Troubleshooting

### Common Issues

1. **Import errors**: Check deployment package includes all dependencies
2. **Bedrock access**: Ensure model access is enabled in Bedrock console
3. **OpenSearch connection**: Verify security group and IAM permissions
4. **API Gateway CORS**: Ensure proper headers for web applications

### Debug Steps
```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/

# Test Lambda function
aws lambda invoke \
  --function-name pdf-processor \
  --payload file://test-event.json \
  response.json
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see LICENSE file for details


📬 Contact
For questions, collaborations, or feedback, feel free to reach out:

📧 Email: fermaat.vl@gmail.com
🧑‍💻 GitHub: [@fermaat](https://github.com/fermaat)
🌐 [Website](https://fermaat.github.io)
