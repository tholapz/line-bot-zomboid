import os
import docker
from fastapi import FastAPI, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import JoinEvent, MessageEvent, TextMessageContent

# Initialize Docker client
docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")


def restart_container(container_name: str):
    try:
        container = docker_client.containers.get(container_name)
        container.restart()
        print(f"Container '{container_name}' restarted successfully.")
    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")
    except docker.errors.APIError as e:
        print(f"Failed to restart container '{container_name}': {e}")

# LINE credentials
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "your_line_channel_secret")
CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN", "your_line_channel_access_token"
)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

app = FastAPI()


# Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")

    # Get request body as text
    body = await request.body()

    # Validate signature
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"status": "ok"}


# Handler for when the bot joins a group chat
@handler.add(JoinEvent)
def handle_join(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        group_id = event.source.group_id
        print(f"Bot invited to group: {group_id}")
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text="Hello everyone! Thanks for adding me to this group 😊."
                    )
                ],
            )
        )


# Handler for when the bot is mentioned
@handler.add(MessageEvent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if not isinstance(event.message, TextMessageContent):
            return
        message_text = event.message.text

        if "zomboid re" in event.message.text:
            container_name = "zomboid-server"
            restart_container(container_name)
            message_text = (
                f"I’ve restarted the `{container_name}` container as requested! 🚀"
            )

        # Reply to the user
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=message_text)],
            )
        )
