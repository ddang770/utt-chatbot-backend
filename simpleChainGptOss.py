#from langchain_community.llms import CTransformers
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Cau hinh


# Load LLM
def load_llm():
    llm = ChatOpenAI(
        api_key=getenv("OPENROUTER_API_KEY"),
        base_url=getenv("OPENROUTER_BASE_URL"),
        model="openai/gpt-oss-20b:free",
        temperature=0.01
    )
    return llm

# Tao prompt template
def creat_prompt(template):
    prompt = PromptTemplate(template = template, input_variables=["question"])
    return prompt


# Tao simple chain
def create_simple_chain(prompt, llm):
    #llm_chain = LLMChain(prompt=prompt, llm=llm)
    llm_chain = prompt | llm
    return llm_chain

# Chay thu chain

template = """<|im_start|>system
Bạn là một trợ lí AI hữu ích. Hãy trả lời người dùng một cách chính xác.
<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""

prompt = creat_prompt(template)
llm = load_llm()
llm_chain = create_simple_chain(prompt, llm)

question = "Một cộng một bằng mấy?"
response = llm_chain.invoke({"question":question})
print(response.content)
