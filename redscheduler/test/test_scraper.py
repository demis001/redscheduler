from . import unittest, mock, json_response, CONFIG_EXAMPLE, builtins

from .. import scraper, config

responses = {
    'jobs': [
            'issue': {
                'id': 1,
				'project': {'id': 1, 'name': 'fooproj'},
				'tracker': {'id': 1, 'name': 'example'},
				'status': {'id': 1, 'name': 'New'},
				'priority': {'id': 1, 'name': 'Normal'},
				'author': {'id': 1, 'name': 'foo bar'},
				'subject': 'foo',
				'description': '/path/to/mysample\r\nattachment: myreference.fasta\r\nmysample',
				'start_date': '2015-01-01',
				'done_ratio': 0,
				'created_on': '2015-01-01T00: 01: 01Z',
				'updated_on': '2015-01-01T00: 01: 01Z'
            },
    ]
}

class TestScraper(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.scraper = scraper.Scraper(self.config)

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

    def test_scrapes_only_trackers_defined_in_config(self)
        self.response.json = json_response(responses['jobs'])
        config_example_job = self.config['job_defs']['example']
        jobs = self.scraper.jobs
        self.assertEqual(jobs[0].command_line, config_example_job['cli'])
