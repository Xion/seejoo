'''
Created on 2010-12-05

@author: xion

Commands used to access various web services such as Google or Wikipedia.
'''
from seejoo.ext import command
from xml.etree import ElementTree
import json
import re
import urllib2


MAX_QUERY_RESULTS = 3

TITLE_RE = re.compile(r'\<\s*title\s*\>(?P<title>.*?)\<\/title\s*\>', re.IGNORECASE)


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
def get_website_title(url):
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

@command('rss')
def get_recent_rss_items(url):
    '''
    Retrieves the few most recent items from the given RSS feed.
    '''
    rss = download(url)
    if not rss: return "Could not retrieve RSS feed."
    rss_xml = ElementTree.ElementTree(ElementTree.fromstring(rss))
    
    # Get title of channel and titles of items
    title = rss_xml._root.find('channel/title').text
    items = [i.text for i in rss_xml._root.findall('channel/item/title')]
    items= items[:MAX_QUERY_RESULTS]
    
    # Construct result
    res = title + " :: "
    res += " | ".join(items)
    return res


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
def google_search(query):
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
def google_search_count(query):
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
    if not wp_site: return "Could not connect to Wikipedia."
    
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
    
    return "Could not find the definition of `%s` in Wikipedia" % term


###############################################################################
# Weather

WEATHER_DIV = re.compile(r'''
    \<\s*div\s+class="large"\s*\>    # Opening tag
        (?P<degrees>[+-]?\d+)        # Degrees
        .*(\s*\<br\s*/?\>\s*)?
        (?P<comment>.*)              # Fucking comment ;P
    \</div\s*\>                      # Closing tag
    ''', re.IGNORECASE | re.VERBOSE)

@command('f')
def weather_forecast(place):
    '''
    Polls thefuckingweather.com (sic) site for current weather data at specific
    place. Returns a text containing current temperature, whether it's raining etc.
    '''
    if len(place) == 0: return "No place supplied."
    url = "http://www.thefuckingweather.com/?zipcode=%s&CELSIUS=yes" % urllib2.quote(place)
    fw_site = download(url)
    if not fw_site: return "Could not retrieve weather information."
    
    # Look up for the contents of <div class="large">
    m = WEATHER_DIV.search(fw_site)
    if m:
        # Get the contents
        degrees = m.groupdict().get("degrees")
        comment = m.groupdict().get("comment")        
        if degrees:
            res = "%s: %s^C" % (place, degrees)
            if comment:
                comment = " ".join(re.split(r"\<br\s*/?\>", comment)) # Convert br's to spaces
                res += " (" + str(comment).lower() + ")"
            return res
            
    return "Could not find weather information."