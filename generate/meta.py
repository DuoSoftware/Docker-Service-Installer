#!/usr/bin/env python

import json
import re

with open('services.json.backup', 'r') as f:
    services = json.load(f)

with open('config.sample.json', 'r') as f:
    config = json.load(f)


regx = re.compile(r"--(.*?)=(.*?)\s")
variables = {}

for k, v in services.iteritems():

    options = regx.findall(v['run_cmd'])

    for opt in options:
        if opt[0] == "env":

            var = opt[1][1:-1].split('=')
            if len(var) == 2:
                if var[1] not in variables:
                    variables[var[1]] = []

                variables[var[1]].append(var[0])
    

print json.dumps(variables, indent=4)