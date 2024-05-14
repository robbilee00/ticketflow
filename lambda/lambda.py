import json
import boto3
from email.parser import Parser
from datetime import datetime
import requests

def lambda_handler(event, context):
    # Extract relevant information from the S3 event
    s3_event = event['Records'][0]['s3']
    bucket_name = s3_event['bucket']['name']
    object_key = s3_event['object']['key']

    # Download the email content from S3
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    email_content = response['Body'].read().decode('utf-8')

    # Parse the email content
    email_parser = Parser()
    email = email_parser.parsestr(email_content)

    # Extract relevant information from the email
    raised_by = email['From']
    subject = email['Subject']
    description = email.get_payload()
    timestamp = email['Date']

    # Convert the email timestamp to a datetime object
    email_time = datetime.strptime(timestamp, '%a, %d %b %Y %H:%M:%S %z')

    # Create a ticket in the ticket management system
    create_ticket(raised_by, subject, description, email_time)

    return {
        'statusCode': 200,
        'body': json.dumps('Ticket created successfully')
    }

def create_ticket(raised_by, subject, description, timestamp):
    # Make a POST request to your API Gateway endpoint to create a ticket
    api_gateway_url = 'https://uk1vg0ibqh.execute-api.us-east-2.amazonaws.com/stage'
    data = {
        'raised_by': raised_by,
        'subject': subject,
        'description': description,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_gateway_url, json=data, headers=headers)

    if response.status_code == 200:
        print('Ticket created successfully')
    else:
        print('Failed to create ticket')
