from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from env_utils import QWEN_API_KEY, QWEN_BASE_URL

# 调用gemini
llm = ChatOpenAI(
    model_name="qwen3.5-plus",
    temperature=0.5,
    api_key=QWEN_API_KEY,
    base_url=QWEN_BASE_URL
)

