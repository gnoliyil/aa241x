import re


def matchIntResponse(query, response):
    return re.match('^' + query + '([0-9]+)\s*$', response)

def matchExactString(query, string, response):
    return re.match('^' + query + string + '\s*$', response)
