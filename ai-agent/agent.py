import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from tools import trigger_backstage_template

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
tools = [trigger_backstage_template]

agent_prefix = (
    "Bạn là Kỹ sư DevOps AI nội bộ của nền tảng IDP.\n"
    "Quy tắc hoạt động khắt khe:\n"
    "1. Chỉ sử dụng công cụ 'trigger_backstage_template' khi người dùng cung cấp ĐỦ tên dự án và môi trường (dev, staging, prod).\n"
    "2. Nếu thiếu một trong hai thông tin, tuyệt đối KHÔNG gọi công cụ. Hãy hỏi lại để bổ sung.\n"
    "3. Trả lời ngắn gọn, trực diện, mang phong cách hệ thống tự động."
)

agent_executor = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prefix": agent_prefix},
)

def process_chat(user_input: str) -> str:
    try:
        result = agent_executor.invoke({"input": user_input})
        return result["output"]
    except Exception as e:
        return f"Hệ thống phân tích AI đang gặp sự cố: {str(e)}"