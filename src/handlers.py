import os
import logging
import json
from slackclient import SlackClient

BOT_TOKEN = os.environ['BOT_TOKEN']
VERIFICATION_TOKEN = os.environ['VERIFICATION_TOKEN']
sc = SlackClient(BOT_TOKEN)


def message_handler(event, context):
    """
    Handle incoming message.im event received via HTTP from Slack Dr Gut bot.
    """


    body = json.loads(event['body'])

    if 'challenge' in body:
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'challenge': body['challenge']
            })
        }
        return response

    event_details = body['event']

    if 'bot_id' in event_details:
        logging.warn('Bot message, ignored.')
    else:
        message = f'Hello {event_details["user"]}'

        sc.api_call(
            'chat.postMessage',
            channel=event_details['channel'],
            text=message,
            as_user=True
        )

    return {'statusCode': 200}
