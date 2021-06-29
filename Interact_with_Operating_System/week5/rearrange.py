#!/usr/bin/env python3

import re 

def rearrange_name(name):
    result = re.search(r'([\w .]+), ([\w .]*)$',name)
    if result is None:  # It's better for error to crash than failed silently
        return name
    return '{} {}'.format(result[2],result[1])
