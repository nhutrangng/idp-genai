import os
import re
import threading
import time
from fastapi import FastAPI, Request
from pydantic import BaseModel
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from agent import process_chat
from tools import get_scaffolder_task
from dotenv import load_dotenv


load_dotenv()

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
app_handler = SlackRequestHandler(slack_app)

api = FastAPI(title="IDP AI Agent Gateway")

def extract_task_links(task_data: dict) -> list:
    links = task_data.get("output", {}).get("links", []) or []
    if links:
        return links

    for step in task_data.get("steps", []):
        if step.get("id") != "publish":
            continue
        output = step.get("output", {}) or {}
        remote_url = output.get("remoteUrl")
        if not remote_url:
            continue

        return [
            {"title": "Repository", "url": remote_url},
            {"title": "GitHub Actions", "url": f"{remote_url}/actions"},
        ]

    return []

def run_agent_background(user_text: str, say_fn):
    """
    Hàm chạy nền xử lý logic độc lập.
    Giúp gọi model Llama-3.3 mà không làm nghẽn mạch kết nối của Slack.
    """
    ai_response = process_chat(user_text)
    say_fn(ai_response)

    match = re.search(r"taskId='([^']+)'", ai_response)
    if not match:
        return

    task_id = match.group(1)
    ui_base = os.environ.get("BACKSTAGE_UI_URL", "http://localhost:3000")
    say_fn(f"🔎 Đang theo dõi tiến độ task: {ui_base}/create/tasks/{task_id}")

    for _ in range(60):
        task_data = get_scaffolder_task(task_id)
        if "error" in task_data:
            say_fn(f"⚠️ Không lấy được trạng thái task: {task_data['error']}")
            return

        status = task_data.get("status")
        if status in {"completed", "failed", "cancelled"}:
            break

        time.sleep(5)

    task_data = get_scaffolder_task(task_id)
    if "error" in task_data:
        say_fn(f"⚠️ Không lấy được kết quả task: {task_data['error']}")
        return

    status = task_data.get("status")
    if status == "completed":
        links = extract_task_links(task_data)
        if links:
            link_text = "\n".join(
                f"- {item.get('title', 'Link')}: {item.get('url', '')}" for item in links
            )
            say_fn(f"✅ Task hoàn tất. Kết quả:\n{link_text}\n\n📦 Hạ tầng đang deploy, IP sẽ được gửi sau khi workflow hoàn tất.")
        else:
            say_fn("✅ Task hoàn tất nhưng chưa có link output.")
        return

    say_fn(f"❌ Task kết thúc với trạng thái: {status}.")


@slack_app.message(".*")
def handle_all_messages(message, say):
    user_text = message.get('text')
    
    say("🤖 Chờ một xíu, Agent đang phân tích và xử lý hạ tầng...")
    threading.Thread(target=run_agent_background, args=(user_text, say)).start()

@api.post("/slack/events")
async def slack_endpoints(req: Request):
    """Endpoint xử lý xác thực URL và điều hướng sự kiện từ Slack sang Slack Bolt"""
    return await app_handler.handle(req)

class DeploymentResult(BaseModel):
    project_name: str
    status: str
    resource_url_or_ip: str
    slack_channel_id: str

@api.post("/callback/terraform")
async def terraform_callback(result: DeploymentResult):
    """
    Hứng dữ liệu trạng thái cuối cùng sau khi hạ tầng deploy xong 
    để tự động thông báo kết quả nghiệm thu lại cho nhóm Chat.
    """
    if result.status == "success":
        msg = (
            f"🎉 **[Hạ tầng Enterprise]** Quá trình cấp phát cho dự án *{result.project_name}* đã hoàn tất thành công!\n"
            f"🌐 URL/IP truy cập hệ thống: `{result.resource_url_or_ip}`"
        )
    else:
        msg = f"🚨 **[Cảnh báo Hạ tầng]** Quá trình chạy Terraform deploy dự án *{result.project_name}* đã xảy ra lỗi thất bại!"
        
    
    slack_app.client.chat_postMessage(channel=result.slack_channel_id, text=msg)
    return {"status": "completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)