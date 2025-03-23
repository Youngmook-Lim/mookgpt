from config import NOT_YET_MESSAGE, RETRY_MESSAGE_LABEL, RETRY_MESSAGE

def text_response_format(bot_response):
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": bot_response
                    }
                }
            ],
            "quickReplies": []
        }
    }
    return response


def image_response_format(bot_response, prompt):
    output_text = prompt + " 내용에 관한 이미지입니다."
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleImage": {
                        "imageUrl": bot_response,
                        "altText": output_text
                    }
                }
            ],
            "quickReplies": []
        }
    }
    return response


def time_over():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": NOT_YET_MESSAGE
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": RETRY_MESSAGE_LABEL,
                    "messageText": RETRY_MESSAGE
                }
            ]
        }
    }
    return response