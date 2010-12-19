import delicious2fluid
import uuid
import unittest


# Generic test user created on the FluidDB Sandbox for the express purpose of
# running unit tests
USERNAME = 'test'
PASSWORD = 'test'


class TestDelicious2Fluid(unittest.TestCase):
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
        self.assertEquals(3, len(tags))
        # There are the expected number of objects (one was ignored)
        self.assertEquals(10, len(objs))
        # The objects have the expected keys
        for attribute in ['href', 'hash', 'title', 'tag', 'time',
            'notes', 'meta']:
            self.assertTrue(attribute in objs[0])

    def testCreateNamespace(self):
        """
        Check that the recursive function works correctly to generate a set of
        namespaces from a given path.
        """
        delicious2fluid.login(USERNAME, PASSWORD)
        parent = 'test'
        unique_ns = str(uuid.uuid4())
        path = [unique_ns, 'foo', 'bar', 'baz']
        try:
            delicious2fluid.createNamespace(parent, path)
            headers, result = delicious2fluid.call('GET',
                '/namespaces/test/%s/foo/bar/baz' % unique_ns)
            # if the end of the path exists then all other parts of the path
            # must've been created too
            self.assertEquals('200', headers['status'])
        finally:
            # clean up
            delicious2fluid.call('DELETE',
                '/namespaces/test/%s/foo/bar/baz' % unique_ns)
            delicious2fluid.call('DELETE',
                '/namespaces/test/%s/foo/bar' % unique_ns)
            delicious2fluid.call('DELETE',
                '/namespaces/test/%s/foo' % unique_ns)
            delicious2fluid.call('DELETE', '/namespaces/test/%s' % unique_ns)

    def testCreateTags(self):
        """
        Checks that a given set of tags from delicious are created in the
        right place in FluidDB.
        """
        delicious2fluid.login(USERNAME, PASSWORD)
        tags = set(['foo', 'bar', 'baz'])
        unique_ns = str(uuid.uuid4())
        try:
            # create the test namespace(s)
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
            # remove the test namespace(s)
            delicious2fluid.call('DELETE', '/namespaces/test/%s' % unique_ns)

    def testCreateObjects(self):
        """
        Checks that objects are created correctly and have the appropriate tags
        associated with them.
        """
        # A couple of mock "objects"
        obj1 = {'foo': 'A', 'bar': 'B', 'tag': 'foo bar', 'title': 'foo bar',
            'notes': 'baz'}
        obj2 = {'foo': 'C', 'bar': 'C', 'tag': 'foo bar', 'title': 'foo bar',
            'notes': 'baz'}
        objs = [obj1, obj2]
        # Set things up
        delicious2fluid.login(USERNAME, PASSWORD)
        tags = set(['foo', 'bar'])
        unique_ns = str(uuid.uuid4())
        try:
            # create the test namespace(s)
            headers, result = delicious2fluid.call('POST', '/namespaces/test',
                {'name': unique_ns, 'description': 'a test namespace'})
            self.assertEquals('201', headers['status'])
            headers, result = delicious2fluid.call('POST',
                '/namespaces/test/%s' % unique_ns,
                {'name': 'delicious', 'description': 'a test namespace'})
            self.assertEquals('201', headers['status'])
            # create the tags
            delicious2fluid.createTags(tags, 'test/%s' % unique_ns)
            # create the objects
            delicious2fluid.createObjects(objs, 'test/%s' % unique_ns,
                about='foo')
            # Check there are two objects tagged with the 'foo' and 'bar' tags
            for tag in tags:
                query_tag = 'has test/%s/%s' % (unique_ns, tag)
                headers, result = delicious2fluid.call('GET', '/objects',
                    query=query_tag)
                # there are two objects that are tagged
                self.assertEquals(2, len(result['ids']))
        finally:
            # remove the tags
            tags.add('tag')
            for tag in tags:
                tag_path = '/tags/test/%s/%s' % (unique_ns, tag)
                tag_path_obj = '/tags/test/%s/delicious/%s' % (unique_ns, tag)
                delicious2fluid.call('DELETE', tag_path)
                delicious2fluid.call('DELETE', tag_path_obj)
            delicious2fluid.call('DELETE', '/tags/test/%s/title' % unique_ns)
            delicious2fluid.call('DELETE', '/tags/test/%s/notes' % unique_ns)
            # remove the test namespaces
            delicious2fluid.call('DELETE',
                '/namespaces/test/%s/delicious' % unique_ns)
            delicious2fluid.call('DELETE', '/namespaces/test/%s' % unique_ns)

    def testImportIntoFluidDB(self):
        """
        Ensures that the steps required to import tags and bookmarks into
        FluidDB behave as expected
        """
        unique_ns = str(uuid.uuid4())
        bookmarks = open('bookmarks.xml', 'r')
        tags, objects = delicious2fluid.parseXml(bookmarks.read())
        try:
            delicious2fluid.importIntoFluidDB(tags, objects, USERNAME,
                PASSWORD, 'test/%s' % unique_ns)
            # check there are delicious tags
            header, result = delicious2fluid.call('GET',
                '/namespaces/test/%s/delicious' % unique_ns, returnTags=True)
            for tag in ['hash', 'tag', 'time', 'meta']:
                self.assertTrue(tag in result['tagNames'])
            self.assertEquals(4, len(result['tagNames']))
            # check we have the imported tags along with the title and notes
            # tags
            header, result = delicious2fluid.call('GET',
                '/namespaces/test/%s' % unique_ns, returnTags=True)
            for tag in ['foo', 'bar', 'baz', 'title', 'notes']:
                self.assertTrue(tag in result['tagNames'])
            self.assertEquals(5, len(result['tagNames']))
            # make sure we have the ten expected objects
            for tag in ['foo', 'bar', 'baz', 'title', 'notes']:
                query_tag = 'has test/%s/%s' % (unique_ns, tag)
                headers, result = delicious2fluid.call('GET', '/objects',
                    query=query_tag)
                # there are two objects that are tagged
                self.assertEquals(10, len(result['ids']))
        finally:
            # clean up
            for tag in ['hash', 'tag', 'time', 'meta']:
                delicious2fluid.call('DELETE',
                    '/tags/test/%s/delicious/%s' % (unique_ns, tag))
            for tag in ['foo', 'bar', 'baz', 'title', 'notes']:
                delicious2fluid.call('DELETE',
                    '/tags/test/%s/%s' % (unique_ns, tag))
            delicious2fluid.call('DELETE',
                    '/namespaces/test/%s' % unique_ns)
