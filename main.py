import gc
import json
import threading
import time

from quipclient import QuipClient
from websocket import WebSocketApp
from config import config
from slack import send_message, status_channel
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


def open_websocket(url):
    def on_message(ws, message):
        if is_valid_json(message):
            receive_data = json.loads(message)
            data_type = receive_data.get("type")
            if data_type == "message":
                msg_data = receive_data.get("message") or {}
                author_name = msg_data.get("author_name")
                text = msg_data.get("text")
                if author_name and text:
                    send_message(f"{author_name}: {text}")
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
