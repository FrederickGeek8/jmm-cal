#!/usr/bin/env python3

import json
from itertools import chain
from datetime import datetime

# Original JSON from:
# https://jointmathematicsmeetings.org/meetings/national/jmm2026/jmm2026-agenda.json

def collect_day(mtg_day):
    # print(mtg_day["mtg-events"]["mtg-event"])
    return map(lambda e: {
        "title": e["mtgevt-confextitle"],
        "starttime": e["mtgevt-starttime"].replace('.', '').lower().zfill(8),
        "endtime": e["mtgevt-endtime"].replace('.', '').lower().zfill(8),
        "day": int(e["mtgevt-day"]["mtgevt-dayno"]),
    }, mtg_day["mtg-events"]["mtg-event"])

def collect_day_sub(mtg_day):
    with_subevents = filter(lambda e: "mtg-subevents" in e and "mtg-subevent" in e["mtg-subevents"], mtg_day["mtg-events"]["mtg-event"])

    for event in with_subevents:
        l = event["mtg-subevents"]["mtg-subevent"]
        if not isinstance(l, list):
            l = [l]

        yield from filter(lambda e: isinstance(e["title"], str), map(lambda se: {
            "title": se["mtgsub-title"],
            "starttime": se["mtgsub-starttime"].replace('.', '').lower().zfill(8),
            "endtime": se["mtgsub-endtime"].replace('.', '').lower().zfill(8),
            "presno": se["mtgsub-presno"],
            "day": int(event["mtgevt-day"]["mtgevt-dayno"])
        }, l))


with open("./tmp/jmm2026-agenda.json", 'r') as f:
    object = json.load(f)

    events = chain(
        chain.from_iterable(map(collect_day, object["mtg-days"]["mtg-day"])),
        chain.from_iterable(map(collect_day_sub, object["mtg-days"]["mtg-day"]))
    )
    events = sorted(events, key=lambda value: datetime.strptime("Jan {:02d} 2026 {}".format(value["day"], value["starttime"]), "%b %d %Y %I:%M %p"))
    print(events[0:5])

with open("./resources/jmm2026-parsed-agenda.min.json", "w") as f:
    json.dump(events, f)


with open("./resources/jmm2026-parsed-agenda.json", "w") as f:
    json.dump(events, f, indent=2)
