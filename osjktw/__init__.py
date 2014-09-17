#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import time

import requests
import twitter

def tweet():
    with open("credentials.json") as f:
        creds = json.load(f)

    req = requests.get("http://zuul.openstack.org/status.json")
    content = json.loads(req.content)

    for pipeline in content['pipelines']:
        if pipeline['name'] == 'gate':
            count = sum([sum(map(len, change['heads']))
                         for change in pipeline['change_queues']])
            for change in pipeline['change_queues']:
                # Queue name
                if change['name'] == 'integrated':
                    hours = ((time.time() * 1000 - change['heads'][0][0]['enqueue_time']) / (3600 * 1000))
                    break
            break

    if hours > 4:
        symbol = "😱"
    elif hours > 2:
        symbol = "😓"
    else:
        symbol = "😎"

    api = twitter.Api(**creds)

    status = api.PostMedia('Gate status %s\n'
                           '%d patches in queue\n'
                           'Integrated queue delay: %.1f hours\n'
                           % (symbol, count, hours),
    'http://graphite.openstack.org/render/?from=-8hours&width=500&height=200&margin=10&hideLegend=true&hideAxes=false&hideGrid=false&target=color(stats.gauges.zuul.pipeline.gate.current_changes,%20%276b8182%27)')
