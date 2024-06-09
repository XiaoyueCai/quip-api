import json
import time

import quipclient as quip
import websocket
import _thread as thread
from config import config
from slack import send_message
from logger import logger

HEARTBEAT_INTERVAL = 20


def open_websocket(url):
    def on_message(ws, message):
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

    def on_error(ws, error):
        logger.error("error:")
        logger.error(error)

    def on_close(ws, status_code, msg):
        logger.info(f"### connection closed, status code is {status_code}, msg is{msg} ###")

    def on_open(ws):
        logger.info("### connection established ###")

        def run(*args):
            while True:
                time.sleep(HEARTBEAT_INTERVAL)
                ws.send(json.dumps({"type": "heartbeat"}))

        thread.start_new_thread(run, ())

    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


def main():
    quip_config = config.get("quip")

    quip_client = quip.QuipClient(
        access_token=quip_config.get("access_token"))

    websocket_info = quip_client.new_websocket()
    open_websocket(websocket_info["url"])


if __name__ == "__main__":
    main()
