import delicious2fluid
import uuid
import unittest

# Generic test user created on the FluidDB Sandbox for the express purpose of
# running unit tests
USERNAME = 'test'
PASSWORD = 'test'

class TestDelisious2Fluid(unittest.TestCase):
    """
    The names of the test methods are pretty self-explanatory. I've made sure
    to comment what's I'm testing if there are various test cases.
    """

    def setUp(self):
        # Only test against the SANDBOX
        delicious2fluid.instance = delicious2fluid.SANDBOX
        delicious2fluid.logout()

    def testParseXml(self):
        """
        Makes sure the correct set and list of object dicts is returned given
        the dummy data in bookmarks.xml
        """
        data = open('bookmarks.xml', 'r')
        bookmarks = data.read()
        data.close()
        tags, objs = delicious2fluid.parseXml(bookmarks)
        # There are the expected number of tags
        self.assertEquals(54, len(tags))
        # There are the expected number of objects
        self.assertEquals(10, len(objs))
        # The objects have the expected keys
        for attribute in ['href', 'hash', 'description', 'tag', 'time',
            'extended', 'meta']:
            self.assertTrue(attribute in objs[0])

    def testCreateTags(self):
        """
        Checks that a given set of tags from delicious are created in the
        right place in FluidDB
        """
        delicious2fluid.login(USERNAME, PASSWORD)
        tags = set(['foo', 'bar', 'baz'])
        unique_ns = str(uuid.uuid4())
        try:
            # create the test namespace
            headers, result = delicious2fluid.call('POST', '/namespaces/test',
                {'name': unique_ns, 'description': 'a test namespace'})
            self.assertEquals('201', headers['status'])
            # create the tags
            delicious2fluid.createTags(tags, 'test/%s' % unique_ns)
            # check they exist
            for tag in tags:
                path = '/tags/test/%s/%s' % (unique_ns, tag)
                headers, result = delicious2fluid.call('GET', path)
                self.assertEquals('200', headers['status'])
        finally:
            # remove the tags
            for tag in tags:
                path = '/tags/test/%s/%s' % (unique_ns, tag)
                delicious2fluid.call('DELETE', path)
            # remove the test namespace
            delicious2fluid.call('DELETE', '/namespaces/test/%s' % unique_ns)
