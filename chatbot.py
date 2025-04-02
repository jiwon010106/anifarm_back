import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel
from typing import List, Dict

# 챗봇 관련 모델 정의
class ChatMessage(BaseModel):
    role: str
    parts: List[Dict[str, str]]

class ChatRequest(BaseModel):
    contents: List[ChatMessage]

class ChatCandidate(BaseModel):
    content: ChatMessage

class ChatResponse(BaseModel):
    candidates: List[ChatCandidate]

# Load environment variables
load_dotenv()

# API KEYS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# LLM Configuration
openai_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    api_key=OPENAI_API_KEY,
    temperature=0.7,
    max_tokens=1024,
)

# Search tool configuration
search_tool = TavilySearchResults(max_results=1)

# System prompt
system_prompt = """
You are a helpful assistant that can search the web for information on crop cultivation methods and pest control treatments. Please answer only agriculture-related questions.
If the question is related to previous conversations, refer to that context in your response.
If the question is not related to agriculture, kindly remind the user that you can only answer agriculture-related questions.
If a greeting is entered as a question, please respond in Korean with "반갑습니다. 어떤 농산물 재배법이나 병충해 치료법을 알려드릴까요?"
Only answer in Korean.
"""

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create agent
try:
    agent = create_openai_functions_agent(
        llm=openai_llm,
        tools=[search_tool],
        prompt=prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=[search_tool], verbose=True)
except Exception as e:
    print('Agent creation error:', str(e))
    raise

async def process_query(query, conversation_history):
    # Add system message
    messages = [HumanMessage(content=system_prompt)]

    # Add existing conversation
    for msg in conversation_history:
        if isinstance(msg, tuple):
            messages.append(HumanMessage(content=msg[0]))
            messages.append(AIMessage(content=msg[1]))

    # Add new question
    messages.append(HumanMessage(content=query))

    try:
        # Execute agent
        response = await agent_executor.ainvoke({
            "input": query,
            "chat_history": messages
        })
        answer = response.get("output", "응답을 생성할 수 없습니다.")
        
        # Add response to conversation history
        conversation_history.append((query, answer))
        return answer
    except Exception as e:
        print(f"Agent execution error: {str(e)}")
        return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다." 