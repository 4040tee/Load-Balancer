import os
import datetime
from datetime import timezone, timedelta
import time
import argparse
from urllib.parse import urlparse
import sys

x = datetime.datetime.now().astimezone()
y = x + timedelta(hours = 2)
x = x.strftime('%a, %d %b %Y %H:%M:%S %Z')
y =y.strftime('%a, %d %b %Y %H:%M:%S %Z')
print(x)
print(y)
if (x>y): print('comparison true')
#strftime('%a, %d %b %Y %H:%M:%S %Z')

string = 'sy'
x = string.split(':')


print('\n')

#a = '{:%a, %d %b %Y %H:%M:%S %Z}'.format(datetime.datetime.fromtimestamp(os.path.getmtime('test.txt')).astimezone().astimezone(timezone.utc))
#b = datetime.datetime.fromtimestamp(os.path.getctime('test.txt')).astimezone().astimezone(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %Z')
#c =  (datetime.datetime.fromtimestamp(os.path.getctime('test.txt')).astimezone().astimezone(timezone.utc) + timedelta(hours = 2)).strftime('%a, %d %b %Y %H:%M:%S %Z')
#print(a + '\n' + b + '\n' + c)

#if(a<c): print('compared')

"""
proxy = ''
parser = argparse.ArgumentParser()
parser.add_argument("url", help="URL to fetch with an HTTP GET request")
parser.add_argument('-proxy', type = str)
args = parser.parse_args()

# Check the URL passed in and make sure it's valid.  If so, keep track of
# things for later.


try:
    parsed_url = urlparse(args.url)
    if ((parsed_url.scheme != 'http') or (parsed_url.port == None) or (parsed_url.path == '') or (parsed_url.path == '/') or (parsed_url.hostname == None)):
        raise ValueError
    host = parsed_url.hostname
    port = parsed_url.port
    file_name = parsed_url.path
    file_path = file_name.split('/')
    print(host + str(port) + file_name)
except ValueError:
    print('Error:  Invalid URL.  Enter a URL of the form:  http://host:port/file')
    sys.exit(1)
try:
    proxy = args.proxy
    proxy_list = proxy.split(':')
    proxyHost = proxy_list[0]
    proxyPort = proxy_list[1]
    print(proxyHost + ' ' + proxyPort)
    """