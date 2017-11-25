from slackclient import SlackClient
import os


BOT_TOKEN = os.environ["BOT_TOKEN"]
sc = SlackClient(BOT_TOKEN)


def message_handler(event: dict, context: dict):

    if 'challenge' in event:
        return event['challenge']

    event_details = event['event']
    message = {
        'message': f'Hello {event_details["user"]}'
    }

    sc.api_call(
        'chat.postMessage',
        channel=event_details['channel'],
        text=message,
        as_user=True
    )

    return True
