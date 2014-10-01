#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import time

import requests
import twitter


def tweet():
    with open("credentials.json") as f:
        creds = json.load(f)

    api = twitter.Api(**creds)

    try:
        req = requests.get("http://zuul.openstack.org/status.json")
        content = json.loads(req.content)

        for pipeline in content['pipelines']:
            if pipeline['name'] == 'gate':
                count = sum([sum(map(len, change['heads']))
                             for change in pipeline['change_queues']])
                if count:
                    for change in pipeline['change_queues']:
                        # Queue name
                        if change['name'] == 'integrated':
                            hours = ((time.time() * 1000
                                      - change['heads'][0][0]['enqueue_time'])
                                     / (3600 * 1000))
                            break
                break
    except Exception:
        api.PostUpdate("Where is the gate!? 😱")
        # Re raise to have the full trace
        raise

    if count:
        if hours > 12:
            symbol = "😰"
        elif hours > 10:
            symbol = "😤"
        elif hours > 8:
            symbol = "😓"
        elif hours > 4:
            symbol = "😣"
        elif hours > 2:
            symbol = "😠"
        else:
            symbol = "😌"

        text = ('%d patches in queue %s\n'
                'Integrated queue delay: %.1f hours\n' % (count, symbol, hours))
    else:
        text = "The gate is empty 😎 🏖"

    api.PostMedia(
        text,
        'http://graphite.openstack.org/render/'
        '?from=-8hours&width=500&height=200'
        '&margin=10&hideLegend=true&hideAxes=false&hideGrid=false'
        '&target=color(stats.gauges.zuul.pipeline.gate.current_changes,'
        '%20%276b8182%27)')
