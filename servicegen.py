#!/usr/bin/env python

import sys

import re


"""
Docker service installer script for Facetone.
Author: Nimeshka Srimal
"""

# import sys
# import curses
# import ConfigParser
# from os import popen, path

# import editor

# print [ int(x) for x in popen('stty size', 'r').read().split() ]



# f = open('conf.txt', 'rU')
with open('conf.txt') as f:
    lines = f.readlines()

    section = ''
    section_strp = ''

    last_match = ''

    # i = 0
    for a in lines:


        

        match = re.match(r"^\"(.*)\"\).*$",a.strip())
        if match:

            

            if section_strp != "":
                # print '[' + last_match + ']'

                service_type = "nodejs"

                envvars = re.findall(r"(\$GO_VERSION_TAG)",section_strp)
                # envvars = section_strp

                if envvars:
                    service_type = "go"
                    # print "found go tag" + str(envvars)
                    # print envvars
                    # envvars = list(set(envvars))
                    # for i in envvars:
                    #     print i[1:] + ':'
                # else:
                #     print 'No vars'

                print '"{}": {{ type: "{}", configs: [] }}, '.format(last_match, service_type)
                # print '{} "{}": {{ type: "", configs: [] }}, '.format(len(last_match), last_match)

                # i += 1
                # print "\n"
                # print '========================================='

            # print "\n"
            section_strp = ''
            last_match = match.group(1)

        else:
            section_strp += a.strip()




















        
        # if a.strip() != ";;":
        #     section += a
        #     section_strp += a.strip()
        # else:
        #     section = ''
        #     section_strp=''




        # print a.strip()
        # sys.exit()

        # print a


        # print section_strp


        # match = re.match(r"^\"(.*)\"\).*$",a.strip())
        # if match:
            
        #     print '------------------------------'
        #     print match.group(1)
        #     print '------------------------------'

        #     # print section_strp


        #     envvars = re.findall(r"(\$[A-Z_]+)",section_strp)

        #     # envvars = re.match(r"^.*(\$[A-Z]?.*).*$",section_strp)
            
        #     if envvars:
        #         print envvars
        #     else:
        #         print 'nooo'

        #     # print a.strip()
        #     print '========================================='

        #     section_strp = ''


        #     # print match.group(1)
        # else:
        #     section_strp += a.strip()

        




        # match = re.match(r"^\"(.*)\"\).*;;$",a.strip())
        # if match:
        #     print match.group(1)
            

        # print a.strip()
        
        