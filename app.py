import boto3    # used to invoke foundation model from aws bedrock
import botocore.config
import json

from datetime import datetime

def blog_generate_using_bedrock(blogtopic: str)-> str:
    # create prompt for model 
    prompt = f"""<s>[INST]Human: Write a 200 words blog on this topic {blogtopic}
    Assistant: [/INST]
    """
    # create api body for invoking the model as per amazon bedrock instructions
    body = {
        "prompt":prompt,
        "max_gen_len":512,
        "temperature":0.5,
        "top_p":0.9
    }

    try:
        # invoking the models with config and body
        bedrock = boto3.client("bedrock-runtime",region_name="us-east-1",
                               config=botocore.config.Config(read_timeout=300,retries={'max_attempts':3}))
        response = bedrock.invoke_model(body=json.dumps(body),modelId="meta.llama3-70b-instruct-v1:0")

        response_content = response.get("body").read()
        response_data = json.loads(response_content)
        print(response_data)
        blog_details = response_data["generation"]
        return blog_details
    except Exception as e:
        print(f"Error in generating the blog:{e}")
        return ""
    
def save_blog_to_s3(s3_key,s3_bucket,generated_blog):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=s3_bucket,Key=s3_key, Body = generated_blog)
        print("blog saved")
    except Exception as e:
        print("error while saving blog")



    
def lambda_handler(event, context):
    # triigered when api is hit through amazon api gateway

    # we extract the topic from api body
    event = json.loads(event['body'])
    blogtopic = event['blog_topic']

    # we generate blog by calling amazon bedrock

    generated_blog = blog_generate_using_bedrock(blogtopic=blogtopic)

    # we save the blog topic in s3 bucket

    if generated_blog:
        time = datetime.now().strftime('%H%M%S')
        s3_key = f"blog_output/{time}.txt"
        s3_bucket = 'aws-bedrock-blog-proj'
        save_blog_to_s3(s3_key=s3_key,s3_bucket=s3_bucket,generated_blog=generated_blog)
        print("code saved to s3")
    else:
        print("Error while saving code to s3")


    return {
        'statusCode': 200,
        'body': json.dumps('Blog generation is completed!')
    }