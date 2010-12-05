'''
Created on 2010-12-05

@author: xion

Commands used to access various web services such as Google or Wikipedia.
'''
from seejoo.ext import command
import json
import re
import urllib2


MAX_QUERY_RESULTS = 3

TITLE_RE = re.compile(r'\<\s*title\s*\>(?P<title>.*)\<\/title\s*\>', re.IGNORECASE)


##############################################################################
# Utility functions

def download(url):
    '''
    Downloads content of given URL.
    '''
    try:
        req = urllib2.Request(url, headers = { 'User-Agent': 'seejoo'})
        return urllib2.urlopen(req).read()
    except ValueError:  return download("http://" + url)
    except IOError:     return None

def strip_html_tags(data):
    '''
    Strips any HTML-like tags from given data.
    '''
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def strip_html_entities(data):
    '''
    Strips any HTML entity references from given data.
    '''
    p = re.compile(r'&[^;]+;')
    return p.sub('', data)

def normalize_whitespace(data):
    '''
    Normalizes the whitespace in given string, replacing sequences of
    whitespace with single space character.
    '''
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def strip_html(data):
    '''
    Strips HTML tags and stuff from given text, making it plain text.
    '''
    data = strip_html_tags(data)
    data = strip_html_entities(data)
    data = normalize_whitespace(data)
    return data


##############################################################################
# General commands

@command('t')
def get_website_title(url, **kwargs):
    '''
    Retrieves the title of given website and returns it.
    '''
    # Download the page
    site = download(url)     
    if not site:    return "(Could not retrieve page)"
    
    # Find the title and return it
    m = TITLE_RE.search(site)
    if not m:   return "(Untitled)"
    return m.group('title')


###############################################################################
# Google commands

def _google_websearch(query):
    '''
    Performs a query to Google Web Search API and returns resulting JSON object.
    '''
    url = "https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s" % urllib2.quote(query)
    response = download(url)
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
# Wikipedia commands

# Number of sentences returned in definitions
SENTENCES = 1

def find_first_sentences(html):
    '''
    Find the first few sentences in given string of HTML.
    '''
    dot = re.compile(r"\.\s+")
    
    pos = i = 0
    while i < SENTENCES:
        m = dot.search(html, pos)
        if not m:   break
        pos = m.end() ; i += 1
        
    return html[:pos]

def strip_footnotes(data):
    '''
    Removes the footnote references from given data.
    '''
    p = re.compile(r'\[\d+\]')
    return p.sub('', data)

@command('w')
def wikipedia_definition(term):
    '''
    Looks up given term in English Wikipedia and returns first few sentences
    of the definition.
    '''
    if len(term) == 0:  return "No query supplied."
    url = "http://en.wikipedia.org/wiki/%s" % urllib2.quote(term)
    wp_site = download(url)
    
    # Look for <!-- bodytext --> and then the first <p> afterwards
    pos = wp_site.find("<!-- bodytext -->")
    if pos > 0:
        pos = wp_site.find("<p>", pos)
        if pos > 0:
            
            # Found; retrieve the text afterwards, get rid of HTML tags
            # and pick first few sentences
            pos += len("<p>")
            content = strip_html(wp_site[pos:])
            definition = find_first_sentences(content)
            definition = strip_footnotes(definition)
            
            return definition + " --- from: " + url
    
    return "Could not find the definition of `%s`" % term