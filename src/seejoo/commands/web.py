'''
Created on 2010-12-05

@author: xion

Commands used to access various web services such as Google or Wikipedia.
'''
from seejoo.ext import command
import urllib2
import json


MAX_QUERY_RESULTS = 3


@command('test')
def ble(arg, **kwargs):
    return "I've read %s" % arg if arg else "Works."


###############################################################################
# Google

def _google_websearch(query):
    '''
    Performs a query to Google Web Search API and returns resulting JSON object.
    '''
    url = "https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s" % urllib2.quote(query)
    response = urllib2.urlopen(url).read()
    return json.loads(response)
    
@command('g')
def google_search(query, **kwargs):
    '''
    Performs a search using Google search engine.
    @warning: Uses deprecated Google Web Search API that has limitations to 100 queries per day.
    '''
    json_resp = _google_websearch(query)
    
    # Parse the response and return first few results
    results = json_resp['responseData']['results'][:MAX_QUERY_RESULTS]
    result_count = int(json_resp['responseData']['cursor']['estimatedResultCount']) 
    
    # Format resulting string
    res = [r['titleNoFormatting'][:40] + " - " + r['unescapedUrl'] for r in results]
    res = "  |  ".join(res)
    if result_count > MAX_QUERY_RESULTS:
        res += " (and about %s more)" % (result_count - MAX_QUERY_RESULTS)
        
    return res

@command('gc')
def google_search_count(query, **kwargs):
    '''
    Performs a search using Google search engine and returns only the estimated number of results.
    '''
    json_resp = _google_websearch(query)
    result_count = int(json_resp['responseData']['cursor']['estimatedResultCount'])
    return "`%s`: about %s results" % (query, result_count)


###############################################################################
# Wikipedia

# NYI