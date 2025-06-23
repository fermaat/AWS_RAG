import boto3
import os

import json
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate

# ... other LangChain imports for the chain

# event template
# {
#   "httpMethod": "POST",
#   "path": "/query",
#   "headers": {
#     "Content-Type": "application/json",
#     "User-Agent": "Mozilla/5.0..."
#   },
#   "body": "{\"question\": \"What is the main topic of the uploaded document?\"}",
#   "isBase64Encoded": false,
#   "requestContext": {
#     "requestId": "12345678-1234-1234-1234-123456789012",
#     "stage": "prod",
#     "httpMethod": "POST"
#   },
#   "queryStringParameters": null,
#   "pathParameters": null
# }


def lambda_handler(event, context):
    # 1. Extract user question from API Gateway request body
    body = json.loads(event.get('body', '{}'))
    question = body.get('question')
    
    if not question:
        return {
            'statusCode': 400, 
            'body': json.dumps('No question provided.')
        }
    
    print(f"Question received: {question}")
    
    # 2. Initialize LangChain components (Bedrock and Vector Store)
    embeddings = BedrockEmbeddings(client=boto3.client('bedrock-runtime'))
    llm = ChatBedrock(
        client=boto3.client('bedrock-runtime'), 
        model_id="anthropic.claude-3-sonnet-20240229-v1:0"
    )

    vector_store = OpenSearchVectorSearch(
        opensearch_url=os.environ.get("OPENSEARCH_ENDPOINT"),
        index_name=os.environ.get('OPENSEARCH_INDEX_NAME'),
        embedding_function=embeddings
    )
    retriever = vector_store.as_retriever()
    
    # 3. Create and execute RAG chain (Retrieval-Augmented Generation)
    prompt =  ChatPromptTemplate.from_template("""You are a...
    use the context
    {context}
    for answering the question
    {input}
    """
    )
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    response = retrieval_chain.invoke({"input": question})
    answer = response.get("answer", "Could not generate a response.")
    
    
    # 4. Return response through API Gateway (important to include CORS headers)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({'answer': answer})
    }