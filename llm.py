import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# OpenAI LLM instance 

def get_llm():
    return ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


llm = get_llm()
