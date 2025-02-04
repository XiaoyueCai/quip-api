import gc
import json
import threading
import time
from urllib.parse import urlencode

from quipclient import QuipClient
from websocket import WebSocketApp
from config import config
from slack import send_message, status_channel, generate_attachments
from logger import logger

HEARTBEAT_INTERVAL = 20


class HeartbeatThread(threading.Thread):
    def __init__(self, ws: WebSocketApp):
        threading.Thread.__init__(self)
        self.ws = ws

    def run(self):
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            self.ws.send(json.dumps({"type": "heartbeat"}))


def is_valid_json(s):
    try:
        json.loads(s)
    except ValueError:
        return False
    return True


def get_file_url(thread_id: str, file_hash: str, file_name: str) -> str:
    params = {
        "name": file_name
    }
    base_url = f"https://quip.com/-/blob/{thread_id}/{file_hash}"
    query_string = urlencode(params, encoding="utf-8")
    return f"{base_url}?{query_string}"


def open_websocket(url):
    def on_message(ws, message):
        if is_valid_json(message):
            receive_data = json.loads(message)
            data_type = receive_data.get("type")
            thread_data = receive_data.get("thread")
            if data_type == "message":
                msg_data = receive_data.get("message") or {}
                author_name = msg_data.get("author_name")
                text = msg_data.get("text")
                files = msg_data.get("files")
                if author_name and (text or files):
                    attachments = None
                    if files and thread_data:
                        thread_id = thread_data.get("id")
                        file_names = []
                        file_urls = []
                        for file in files:
                            file_name = file.get("name")
                            file_hash = file.get("hash")
                            file_names.append(file_name)
                            file_urls.append(get_file_url(
                                thread_id=thread_id, file_hash=file_hash, file_name=file_name))
                        attachments = generate_attachments(file_names=file_names, file_urls=file_urls)
                    send_message(f"{author_name}: {text or ''}", attachments=attachments)
            if data_type == "alive" or data_type == "heartbeat":
                logger.debug("message")
                logger.debug(json.dumps(receive_data, indent=4))
            else:
                logger.info("message:")
                logger.info(json.dumps(receive_data, indent=4))
        else:
            logger.info(f"message: {message}")

    def on_error(ws, error):
        logger.error("error:")
        logger.error(error)

    def on_close(ws, status_code, msg):
        log_msg = f"### connection closed, status code is {status_code}, msg is{msg} ###"
        logger.info(log_msg)
        send_message(msg=log_msg, channel=status_channel)

    def on_open(ws):
        log_msg = "### connection established ###"
        logger.info(log_msg)
        send_message(msg=log_msg, channel=status_channel)
        HeartbeatThread(ws).start()

    while True:
        try:
            # websocket.enableTrace(True)
            ws_app = WebSocketApp(
                url, on_message=on_message, on_error=on_error, on_close=on_close)
            ws_app.on_open = on_open
            ws_app.run_forever()
        except Exception as e:
            gc.collect()
            logger.warning(f"Websocket connection Error: {e}")
        logger.info("Reconnecting websocket after 5 sec")
        time.sleep(5)


def main():
    quip_config = config.get("quip")
    quip_client = QuipClient(access_token=quip_config.get("access_token"))
    websocket_info = quip_client.new_websocket()
    open_websocket(websocket_info["url"])


if __name__ == "__main__":
    main()
