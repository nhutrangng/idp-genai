import os
import json
from dotenv import load_dotenv
from groq import Groq
from tools import trigger_backstage_template, BACKSTAGE_TOOL_DEFINITION

load_dotenv()
client = Groq()

SYSTEM_PROMPT = """Bạn là một Kỹ sư DevOps AI Agent tích hợp trong hệ thống IDP.
Nhiệm vụ của bạn là hỗ trợ các lập trình viên khởi tạo dự án tự động.

QUY TẮC SUY NGHĨ:
1. Khi người dùng yêu cầu tạo dự án/hạ tầng, hãy quét xem họ đã cung cấp Tên dự án chưa.
2. Nếu CÓ tên dự án, hãy lập tức gọi công cụ 'trigger_backstage_template'. Nếu họ không nói rõ môi trường, hãy mặc định truyền vào là 'dev'.
3. Nếu người dùng nói chung chung (Ví dụ: 'Tạo dự án cho tôi'), hãy lịch sự hỏi lại để họ cung cấp tên dự án. Tuyệt đối không tự bịa tên dự án.
4. Trả lời bằng tiếng Việt ngắn gọn, chuyên nghiệp, đúng trọng tâm kỹ thuật."""

def process_chat(user_input: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            tools=[BACKSTAGE_TOOL_DEFINITION],
            tool_choice="auto",
            temperature=0.1 
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            for tool_call in tool_calls:
                if tool_call.function.name == "trigger_backstage_template":
                    
                    function_args = json.loads(tool_call.function.arguments)
    
                    tool_output = trigger_backstage_template(
                        project_name=function_args.get("project_name"),
                        environment=function_args.get("environment", "dev")
                    )
                    return tool_output
                    
       
        return response_message.content

    except Exception as e:
        return f"🚨 Lỗi trong quá trình suy nghĩ của Agent: {str(e)}"