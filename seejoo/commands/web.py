'''
Created on 2010-12-05

@author: xion

Commands used to access various web services such as Google or Wikipedia.
'''
from seejoo.ext import command
from seejoo.util.common import download
from seejoo.util.strings import strip_html
from xml.etree import ElementTree
import json
import re
import urllib2


MAX_QUERY_RESULTS = 3


##############################################################################
# General commands

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
    items = items[:MAX_QUERY_RESULTS]
    
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

def _get_google_websearch_result_count(json_resp):
    '''
    Extracts number of results from Google Web Search JSON response.
    '''
    if not json_resp:   return
    try:    
        result_count = int(json_resp['responseData']['cursor']['estimatedResultCount'])
    except KeyError:
        return
    
    return result_count
    
    
@command('g')
def google_search(query):
    '''
    Performs a search using Google search engine.
    @warning: Uses deprecated Google Web Search API that has limitations to 100 queries per day.
    '''
    if not query or len(str(query).strip()) == 0:
        return "No query supplied."
    json_resp = _google_websearch(query)
    
    # Parse the response and return first few results
    results = json_resp['responseData']['results'][:MAX_QUERY_RESULTS]
    result_count = _get_google_websearch_result_count(json_resp) 
    
    # Format resulting string
    res = (r['titleNoFormatting'][:40] + " - " + r['unescapedUrl'] for r in results)
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
    result_count = _get_google_websearch_result_count(json_resp)
    return "`%s`: about %s results" % (query, result_count)

@command('gf')
def googlefight(queries):
    '''
    Performs a Googlefight, querying each term and displaying results.
    Queries shall be separated with semicolon.
    '''
    if not queries:
        return "No queries provided."    
    queries = map(str.strip, queries.split(";"))
    
    # Query for each term
    results = []
    for query in queries:
        json_resp = _google_websearch(query)
        count = _get_google_websearch_result_count(json_resp)
        results.append((query, count or 0))
    
    # Format results
    results = sorted(results, key = lambda r: r[1], reverse = True)
    results_str = ["%i. %s (%s)" % (place, r[0], r[1]) for place, r in enumerate(results, 1)]
    
    return " ".join(results_str)


###############################################################################
# Wikipedia commands

def get_wikipage_api_url(title, lang = 'en', format = 'json'):
    ''' 
    Returns an URL to Wikipedia API call that returns content of given page.
    @note: What is actually returned is the list of most recent revisions
    with a limit of 1. 
    '''
    if not title:   return None
    url = "http://%s.wikipedia.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=content&format=%s&titles=%s"
    return url % (lang, format, urllib2.quote(title))

def get_wikipage_content(title):
    '''
    Returns raw markup of given Wikipedia page using API call.
    '''
    url = get_wikipage_api_url(title)
    resp = download(url)
    if not resp:    return None
   
    resp = json.loads(resp)
    try:
        pages = resp['query']['pages']
        page = pages.values()[0]
        content = page['revisions'][0].values()[0]
    except (KeyError, AttributeError), _:
        return None
           
    return content


WIKI_HTML_TAGS = re.compile(r'\<\s*(\w+?)(\s+\w+?\s*\=\s*".*?")*?\s*\>.*?\<\/\s*\1\s*\>')
WIKI_HTML_COMMENTS = re.compile(r"\<\!\-\-.*?\-\-\>", re.DOTALL)
WIKI_UNDERSCORES = re.compile(r"__\w+__")

def get_definition_from_wiki(wiki, chars):
    '''
    Retrieves the beginning of definition text from given Wiki page,
    converted from Wiki markup to plaintext.
    '''
    if not wiki:  return wiki
    
    # Remove a whole lot of unnecessary stuff (order matters!)
    wiki = WIKI_HTML_COMMENTS.sub("", wiki)
    wiki = WIKI_HTML_TAGS.sub("", wiki)
    wiki = WIKI_UNDERSCORES.sub("", wiki)  # __STUFF_LIKE_THIS___
    
    # Find position of first non-whitespace character on top level of
    # double square or curly brackets
    square_depth = 0
    curly_depth = 0
    for i in xrange(0, len(wiki)):
        c = wiki[i]
       
        if c == '[':   square_depth += 1
        elif c == '{':  curly_depth += 1
        elif c == ']':  square_depth -= 1
        elif c == '}':  curly_depth -= 1
        elif not c.isspace() and (square_depth == curly_depth == 0):
            pos = i
            break
    else:
        return None
    text = wiki[pos:]
    
    # Strip unnecessary markup
    text = re.sub(r"\{\{.*?\}\}", "", text)   # Other remaining markup -- requires refinement to support {{convert...}}
    text = re.sub(r"\[\[(.[^\]]*?\|)?(?P<link>.*?)\]\]", lambda m: m.group("link"), text)     # Links
    text = re.sub(r"\'{3}(.*?)\'{3}", lambda m: '"%s"' % m.group(1), text)                    # Quotes
    
    text = re.sub(r"\s+\(\W*?\)", "", text)

    ending = '...'
    chars -= len(ending)
    return text[:chars] + ending
    
        
@command('w')
def wikipedia_definition(term):
    '''
    Looks up given term in English Wikipedia and returns the beginning
    of its definition.
    '''
    if not term or len(str(term).strip()) == 0:
        return "No term supplied."
    
    page = get_wikipage_content(term)
    if not page:
        return "Could not connect to Wikipedia."
    
    wiki_def = get_definition_from_wiki(page, 200)
    if not wiki_def:
        return "Could found the definition in Wikipedia."
    
    # Handle Wikipedia redirects
    if wiki_def.startswith("#REDIRECT"):
        first_line = wiki_def[:wiki_def.find('\n')]
        _, target = first_line.split(None, 1)
        return wikipedia_definition(target)
    
    wiki_url = "http://en.wikipedia.org/wiki/" + urllib2.quote(term)
    return "%s -- from: %s" % (wiki_def, wiki_url)


##############################################################################
# Dictionaries

UD_DEF_DIV = re.compile(r'''
    \< \s* div \s+ class="definition" \s* \>    # Opening tag
        (?P<def>.*?)                            # Definition
    \</div\s*\>                                 # Closing tag
    ''', re.IGNORECASE | re.VERBOSE)

def find_first_sentences(html, s = 1):
    '''
    Find the first few sentences in given string of HTML.
    '''
    dot = re.compile(r"\.\s+")
    
    pos = i = 0
    while i < s:
        m = dot.search(html, pos)
        if not m:   break
        pos = m.end() ; i += 1
        
    return html[:pos] if pos > 0 else html

@command('ud')
def urban_dictionary(term):
    '''
    Looks up given term in urbandictionary.com. Returns the first sentence
    of definition.
    '''
    if not term or len(str(term).strip()) == 0:
        return "No term supplied."
    
    url = "http://www.urbandictionary.com/define.php?term=%s" % urllib2.quote(term)
    ud_site = download(url)
    if not ud_site: return "Could not retrieve definition of '%s'." % term
    
    # Look for definition
    m = UD_DEF_DIV.search(ud_site)
    if m:
        definition = strip_html(m.groupdict().get('def'))
        definition = find_first_sentences(definition, 5)
        if len(definition.strip()) > 0:
            return "'%s': %s" % (term, definition)
    
    return "Could not find definition of '%s'." % term


###############################################################################
# Weather

WEATHER_DIV = re.compile(r'''
    \<\s* div \s+ class="large" \s* \>    # Opening tag
        (?P<degrees>[+-]?\d+)             # Degrees
        .*(\s*\<br\s*/?\>\s*)?
        (?P<comment>.*)                   # Comment
    \</div\s*\>                           # Closing tag
    ''', re.IGNORECASE | re.VERBOSE)
WEATHER_PLACE_DIV = re.compile(r'''
    \<\s* div \s* \> \s* \< \s* span \s+ class="small" \s* \>    # Opening tag
        (?P<place>[\w\s,]+)                                      # Place
    \</span \s* \> \s* \</div \s*\>                              # Closing tag
    ''', re.IGNORECASE | re.VERBOSE)

@command('f')
def weather_forecast(place):
    '''
    Polls thefuckingweather.com (sic) site for current weather data at specific
    place. Returns a text containing current temperature, whether it's raining etc.
    '''
    if not place or len(str(place).strip()) == 0:
        return "No place supplied."
    
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
            
            # Try to fetch the actual place
            m = WEATHER_PLACE_DIV.search(fw_site)
            if m:   place = m.groupdict().get("place", place)
        
            res = "%s: %s^C" % (place, degrees)
            if comment:
                comment = str(comment).lower()
                comment = re.sub(r"\<br\s*/?\>", " ", comment) # Convert br's to spaces
                comment = re.sub(r"\sfucking", "", comment)
                res += " (%s)" % comment
            return res
            
    return "Could not find weather information."

@command('j')
def joke(place):
    jsonData = download("http://api.icndb.com/jokes/random")
    data = json.loads(jsonData)
    return data["value"]["joke"]
