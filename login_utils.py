from time import time
from config import LOGIN_PERSIST_SECONDS
import os


def check_login_yn(kakao_request, ssm):
    user_key = kakao_request["userRequest"]["user"]["id"]
    login_list = ssm.describe_parameters(Filters=[{"Key": "Name", "Values": [f"/sessions/{user_key}"]}])
    if login_list["Parameters"]:
        last_login_date = login_list["Parameters"][0]['LastModifiedDate']
        return not is_expired(user_key, last_login_date, ssm)
    else:
        return False


def is_expired(user_key, last_login_date, ssm):
    current_time = time()
    login_time = last_login_date.timestamp()

    if current_time - login_time > LOGIN_PERSIST_SECONDS:
        ssm.delete_parameters(Names=[f"/sessions/{user_key}"])
        return True
    else:
        return False


def verify_login(kakao_request, ssm):
    user_key = kakao_request["userRequest"]["user"]["id"]
    user_utterance = kakao_request["userRequest"]["utterance"]

    if user_utterance.startswith("/login"):
        password = user_utterance.replace("/login", "", 1).strip()
        if password == os.environ["LOGIN_PASSWORD"]:
            ssm.put_parameter(Name=f"/sessions/{user_key}", Value="logged_in", Type="String", Overwrite=True)
            return "login_success"
        else:
            return "login_fail"
    else:
        return "login_needed"