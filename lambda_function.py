from openai import OpenAI
from threading import Thread
from time import time, sleep
from queue import Queue
import os
import json
import boto3
from config import *
from helpers import *
from login_utils import *

ssm = boto3.client("ssm")
secretsmanager = boto3.session.Session().client(service_name="secretsmanager", region_name="ap-northeast-2")

api_key = json.loads(secretsmanager.get_secret_value(SecretId="mookgpt-chatgpt-api-key")["SecretString"]).get("API_KEY")

client = OpenAI(api_key=api_key)

def lambda_handler(event, context):

    kakao_request = json.loads(event["body"])
    response = None

    if check_login_yn(kakao_request, ssm):

        run_flag = False
        start_time = time()

        cwd = "/tmp"
        user_key = kakao_request["userRequest"]["user"]["id"]
        filename = cwd + f"/{user_key}-botlog.txt"
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write("")
        else:
            print("File already exists")

        response_queue = Queue()
        request_respond = Thread(target=response_openai, args=(kakao_request, response_queue, filename))
        request_respond.start()

        while time() - start_time < 3.5:
            if not response_queue.empty():
                response = response_queue.get()
                run_flag = True
                break
            sleep(0.01)

        if not run_flag:
            response = time_over()
        else:
            os.remove(filename)
    else:
        result = verify_login(kakao_request, ssm, secretsmanager)
        match result:
            case "login_success":
                response = text_response_format(LOGIN_SUCCESS_MESSAGE + "\n\n" + HELP_MESSAGE)
            case "login_fail":
                response = text_response_format(LOGIN_FAIL_MESSAGE)
            case "login_needed":
                response = text_response_format(LOGIN_NEEDED_MESSAGE)

    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            'Access-Control-Allow-Origin': '*',
        }
    }


def response_openai(request, response_queue, filename):
    user_utterance = request["userRequest"]["utterance"]

    if RETRY_MESSAGE in user_utterance:
        with open(filename) as f:
            last_update = f.read()
        if len(last_update.split()) > 1:
            kind = last_update.split()[0]
            if kind == "img":
                bot_res, prompt = last_update.split()[1], " ".join(last_update.split()[2:])
                response_queue.put(image_response_format(bot_res, prompt))
            else:
                bot_res = last_update[4:]
                response_queue.put(text_response_format(bot_res))
            db_reset(filename)
    elif user_utterance.startswith("/img"):
        db_reset(filename)
        prompt = user_utterance.replace("/img", "", 1)
        bot_res = get_image_url_from_dalle(prompt)
        response_queue.put(image_response_format(bot_res, prompt))
        save_log = f'img {str(bot_res)} {str(prompt)}'
        with open(filename, "w") as f:
            f.write(save_log)
    elif user_utterance.startswith("/ask"):
        db_reset(filename)
        prompt = user_utterance.replace("/ask", "", 1)
        bot_res = get_text_from_gpt(prompt)
        response_queue.put(text_response_format(bot_res))
        save_log = f'ask {str(bot_res)}'
        with open(filename, "w") as f:
            f.write(save_log)
    elif user_utterance.startswith("/help"):
        db_reset(filename)
        response_queue.put(text_response_format(HELP_MESSAGE))
    elif user_utterance.startswith("/be"):
        db_reset(filename)
        global gpt_system_command
        prompt = user_utterance.replace("/be ", "", 1)
        gpt_system_command = prompt
        response_queue.put(text_response_format(BE_RESPONSE_MESSAGE + "🤖" + prompt + "🤖"))
    elif user_utterance.startswith("/who"):
        db_reset(filename)
        response_queue.put(text_response_format("🤖 현재 MookGPT의 정체성 🤖\n\n" + gpt_system_command))
    else:
        base_response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": BASE_MESSAGE
                        }
                    }
                ],
                "quickReplies": []
            }
        }
        response_queue.put(base_response)


def get_text_from_gpt(prompt):
    message_prompt = [{"role": "system",
                       "content": gpt_system_command}]
    message_prompt += [{"role": "user",
                        "content": prompt}]

    response = client.chat.completions.create(model=os.environ["GPT_MODEL"], messages=message_prompt)
    system_message = response.choices[0].message.content

    return system_message


def get_image_url_from_dalle(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    return image_url


def db_reset(filename):
    with open(filename, 'w') as f:
        f.write("")


