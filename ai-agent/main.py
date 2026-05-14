import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from agent import process_chat
from dotenv import load_dotenv

load_dotenv()

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
app_handler = SlackRequestHandler(slack_app)
api = FastAPI(title="GenAI IDP Agent Server")

@slack_app.message(".*")
def handle_message(message, say):
    user_text = message.get('text')
    
    say("Đang phân tích yêu cầu cấp phát hạ tầng...") 
    
    ai_response = process_chat(user_text)
    say(ai_response)

@api.post("/slack/events")
async def slack_events(req: Request):
    """Endpoint hứng Webhook (tin nhắn) gửi từ máy chủ Slack"""
    return await app_handler.handle(req)

class DeploymentResult(BaseModel):
    project_name: str
    status: str
    resource_url_or_ip: str
    slack_channel_id: str

@api.post("/callback/terraform")
async def terraform_callback(result: DeploymentResult):
    """Endpoint hứng tín hiệu khi quá trình Terraform chạy xong"""
    if result.status == "success":
        msg = f"🎉 Hoàn tất cấp phát hạ tầng AWS cho dự án *{result.project_name}*!\n🌐 Tài nguyên sẵn sàng tại: {result.resource_url_or_ip}"
    else:
        msg = f"🚨 Quá trình tạo hạ tầng AWS cho *{result.project_name}* thất bại. Vui lòng kiểm tra lại log."
        
    slack_app.client.chat_postMessage(channel=result.slack_channel_id, text=msg)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 AI Agent Server is running on port 8000...")
    uvicorn.run(api, host="0.0.0.0", port=8000)