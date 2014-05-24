'''
Created on 2011-06-15

@author: xion

Contains utility functions that don't fint anywhere else.
'''
import urllib2


def download(url, **headers):
    """Downloads content of given URL.
    Additional headers can be passed as keyword arguments.
    """
    def header_arg_to_name(header):
        """Convert header argument (e.g. user_agent) into actual
        HTTP header name (e.g. User-Agent).
        """
        parts = header.split('_')
        return '-'.join(part.capitalize() for part in parts)

    headers = dict((header_arg_to_name(arg), value)
                   for arg, value in headers.items())
    headers.setdefault('User-Agent', "seejoo")

    try:
        req = urllib2.Request(url, headers=headers)
        return urllib2.urlopen(req).read()
    except ValueError:
        return download("http://" + url, **headers)
    except IOError:
        return None
