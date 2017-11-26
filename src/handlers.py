import os
import logging
import json
import boto3
from urllib.parse import parse_qs
from slackclient import SlackClient

BOT_TOKEN = os.environ['BOT_TOKEN']
VERIFICATION_TOKEN = os.environ['VERIFICATION_TOKEN']
dynamodb = boto3.resource('dynamodb')
sc = SlackClient(BOT_TOKEN)


def message_handler(event, context):
    """
    Handle incoming message.im event received via HTTP from Slack Dr Gut bot.
    """
    # The event body is received as a string, not a json object
    body = json.loads(event['body'])

    # Validate the message is coming from our Slack app
    if 'token' not in body or body['token'] != VERIFICATION_TOKEN:
        return {'statusCode': 403}

    # Slack bot verification
    if 'challenge' in body:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'challenge': body['challenge']
            })
        }

    try:
        event_details = body['event']
    except KeyError:
        return {'statusCode': 400}

    if 'bot_id' in event_details:
        logging.warn('Bot message, ignored.')
    elif event_details.get('subtype') == 'message_changed':
        logging.warn('Message change, ignored')
    else:
        user_id = event_details['user']
        table = dynamodb.Table('DrGutUsers')
        user = table.get_item(
            Key={'UserId': user_id}
        ).get('Item')

        if not user:
            table.put_item(
                Item={
                    'UserId': user_id,
                    'needName': True
                }
            )
            message = 'Hi, welcome to Dr Gut Bot!'
            message += '\nPlease enter your name using the `/name` command.'
            sc.api_call(
                'chat.postMessage',
                channel=event_details['channel'],
                text=message,
                as_user=True
            )
        elif user['needName']:
            message = 'Please enter your name using the `/name` command.'
            sc.api_call(
                'chat.postMessage',
                channel=event_details['channel'],
                text=message,
                as_user=True
            )
        else:
            attachment = dynamodb.Table('DrGutQuestions').get_item(
                Key={'QuestionNum': 0}
            ).get('Item').get('attachmentString')
            sc.api_call(
                'chat.postMessage',
                channel=event_details['channel'],
                attachments=[json.loads(attachment)],
                as_user=True
            )

    return {'statusCode': 200}


def question_resp(event, context):
    """
    Handle incoming interactive event received via HTTP from Slack Dr Gut bot.
    """
    # Validate the message is coming from our Slack app
    if 'token' not in event or event['token'] != VERIFICATION_TOKEN:
        return {'statusCode': 403}

    questions = {
        'bowel_movements_normal': 0,
        'bowel_movements': 1,
        'stool_blood': 2,
        'symptom_activity': 3,
        'test_form': 4
    }

    question_num = questions[event['callback_id']]
    user_id = event['user']['id']
    action = event['actions'][0]

    if action['type'] == 'button':
        answer = int(action['value'])
    else:
        answer = int(action['selected_options'][0]['value'])

    dynamodb.Table('DrGutUsers').update_item(
        Key={'UserId': user_id},
        UpdateExpression=f'SET {event["callback_id"]} = :answer',
        ExpressionAttributeValues={':answer': answer}
    )

    if question_num == 4:
        sc.api_call(
            'chat.update',
            channel=event['channel']['id'],
            ts=event['message_ts'],
            text='Thanks for answering!',
            attachments=[],
            as_user=True
        )
        # TODO: implement tally and risk grading
        return None

    attachment = dynamodb.Table('DrGutQuestions').get_item(
        Key={'QuestionNum': question_num + 1}
    ).get('Item').get('attachmentString')

    sc.api_call(
        'chat.update',
        channel=event['channel']['id'],
        ts=event['message_ts'],
        attachments=[json.loads(attachment)],
        as_user=True
    )

    return None


def set_name(event, context):
    """
    Handle incoming /name command from Dr Gut Slack bot.
    """
    logging.warn(event)
    # The event body is received as a string, not a json object
    body = json.loads(json.dumps(parse_qs(event['body'])))

    # Validate the message is coming from our Slack app
    if 'token' not in body or body['token'][0] != VERIFICATION_TOKEN:
        return {'statusCode': 403}

    user_id = body['user_id'][0]
    table = dynamodb.Table('DrGutUsers')
    table.update_item(
        Key={'UserId': user_id},
        UpdateExpression='SET fullName = :user_name, needName = :needName',
        ExpressionAttributeValues={
            ':user_name':  body['text'][0],
            ':needName': False
        }
    )
    user = table.get_item(
        Key={'UserId': user_id}
    ).get('Item')

    if user['fullName'] != body['text'][0]:
        sc.api_call(
            'chat.postMessage',
            channel=body['channel_id'][0],
            text='Failed',
            as_user=True
        )
    else:
        message = 'Thanks!\n'\
            'To continue - type "Start"'
        sc.api_call(
            'chat.postMessage',
            channel=body['channel_id'][0],
            text=message,
            as_user=True
        )

    return {'statusCode': 200}


# message = 'Test message!'

# attachment = dynamodb.Table('DrGutQuestions').get_item(
#     Key={
#         'QuestionNum': 1
#     }
# ).get('Item').get('attachmentString')

# sc.api_call(
#     'chat.postMessage',
#     channel='D8697CR8E',
#     attachments=[json.loads(attachment)],
#     as_user=True
# )
