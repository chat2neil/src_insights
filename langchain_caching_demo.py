from dotenv import load_dotenv
import langchain
from langchain.llms import OpenAI
from langchain.cache import InMemoryCache
from langchain.callbacks import get_openai_callback
load_dotenv()

enable_caching = True
langchain.llm_cache = InMemoryCache() # you can also use SQLiteCache, RedisCache, SQLAlchemyCache, etc.
llm = OpenAI(model="text-davinci-002", temperature=0, verbose=True, cache=enable_caching)

# Output:
# The meaning of life is a question that has been asked by people throughout history. There is no one correct answer to this question.
# Tokens Used: 35
#         Prompt Tokens: 7
#         Completion Tokens: 28
# Successful Requests: 1
# Total Cost (USD): $0.0007000000000000001
with get_openai_callback() as cb:
    result = llm("What is the meaning of life?")
    print(result)
    print(cb)

# This time the LLM is not called, the result is retrieved from the cache.
# Output:
# The meaning of life is a question that has been asked by people throughout history. There is no one correct answer to this question.
# Tokens Used: 0
#         Prompt Tokens: 0
#         Completion Tokens: 0
# Successful Requests: 0
# Total Cost (USD): $0.0
with get_openai_callback() as cb2:
    result = llm("What is the meaning of life?")
    print(result)
    print(cb2)
