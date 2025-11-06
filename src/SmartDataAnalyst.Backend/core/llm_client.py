import os
from openai import AzureOpenAI
from dotenv import load_dotenv


# load environment variables from .env
load_dotenv()


# Retrieve Azure OpenAI settings
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

print(AZURE_OPENAI_ENDPOINT)
print(AZURE_OPENAI_DEPLOYMENT_NAME)

#Initialize Azure OpenAI client
client = AzureOpenAI(azure_endpoint=AZURE_OPENAI_ENDPOINT,
api_key= AZURE_OPENAI_API_KEY,
api_version="2024-12-01-preview")


def ask_llm(prompt: str) -> str:
    """
    Sends a prompt to Azure OpenAI and returns the text output.
    """

    response = client.chat.completions.create(
        # model=AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are an expert Python data analyst."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0.2,
        top_p=1.0,
        model=AZURE_OPENAI_DEPLOYMENT_NAME
    )

    return response.choices[0].message.content