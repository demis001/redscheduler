import unittest2 as unittest

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from os.path import join, dirname

import mock

# Example config
CONFIG_EXAMPLE = join(dirname(dirname(__file__)), 'redscheduler.config.example')

# Various json response mocks
responses = {
    'Job': {
        'get': {'issue': {
                'subject': 'job1',
                'id': 1,
                'description': '',
                'tracker': {'id': 1, 'name': 'example'},
                'status': {'id': 1, 'name': 'New'},
        }},
        'all': {'issues': [
            {'subject': 'job1', 'id': 1},
            {'subject': 'job2', 'id': 2}
        ]},
        'filter': {'issues': [
            {'subject': 'job1', 'id': 1},
            {'subject': 'job2', 'id': 2}
        ]},
    },
    'issue_status': {
        'all': {'issue_statuses': [
            {"id":1, "name": "New", "is_default": True},
            {"id":2, "name": "In Progress"},
            {"id":3, "name": "Completed", "is_closed": True},
            {"id":4, "name": "Error"}
        ]}
    },
    'attachments': {
        'all': [
                {'id': 1, 'content_url': 'http://foo/bar.txt', 'filename':'bar.txt'},
                {'id': 2, 'content_url': 'http://foo/baz.txt', 'filename':'baz.txt'}
        ]
    }
}

def json_response(json_):
    return mock.Mock(return_value=json_)

class RequestBase(unittest.TestCase):
    def setUp(self):
        self.response = mock.Mock(status_code=200)
        self.patcher_get = mock.patch('requests.get', return_value=self.response)
        self.patcher_post = mock.patch('requests.post', return_value=self.response)
        self.patcher_put = mock.patch('requests.put', return_value=self.response)
        self.patcher_delete = mock.patch('requests.delete', return_value=self.response)
        self.mock_get = self.patcher_get.start()
        self.patcher_post.start()
        self.patcher_put.start()
        self.patcher_delete.start()
        self.addCleanup(self.patcher_get.stop)
        self.addCleanup(self.patcher_post.stop)
        self.addCleanup(self.patcher_put.stop)
        self.addCleanup(self.patcher_delete.stop)
        response = responses['Job']['get']
        response['issue']['attachment'] = {'content_url': 'http://foo/bar.txt'}
        response['upload'] = {'token': '123456'}
        issue_status = responses['issue_status']['all']['issue_statuses']
        response['issue_statuses'] = issue_status
        self.response.iter_content = lambda chunk_size: (str(num) for num in range(0, 5))
        response_mock = mock.Mock()
        self.response.json = json_response(response)
