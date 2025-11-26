# Step 1: Install the LangChain Google GenAI package
# !pip install langchain_google_genai

# Step 2: Set up your API key in environment variable (or directly pass it in the code)
import os
from dotenv import load_dotenv
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Step 3: Import the LangChain wrapper for Gemini
from langchain_google_genai import ChatGoogleGenerativeAI

# Step 4: Initialize the Gemini chat model
# RPM = 2
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))
# RPM = 10
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
# RPM = 15
# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
# RPM = 30
# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=os.getenv("GOOGLE_API_KEY"))

# Step 5: Invoke the model with a test prompt
response = llm.invoke("Hello Gemini! Please introduce yourself.")

# Step 6: Print the response
print(response.content)
