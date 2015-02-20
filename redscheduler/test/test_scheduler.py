from . import unittest, mock, json_response, CONFIG_EXAMPLE, builtins

from redmine.managers import ResourceManager

from .. import scheduler, config

responses = {
    'Job': {
        'get': {'issue': {'subject': 'job1', 'id': 1, 'description': '--arg1 foo\r\n--arg2 bar'}},
        'all': {'issues': [
            {'subject': 'job1', 'id': 1, 'description': '--arg1 foo'},
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
        _jobs = self.redscheduler.Job
        self.assertIsInstance(_jobs, scheduler.JobManager)
        self.assertEqual(
            self.config['jobschedulerproject'],
            _jobs.resource_class.project_id
        )

    def test_returns_normal_redmine_resource_managers(self):
        resource = self.redscheduler.Issue
        self.assertIsInstance(resource, ResourceManager)

class TestJobManager(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)

    def test_sets_redmine_attribute(self):
        self.assertEqual(
            self.redscheduler.Job.redmine,
            self.redscheduler
        )

    def test_sets_correct_resource_class(self):
        self.assertIs(
            self.redscheduler.Job.resource_class,
            scheduler.Job
        )

class TestJobResource(unittest.TestCase):
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
        self.assertIsInstance(self.redmine.Job, ResourceManager)

    def test_job_class_has_correct_members(self):
        self.assertIn('percent_done', scheduler.Job._members)
        self.assertIn('arguments', scheduler.Job._members)
        self.assertIn('status', scheduler.Job._members)

    def test_manager_returns_job_resource(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redmine.Job.get(1)
        self.assertIsInstance(job, scheduler.Job)

    def test_retrieves_only_jobs_from_proj(self):
        self.response.json = json_response(responses['Job']['all'])
        issues = self.redmine.Job.all()
        self.assertEqual(issues[0].id, 1)
        self.assertEqual(issues[0].subject, 'job1')
        self.assertEqual(issues[1].id, 2)
        self.assertEqual(issues[1].subject, 'job2')
        args, kwargs = self.mock_get.call_args
        params_sent = kwargs['params']
        self.assertEqual(params_sent['project_id'], self.config['jobschedulerproject'])

    def test_gets_arguments_for_job(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redmine.Job.get(1)
        self.assertEqual(['--arg1 foo','--arg2 bar'], job.arguments)

    def test_percent_done_property(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redmine.Job.get(1)
        job.percent_done = 100
        self.assertEqual(100, job.done_ratio)
        self.assertEqual(100, job.percent_done)

    def test_status_property_completed(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redmine.Job.get(1)
        self.response.json = json_response(responses['issue_status']['all'])
        job.status = 'New'
        self.assertEqual(1, job.status_id)
        self.assertEqual('New', job.status)
        job.status = 'In Progress'
        self.assertEqual(2, job.status_id)
        self.assertEqual('In Progress', job.status)
        job.status = 'Completed'
        self.assertEqual(3, job.status_id)
        self.assertEqual('Completed', job.status)
        job.status = 'Error'
        self.assertEqual(4, job.status_id)
        self.assertEqual('Error', job.status)

    def test_can_only_set_status_to_invvalid_name_raises_exception(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redmine.Job.get(1)
        self.response.json = json_response(responses['issue_status']['all'])
        self.assertRaises(
            scheduler.InvalidStatus,
            setattr, job, 'status', 'foo'
        )
