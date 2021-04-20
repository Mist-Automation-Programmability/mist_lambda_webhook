import logging

import json
from requests import post
from jinja2 import Template

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def check_request(event):
    valid_request = True
    if "headers" in event.keys():
        if "x-notify-type" not in event['headers'].keys():
            logger.info("missing x-notify-type")
            valid_request = False
        if "x-notify-url" not in event['headers'].keys():
            logger.info("missing x-notify-url")
            valid_request = False
    else:
        logger.info(f"headers no in event")
        valid_request = False
    print(event)
    logger.info(f'Is Request Valid? {valid_request}')
    return valid_request

def process_webhook(event):
    message_type = event['headers']['x-notify-type']
    event['body'] = json.loads(event['body'])
    messages = []
    logger.info(event)
    if event['body']['topic'] == 'device-updowns':
        template = f"{message_type}-{event['body']['topic']}.json"
        args = {}
        for message in event['body']['events']:
            for key in message.keys():
                args[key] = message[key]
            messages.append(render_events(args, template))
    elif event['body']['topic'] == 'audits':
        template = f"{message_type}-{event['body']['topic']}.json"
        args = {}
        for message in event['body']['events']:
            for message in event['body']['events']:
                for key in message.keys():
                    if key == "message":
                        args[key] = ''.join(ch for ch in message[key] if ch.isalnum())
                    else:
                        args[key] = message[key]
                messages.append(render_events(args, template))
    elif event['body']['topic'] == 'alarms':
        template = f"{message_type}-{event['body']['topic']}.json"
        args = {}
        for message in event['body']['events']:
            for key in message.keys():
                args[key] = message[key]
            messages.append(render_events(args, template))
    elif event['body']['topic'] == 'occupancy-alerts':
        template = f"{message_type}-{event['body']['topic']}.json"
        args = {}
        for events in event['body']['events']:
            logger.info(events)
            for key in events.keys():
                if key != 'alert_events':
                    args[key] = events[key]
            for message in events['alert_events']:
                for key in message.keys():
                    args[key] = message[key]
                messages.append(render_events(args, template))
    status_results = forward_events(messages, event['headers']['x-notify-url'])
    return event['body'], status_results

def forward_events(messages, url):
    status = []
    logger.info(f'length of item list: {len(messages)}')
    for item in messages:
        if item != None:
            r = post(url, data=item)
            status.append(r.status_code)
            logger.info(f'response: {r.content}')
    return status

def render_events(args, template_file):
    results = None
    try:
        with open(template_file) as file_:
            template = Template(file_.read())
        results = template.render(**args)
        logger.info(f'Template: {results}')
    except Exception as e:
        logging.error(f"Error generating template: {e}")
    return results

def lambda_handler(event, context):
    body = {}
    logging.info(f'Incoming Request: {event}')
    if check_request(event):
        statusCode = 200
        body['success'] = True
        body['x-notify-url'] = event['headers']['x-notify-url']
        body['x-notify-type'] = event['headers']['x-notify-type']
        body['response'], body['results'] = process_webhook(event)
    else:
        statusCode = 400
        body['success'] = False
        body['error'] = "Missing required headers"

    responseObject = {}
    responseObject['statusCode'] = statusCode
    responseObject['headers'] = {}
    responseObject['headers']['content-type'] = "application/json"
    responseObject['body'] = json.dumps(body)
    return responseObject
