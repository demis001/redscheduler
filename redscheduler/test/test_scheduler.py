from . import unittest, mock, json_response, CONFIG_EXAMPLE, builtins

from redmine.managers import ResourceManager

from .. import scheduler, config

responses = {
    'Jobs': {
        'get': {'issue': {'subject': 'Job', 'id': 1}},
        'all': {'issues': [{'subject': 'job1', 'id': 1},{'subject': 'job2', 'id': 2}]},
        'filter': {'issues': [{'subject': 'job1', 'id': 1},{'subject': 'job2', 'id': 2}]},
    }
}

class TestRedScheduler(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)

    def test_initializes_correctly(self):
        self.assertEqual(self.redscheduler.url, self.config['siteurl'])
        self.assertEqual(self.redscheduler.key, self.config['apikey'])
        self.assertEqual(self.redscheduler.custom_resource_paths, ('redscheduler.scheduler',))

    def test_gets_jobs_manager(self):
        _jobs = self.redscheduler.Jobs
        self.assertIsInstance(_jobs, scheduler.JobsManager)
        self.assertEqual(
            self.config['jobschedulerproject'],
            _jobs.resource_class.project_id
        )

    def test_returns_normal_redmine_resource_managers(self):
        resource = self.redscheduler.Issue
        self.assertIsInstance(resource, ResourceManager)

class TestJobsManager(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)

    def test_sets_redmine_attribute(self):
        self.assertEqual(
            self.redscheduler.Jobs.redmine,
            self.redscheduler
        )

    def test_sets_correct_resource_class(self):
        self.assertIs(
            self.redscheduler.Jobs.resource_class,
            scheduler.Jobs
        )

class TestJobsResource(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redmine = scheduler.RedScheduler(self.config)
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

    def test_is_redmine_resourcemanager(self):
        from redmine.managers import ResourceManager
        self.assertIsInstance(self.redmine.Jobs, ResourceManager)

    def test_retrieves_only_jobs_from_proj(self):
        self.response.json = json_response(responses['Jobs']['all'])
        issues = self.redmine.Jobs.all()
        self.assertEqual(issues[0].id, 1)
        self.assertEqual(issues[0].subject, 'job1')
        self.assertEqual(issues[1].id, 2)
        self.assertEqual(issues[1].subject, 'job2')
        args, kwargs = self.mock_get.call_args
        params_sent = kwargs['params']
        self.assertEqual(params_sent['project_id'], self.config['jobschedulerproject'])
