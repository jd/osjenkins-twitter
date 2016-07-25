#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import time
import sys

import requests
import retrying
import six
import twitter


@retrying.retry(stop_max_attempt_number=5)
def get(url):
    return requests.get(url)


def tweet():
    with open("credentials.json") as f:
        creds = json.load(f)

    api = twitter.Api(**creds)

    try:
        req = get("http://zuul.openstack.org/status.json")
        content = json.loads(req.content)

        check_jobs = None
        gate_jobs = None
        hours = None
        for pipeline in content['pipelines']:
            if pipeline['name'] == 'gate':
                gate_jobs = sum([sum(map(len, change['heads']))
                                 for change in pipeline['change_queues']])
            if pipeline['name'] == 'check':
                check_jobs = sum([sum(map(len, change['heads']))
                                  for change in pipeline['change_queues']])
            for change in pipeline['change_queues']:
                if change['heads']:
                    hours = max(hours,
                                ((time.time() * 1000
                                  - change['heads'][0][0]['enqueue_time'])
                                 / (3600 * 1000)))
    except Exception:
        exc = sys.exc_info()
        try:
            api.PostUpdate("Where is the gate!? 😱")
        except Exception:
            pass
        # Re raise to have the full trace
        six.reraise(*exc)

    text = []
    if check_jobs is not None:
        text.append("Check: %d patches in queue" % check_jobs)
    if gate_jobs is not None:
        text.append("Gate: %d patches in queue" % gate_jobs)

    if hours is not None:
        if hours > 16:
            symbol = "😭"
        elif hours > 12:
            symbol = "😰"
        elif hours > 10:
            symbol = "😤"
        elif hours > 8:
            symbol = "😓"
        elif hours > 4:
            symbol = "😣"
        elif hours > 2:
            symbol = "😃"
        else:
            symbol = "😌"
        text.append("Queue max delay: %.2f hours %s" % (hours, symbol))

    if not text:
        text.append("I got nothing to do! So relax! 🏖")

    api.PostMedia(
        "\n".join(text),
        "http://graphite.openstack.org/render/?from=-8hours"
        "&height=200&until=now&width=500&bgcolor=ffffff"
        "&fgcolor=000000"
        "&target=color(alias(stats.gauges.zuul.geard.queue.running,%20%27Running%27)"
        ",%20%27blue%27)&target=color(alias(stats.gauges.zuul.geard.queue.waiting,"
        "%20%27Waiting%27),%20%27red%27)"
        "&target=color(alias(stats.gauges.zuul.geard.queue.total,%20%27Total%20Jobs%27),"
        "%20%27888888%27)&target=color(alias(stats.gauges.zuul.geard.workers,%20%27Workers%27),"
        "%20%27green%27)"
        "&title=Zuul%20Job%20Queue&_t=0.2885273156160839#1469459058311")

