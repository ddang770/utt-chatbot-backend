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


def process_query (user_query: str):
    try:
        prompt = creat_prompt(template)
        llm = load_llm()
        llm_chain = create_simple_chain(prompt, llm)

        response = llm_chain.invoke({"question": user_query})
        #print(response.content)
        if not hasattr(response, 'content'):
            # Nếu response không có thuộc tính content
            return {
                "message": "Success",
                "content": str(response)
            }
            
        return {
            "EM": "Success",
            "EC": 0,
            "DT": response.content
        }
    except Exception as e:
        print(f"Process query error: {str(e)}")  # In ra lỗi để debug
        raise e

#process_query("1 + 1 =?")