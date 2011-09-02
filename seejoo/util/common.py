'''
Created on 2011-06-15

@author: xion

Contains utility functions that don't fint anywhere else.
'''
import urllib2


def download(url):
    '''
    Downloads content of given URL.
    '''
    try:
        req = urllib2.Request(url, headers = { 'User-Agent': 'seejoo'})
        return urllib2.urlopen(req).read()
    except ValueError:  return download("http://" + url)
    except IOError:     return None
