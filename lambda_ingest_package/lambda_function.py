import boto3
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_aws import BedrockEmbeddings

# Event example
# {
#   "Records": [
#     {
#       "eventVersion": "2.1",
#       "eventSource": "aws:s3",
#       "awsRegion": "us-east-1",
#       "eventTime": "2024-01-15T10:30:00.000Z",
#       "eventName": "ObjectCreated:Put",
#       "userIdentity": {
#         "principalId": "AIDAJDPLRKLG7UEXAMPLE"
#       },
#       "requestParameters": {
#         "sourceIPAddress": "203.0.113.1"
#       },
#       "responseElements": {
#         "x-amz-request-id": "C3D13FE58DE4C810",
#         "x-amz-id-2": "FMyUVURIY8/IgAtTv8xRjskZQpcIZ9KG4V5Wp6S7S/JRWeUWerMUE5JgHvANOjpD"
#       },
#       "s3": {
#         "s3SchemaVersion": "1.0",
#         "configurationId": "testConfigRule",
#         "bucket": {
#           "name": "my-pdf-bucket",
#           "ownerIdentity": {
#             "principalId": "A3NL1KOZZKExample"
#           },
#           "arn": "arn:aws:s3:::my-pdf-bucket"
#         },
#         "object": {
#           "key": "documents/research-paper.pdf",
#           "size": 1024000,
#           "eTag": "d41d8cd98f00b204e9800998ecf8427e",
#           "sequencer": "0A1B2C3D4E5F678901"
#         }
#       }
#     }
#   ]
# }
# context example:
# context.function_name → "pdf-processor-lambda"
# context.get_remaining_time_in_millis() → 45000
# context.aws_request_id → "12345678-1234-1234-1234-123456789012"



s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # 1. Get bucket and file name from S3 event
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event['Records'][0]['s3']['object']['key']

    
    # 2. Download PDF to Lambda's temporary folder
    local_path = f"/tmp/{os.path.basename(object_key)}"
    s3_client.download_file(bucket_name, object_key, local_path)
    print(f"Processing file: {object_key}")

    
    # 3. Load and split document with LangChain
    loader = PyMuPDFLoader(local_path)
    documents = loader.load()
    # Tweak a lot!
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)

    
    # 4. Create embeddings with Bedrock
    embeddings = BedrockEmbeddings(
        client=boto3.client('bedrock-runtime'), 
        model_id="amazon.titan-embed-text-v1"
    )


    # 5. Initialize Vector Store and add documents
    vector_store = OpenSearchVectorSearch(
    opensearch_url=os.environ.get("OPENSEARCH_ENDPOINT"),
    index_name=os.environ.get('OPENSEARCH_INDEX_NAME'),
    embedding_function=embeddings
)
    vector_store.add_documents(docs, embeddings)

    
    print(f"Document {object_key} processed and added to vector database.")
    return {
        'statusCode': 200, 
        'body': 'Successfully processed'
    }