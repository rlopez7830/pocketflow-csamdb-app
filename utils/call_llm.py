import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

def call_llm(prompt):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file or environment variables.")
    
    client = AzureOpenAI(
        api_key=openai_api_key,
        api_version="2024-12-01-preview",
        azure_endpoint="https://aimsoa.iglb.intel.com/",
    )
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ],
        functions=None,
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
