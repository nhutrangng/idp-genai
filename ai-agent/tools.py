import json
import os
import requests
from langchain.tools import tool

@tool
def trigger_backstage_template(payload: str) -> str:
    """Sử dụng công cụ này để tạo dự án mới trên Backstage IDP. Input JSON: project_name, environment."""
    url = "http://localhost:7007/api/scaffolder/v2/tasks"

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return "❌ Định dạng input không hợp lệ. Vui lòng gửi JSON với project_name và environment."

    project_name = data.get("project_name")
    environment = data.get("environment", "dev")

    if not project_name or not isinstance(project_name, str):
        return "❌ Thiếu project_name hợp lệ trong input."

    if environment not in {"dev", "staging", "prod"}:
        return "❌ Environment phải là dev, staging hoặc prod."

    token = os.getenv("BACKSTAGE_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = {
        "templateRef": "template:default/node-js-template",
        "values": {
            "name": project_name,
            "environment": environment,
        },
    }

    try:
        # Gửi yêu cầu POST tới Backstage
        response = requests.post(url, json=body, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            task_id = data.get("id")
            return (f"✅ Đã gửi lệnh tạo dự án **{project_name}** ({environment}) thành công. "
                    f"🔗 Link theo dõi: http://localhost:3000/create/tasks/{task_id}")
        else:
            # Trả về chi tiết lỗi nếu Backstage từ chối (401, 403, 400...)
            return f"❌ Backstage từ chối (Mã {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"🚨 Lỗi kết nối tới hệ thống Backstage: {str(e)}"