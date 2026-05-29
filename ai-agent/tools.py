# tools.py
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def trigger_backstage_template(project_name: str, environment: str = "dev") -> str:
    """
    Tạo dự án mới và cấp phát hạ tầng thông qua Backstage Scaffolder.
    Gọi tool này khi người dùng muốn tạo project/service hoặc cấp phát hạ tầng.
    """
    base_url = os.environ.get("BACKSTAGE_URL", "http://localhost:7007")
    url = f"{base_url}/api/scaffolder/v2/tasks"

    token = os.environ.get("BACKSTAGE_TOKEN")
    if not token:
        return "❌ Thiếu BACKSTAGE_TOKEN trong môi trường. Vui lòng cấu hình token để gọi API Backstage."

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "templateRef": "template:default/nodejs-service-template",
        "values": {
            "name": project_name,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 201:
            task_id = response.json().get("id", "unknown")
            return (
                "✅ Đã tạo task scaffolder thành công! "
                f"Project='{project_name}', env='{environment}', taskId='{task_id}'."
            )

        if response.status_code == 401:
            return "❌ Lỗi xác thực Backstage. Vui lòng kiểm tra BACKSTAGE_TOKEN."

        return (
            "❌ Backstage từ chối xử lý. "
            f"Status={response.status_code}, detail={response.text}"
        )

    except Exception as e:
        return f"🚨 Lỗi kết nối tới Backstage: {str(e)}"


def get_scaffolder_task(task_id: str) -> dict:
    """Fetch scaffolder task status and output."""
    base_url = os.environ.get("BACKSTAGE_URL", "http://localhost:7007")
    url = f"{base_url}/api/scaffolder/v2/tasks/{task_id}"

    token = os.environ.get("BACKSTAGE_TOKEN")
    if not token:
        return {"error": "Thiếu BACKSTAGE_TOKEN trong môi trường."}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {
            "error": (
                f"Status={response.status_code}, detail={response.text}"
            )
        }
    except Exception as e:
        return {"error": f"Lỗi kết nối tới Backstage: {str(e)}"}


BACKSTAGE_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "trigger_backstage_template",
        "description": "Sử dụng công cụ này ĐỂ TẠO DỰ ÁN MỚI hoặc CẤP PHÁT HẠ TẦNG khi người dùng cung cấp đủ tên dự án và môi trường.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Tên của dự án/component cần tạo (ví dụ: ga-khong-gay, hermosa-app)",
                },
                "environment": {
                    "type": "string",
                    "description": "Môi trường deploy hạ tầng, mặc định là 'dev' nếu người dùng không nói rõ.",
                    "enum": ["dev", "staging", "prod"],
                },
            },
            "required": ["project_name"],
        },
    },
}