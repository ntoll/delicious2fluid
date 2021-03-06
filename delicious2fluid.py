# -*- coding: utf-8 -*-
"""
Grabs all your delicious bookmarks and imports them into FluidDB.

When running the script you'll be asked for your username and password for
both delicious and FluidDB.

Sign up for FluidDB here: https://fluidinfo.com/accounts/new/

By default the following tags will be created in your root namespace (you can
always override this):

USERNAME/title
USERNAME/notes

And the following tags will be created under the delicious namespace to store
metadata:

USERNAME/delicious/hash
USERNAME/delicious/time
USERNAME/delicious/meta
USERNAME/delicious/tag

FluidDB will store the tag values as a collection of strings in the "tag" tag.
In addition each tag you create in delicious will be recreated in FluidDB under
your root namespace:

USERNAME/TAGNAME
"""

import logging
import sys
from getpass import getpass
from xml.dom.minidom import parseString
import httplib2
import urllib
import types
if sys.version_info < (2, 6):
    import simplejson as json
else:
    import json

# Logging
LOG_FILENAME = 'd2f.log'
logger = logging.getLogger('d2f')
logger.setLevel(logging.DEBUG)
logfile_handler = logging.FileHandler(LOG_FILENAME)
logfile_handler.setLevel(logging.DEBUG)
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s -"\
" %(message)s")
logfile_handler.setFormatter(log_format)
logger.addHandler(logfile_handler)

"""
FLUIDDB RELATED FUNCTIONS

Copied directly from the fluiddb.py script. I've just included them here so
this script has *NO* deps outside Python's core. Unit tests for this can be
found in the project hosted on Github: http://github.com/ntoll/fluiddb.py
"""

# There are currently two instances of FluidDB. MAIN is the default standard
# instance and SANDBOX is a scratch version for testing purposes. Data in
# SANDBOX can (and will) be blown away.
MAIN = 'https://fluiddb.fluidinfo.com'
SANDBOX = 'https://sandbox.fluidinfo.com'
instance = MAIN


ITERABLE_TYPES = set((list, tuple))
SERIALIZABLE_TYPES = set((types.NoneType, bool, int, float, str, unicode, list,
                          tuple))


global_headers = {
    'Accept': '*/*',
}


def login(username, password):
    """
    Creates the 'Authorization' token from the given username and password.
    """
    userpass = username + ':' + password
    auth = 'Basic ' + userpass.encode('base64').strip()
    global_headers['Authorization'] = auth


def logout():
    """
    Removes the 'Authorization' token from the headers passed into FluidDB
    """
    if 'Authorization' in global_headers:
        del global_headers['Authorization']


def call(method, path, body=None, mime=None, tags=[], custom_headers={}, **kw):
    """
    Makes a call to FluidDB

    method = HTTP verb. e.g. PUT, POST, GET, DELETE or HEAD
    path = Path appended to the instance to locate the resource in FluidDB this
        can be either a string OR a list of path elements.
    body = The request body (a dictionary will be translated to json,
    primitive types will also be jsonified)
    mime = The mime-type for the body of the request - will override the
    jsonification of primitive types
    tags = The list of tags to return if the request is to values
    headers = A dictionary containing additional headers to send in the request
    **kw = Query-string arguments to be appended to the URL
    """
    http = httplib2.Http()
    # build the URL
    url = build_url(path)
    if kw:
        url = url + '?' + urllib.urlencode(kw)
    if tags and path.startswith('/values'):
        # /values based requests must have a tags list to append to the
        # url args (which are passed in as **kw), so append them so everything
        # gets urlencoded correctly below
        url = url + '&' + urllib.urlencode([('tag', tag) for tag in tags])
    # set the headers
    headers = global_headers.copy()
    if custom_headers:
        headers.update(custom_headers)
    # Make sure the correct content-type header is sent
    if isinstance(body, dict):
        # jsonify dicts
        headers['content-type'] = 'application/json'
        body = json.dumps(body)
    elif method.upper() == 'PUT' and (
        path.startswith('/objects/' or path.startswith('/about'))):
        # A PUT to an "/objects/" or "/about/" resource means that we're
        # handling tag-values. Make sure we handle primitive/opaque value types
        # properly.
        if mime:
            # opaque value (just set the mime type)
            headers['content-type'] = mime
        elif isprimitive(body):
            # primitive values need to be json-ified and have the correct
            # content-type set
            headers['content-type'] = 'application/vnd.fluiddb.value+json'
            body = json.dumps(body)
        else:
            # No way to work out what content-type to send to FluidDB so
            # bail out.
            raise TypeError("You must supply a mime-type")
    response, content = http.request(url, method, body, headers)
    if ((response['content-type'] == 'application/json' or
        response['content-type'] == 'application/vnd.fluiddb.value+json')
        and content):
        result = json.loads(content)
    else:
        result = content
    return response, result


def isprimitive(body):
    """
    Given the body of a request will return a boolean to indicate if the
    value is a primitive value type.

    See:

    http://doc.fluidinfo.com/fluidDB/api/tag-values.html

    &

    http://bit.ly/hmrMzT

    For an explanation of the difference between primitive and opaque
    values.
    """
    bodyType = type(body)
    if bodyType in SERIALIZABLE_TYPES:
        if bodyType in ITERABLE_TYPES:
            if not all(isinstance(x, basestring) for x in body):
                return False
        return True
    else:
        return False


def build_url(path):
    """
    Given a path that is either a string or list of path elements, will return
    the correct URL
    """
    url = instance
    if isinstance(path, list):
        url += '/'
        url += '/'.join([urllib.quote(element, safe='') for element in path])
    else:
        url += urllib.quote(path)
    return url


"""
DELICIOUS BASED FUNCTIONS

The actual logic and processing happens in these functions.
"""


def getBookmarks(username, password):
    """
    Given a user's delicious username and password grabs the XML using the API.
    """
    logger.info('Grabbing bookmarks from delicious')
    http = httplib2.Http()
    login(username, password)
    url = "https://api.del.icio.us/v1/posts/all"
    response, content = http.request(url, 'GET', None, global_headers)
    if response['status'] == '200':
        logger.info('200 OK')
        return content
    else:
        logger.info(response)
        raise Exception("Can't get bookmarks from delicious")


def parseXml(bookmarks):
    """
    Given the eggsmell in bookmarks will return two objects:
        * a set of all tags used
        * a list of dict objects representing the objects to be created in
        FluidDB
    """
    dom = parseString(bookmarks)
    tags = set()
    objects = []
    if dom.firstChild.hasChildNodes():
        tagNodes = [node for node in dom.firstChild.childNodes
            if node.nodeName == u'post']
        for tagNode in tagNodes:
            obj = {}
            # Create the object dict
            for attribute in ['href', 'hash', 'description', 'tag', 'time',
                'extended', 'meta', 'shared']:
                if tagNode.hasAttribute(attribute):
                    # Faffing about to make sure description->title,
                    # extended->notes and "tag" contains a list. Ugly hack :-(
                    if attribute == 'description':
                        key = 'title'
                    elif attribute == 'extended':
                        key = 'notes'
                    else:
                        key = attribute
                    if key == 'tag':
                        obj[key] = tagNode.getAttribute(attribute).split()
                    else:
                        obj[key] = tagNode.getAttribute(attribute)
            # Grab the tags
            for tag in obj['tag']:
                tags.add(tag)
            # Ignore any bookmark that isn't to be shared
            if 'shared' in obj:
                if obj['shared'] == 'no':
                    continue
            objects.append(obj)
    return tags, objects


def createTags(tags, namespace):
    """
    Given a set of tags from delicious will create equivalent tags in FluidDB
    under the given namespace.
    """
    logger.info('Importing %d tags' % len(tags))
    for tag in tags:
        logger.info('Importing %s' % tag)
        url = '/'.join(['/tags', namespace])
        logger.debug(call('POST', url, {'name': tag,
            'description': 'A tag created in delicious & imported to FluidDB',
            'indexed': False}))


def createObjects(objects, namespace, about="href"):
    """
    Given a list of object dicts will make sure a corresponding object is
    created and tagged appropriately in FluidDB. The namespace argument is used
    to indicate where the tags representing the object's fields are to be
    created. The about argument references the field to use as the unique
    value for the about tag of each object.
    """
    logger.info('Creating tags for object fields')
    for key in objects[0].keys():
        url = '/'.join(['/tags', namespace])
        if key == 'href':
            # ignore href since its the value of the about tag
            continue
        elif not key in ['title', 'notes']:
            url = '/'.join([url, 'delicious'])
        logger.debug(call('POST', url, {'name': key,
            'description': 'A tag generated from meta-data from delicious',
            'indexed': False}))
    logger.info('Creating/tagging %d objects' % len(objects))
    for obj in objects:
        logger.info('Creating/getting object about: %s' % obj[about])
        logger.debug(call('POST', '/objects', {'about': obj[about]}))
        logger.info('Adding metadata fields to the object.')
        # query to identify the object we're interested in
        query = 'fluiddb/about="%s"' % obj[about]
        # build the dict that defines the values to tag
        payload = {}
        for key in obj.keys():
            if key == 'href':
                # ignore 'href' as it's the about tag value
                continue
            elif not key in ['title', 'notes']:
                path = '/'.join([namespace, 'delicious', key])
            else:
                path = '/'.join([namespace, key])
            value = {"value": obj[key]}
            payload[path] = value
        for tag in obj['tag']:
            path = '/'.join([namespace, tag])
            value = {"value": None}
            payload[path] = value
        logger.debug(call('PUT', '/values', payload, query=query))


def createNamespace(parent, path):
    """
    Recursively creates a namespace path from a list of namespaces
    """
    if path:
        logger.debug(call('POST', '/namespaces/%s' % parent,
            {'name': path[0],
            'description': 'Holds tags imported from delicious'}))
        createNamespace('/'.join([parent, path[0]]), path[1:])


def importIntoFluidDB(tags, objects, fdb_username, fdb_password, fdb_root):
    """
    Sets up the correct state in FluidDB for the import of the tags from
    delicious
    """
    # set up things in FluidDB
    logger.info('Creating delicious namespace in FluidDB')
    login(fdb_username, fdb_password)
    if fdb_root == fdb_username:
        # create the delicious namespace
        createNamespace(fdb_root, ['delicious', ])
    else:
        # not importing to the user's root namespace so create the bespoke
        # namespace path.
        path = fdb_root.split('/')
        path.append('delicious')
        createNamespace(path[0], path[1:])
    createTags(tags, fdb_root)
    createObjects(objects, fdb_root)


def run():
    """
    Grabs user input and coordinates the calling of the various functions
    required to export from delicious and import into FluidDB.
    """
    del_username = raw_input("Delicious username: ").strip()
    del_password = getpass("Delicious password: ").strip()
    fdb_username = raw_input("FluidDB username: ").strip()
    fdb_password = getpass("FluidDB password: ").strip()
    fdb_root = raw_input("FluidDB path (hit return to default to root"\
        " namespace: %s)" %
        fdb_username).strip()
    if not fdb_root:
        fdb_root = fdb_username
    # console logger handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(log_format)
    logger.addHandler(ch)
    # grab from delicious
    bookmarks = getBookmarks(del_username, del_password)
    # parse the eggsmell into something useful
    tags, objs = parseXml(bookmarks)
    # import the results into FluidDB
    importIntoFluidDB(tags, objs, fdb_username, fdb_password, fdb_root)
    # fin!
    logger.info('Finished! :-)')
