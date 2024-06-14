from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import config
from logger import logger

slack_config = config.get("slack")
# 使用您的 OAuth 令牌初始化客户端
client = WebClient(token=slack_config.get("oauth_access_token"))
msg_channel = slack_config.get("channel")
status_channel = slack_config.get("status_channel")


def send_message(msg: str = "", channel: str = msg_channel):
    try:
        # 调用 chat_postMessage API 方法，发送消息到指定频道
        response = client.chat_postMessage(
            channel=f'#{channel}',
            text=msg,
        )
        # 确认消息发送成功
        assert response["message"]["text"] == msg
        logger.info("Message sent successfully!")
    except SlackApiError as e:
        # 如果出现错误，打印错误信息
        logger.exception(f"Error sending message: {e.response['error']}")


if __name__ == '__main__':
    author = "test_user"
    text = "test_message"
    send_message(f"{author}: {text}")
