import logging
import argparse
from rc_rmq import RCRMQ
import json

rc_rmq = RCRMQ({"exchange": "RegUsr", "exchange_type": "topic"})
tasks = {
    "create_account": None,
    "git_commit": None,
    "dir_verify": None,
    "subscribe_mail_list": None,
    "notify_user": None,
}
logger_fmt = "%(asctime)s [%(module)s] - %(message)s"


def add_account(username, email, full="", reason=""):
    rc_rmq.publish_msg(
        {
            "routing_key": "request." + username,
            "msg": {
                "username": username,
                "email": email,
                "fullname": full,
                "reason": reason,
            },
        }
    )
    rc_rmq.disconnect()


def worker(ch, method, properties, body):
    msg = json.loads(body)
    username = msg["username"]

    if msg["success"]:
        print(f"Account for {username} has been created.")
    else:
        print(f"There's some issue while creating account for {username}")
        errmsg = msg.get("errmsg", [])
        for err in errmsg:
            print(err)

    rc_rmq.stop_consume()
    rc_rmq.delete_queue()


def consume(username, routing_key="", callback=worker, debug=False):
    if routing_key == "":
        routing_key = "complete." + username

    if debug:
        sleep(5)
    else:
        rc_rmq.start_consume(
            {"queue": username, "routing_key": routing_key, "cb": callback}
        )
        rc_rmq.disconnect()

    return {"success": True}


def get_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="verbose output"
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="enable dry run mode"
    )
    return parser.parse_args()


def get_logger(args=None):
    if args is None:
        args = get_args()

    logger_lvl = logging.WARNING

    if args.verbose:
        logger_lvl = logging.DEBUG

    if args.dry_run:
        logger_lvl = logging.INFO

    logging.basicConfig(format=logger_fmt, level=logger_lvl)
    return logging.getLogger(__name__)


def encrypt_name(uname):
    if "." in uname:
        return uname.replace(".", "_dot_")


def decrypt_name(uname):
    if "_dot_" in uname:
        return uname.replace("_dot_", ".")
