from . import unittest, mock, json_response, CONFIG_EXAMPLE, builtins

import os.path
from nose.plugins.attrib import attr

from redmine.managers import ResourceManager

from .. import scheduler, config

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

class TestRedScheduler(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)

    def test_initializes_correctly(self):
        self.assertEqual(self.redscheduler.url, self.config['siteurl'])
        self.assertEqual(self.redscheduler.key, self.config['apikey'])
        self.assertEqual(self.config['jobschedulerproject'], self.redscheduler.config['jobschedulerproject'])
        self.assertEqual(self.redscheduler.custom_resource_paths, ('redscheduler.scheduler',))

    def test_gets_jobs_manager(self):
        _jobm = self.redscheduler.Job
        self.assertIsInstance(_jobm, scheduler.JobManager)

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

    def test_ensures_project_id_from_config(self):
        self.assertEqual(
            self.config['jobschedulerproject'],
            self.redscheduler.Job.prepare_params({'project_id': 'foo'})['project_id']
        )

class TestJobResource(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)
        self.redscheduler.config = self.config
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
        self.assertIsInstance(self.redscheduler.Job, ResourceManager)

    def test_manager_returns_job_resource(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        self.assertIsInstance(job, scheduler.Job)

    def test_argument_property(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        job.description = u"-input eggs.txt\r\n-output \"spam spam.txt\"\r\n-cmd \"echo '$MONEY'\""
        self.assertEqual(['-input','eggs.txt','-output','spam spam.txt', '-cmd', "echo '$MONEY'"], job.arguments)
        self.assertRaises(
            AttributeError,
            setattr, job, 'arguments', 'foo'
        )

    def test_argument_property_replaces_attachments_with_paths(self):
        response = responses['Job']['get']
        response['issue']['attachments'] = responses['attachments']['all']
        self.response.json = json_response(response)
        job = self.redscheduler.Job.get(1)
        job.description = 'attachment:bar.txt'
        self.assertEqual('/tmp/Issue_1/bar.txt', job.arguments[0])

    def test_percent_done_property(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        job.percent_done = 100
        self.assertEqual(100, job.done_ratio)
        self.assertEqual(100, job.percent_done)

    def test_statusname_property(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        self.response.json = json_response(responses['issue_status']['all'])
        job.statusname = 'New'
        self.assertEqual(1, job.status_id)
        self.assertEqual('New', job.status.name)
        self.assertEqual(1, job.status.id)
        self.assertEqual('New', job.statusname)
        job.statusname = 'In Progress'
        self.assertEqual(2, job.status_id)
        self.assertEqual('In Progress', job.statusname)
        job.statusname = 'Completed'
        self.assertEqual(3, job.status_id)
        self.assertEqual('Completed', job.statusname)
        job.statusname = 'Error'
        self.assertEqual(4, job.status_id)
        self.assertEqual('Error', job.statusname)
        self.assertEqual(job.__dict__['_changes'], {'status_id':4})

    def test_can_only_set_status_to_invalid_name_raises_exception(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        self.response.json = json_response(responses['issue_status']['all'])
        self.assertRaises(
            scheduler.InvalidStatus,
            setattr, job, 'statusname', 'foo'
        )

    def test_replace_attachment_with_path(self):
        response = responses['Job']['get']
        response['issue']['attachments'] = responses['attachments']['all']
        self.response.json = json_response(response)
        job = self.redscheduler.Job.get(1)
        r = job._replace_attachment_with_path('foo attachment:bar.txt baz')
        self.assertEqual('foo /tmp/Issue_1/bar.txt baz', r)

    @attr('current')
    def test_command_line_property(self):
        response = responses['Job']['get']
        response['issue']['attachments'] = responses['attachments']['all']
        self.response.json = json_response(response)
        self.redscheduler.config = config = {
            'siteurl': 'http://foo.bar',
            'output_directory': '/tmp',
            'jobschedulerproject': 'foo',
            'job_defs': {'example': {'cli': u'foo -bar attachment:baz.txt', 'stdout': '{ISSUEDIR}/stdout.txt', 'stderr': '{ISSUEDIR}/stderr.txt'}}
        }
        job = self.redscheduler.Job.get(1)
        job.description = u'foo\r\n--arg1 attachment:baz.txt\r\n'
        cmd = ['foo', '-bar', '/tmp/Issue_1/baz.txt', 'foo', '--arg1', '/tmp/Issue_1/baz.txt']
        self.assertEqual(cmd, job.command_line)
        self.assertRaises(
            AttributeError,
            setattr, job, 'command_line', ''
        )

    @attr('current')
    def test_split_args_unicode(self):
        response = responses['Job']['get']
        response['issue']['attachments'] = responses['attachments']['all']
        self.response.json = json_response(response)
        job = self.redscheduler.Job.get(1)

        a = u'foo bar'
        self.assertEqual(['foo','bar'], job._split_args(a))

    @attr('current')
    def test_split_args_ascii(self):
        response = responses['Job']['get']
        response['issue']['attachments'] = responses['attachments']['all']
        self.response.json = json_response(response)
        job = self.redscheduler.Job.get(1)

        a = 'foo bar'
        self.assertEqual(['foo','bar'], job._split_args(a))

    def test_upload_cannot_be_outside_of_issuedir(self):
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        job.manager.redmine.config['job_defs']['example']['uploads'] = ['/path/foo.txt']
        self.assertRaises(
            scheduler.InvalidUploadPath,
            lambda: job.job_def
        )
        job.manager.redmine.config['job_defs']['example']['uploads'] = ['/path/foo.txt']
        self.assertRaises(
            scheduler.InvalidUploadPath,
            lambda: job.job_def
        )

    def test_job_def_property(self):
        self.response.json = json_response(responses['Job']['get'])
        self.redscheduler.config = {
            'siteurl': 'http://foo.bar',
            'output_directory': '/tmp',
            'jobschedulerproject': 'foo',
            'job_defs': {
                'example': {
                    'cli': 'foo -bar',
                    'stdout': '{ISSUEDIR}/stdout.txt',
                    'stderr': '{ISSUEDIR}/stderr.txt',
                    'uploads': [
                        '{ISSUEDIR}/stdout.txt',
                        '{ISSUEDIR}/stderr.txt'
                    ]
                }
            }
        }
        job = self.redscheduler.Job.get(1)
        self.assertEqual('foo -bar', job.job_def['cli'])
        self.assertEqual('/tmp/Issue_1/stdout.txt', job.job_def['stdout'])
        self.assertEqual('/tmp/Issue_1/stderr.txt', job.job_def['stderr'])
        self.assertEqual('/tmp/Issue_1/stdout.txt', job.job_def['uploads'][0])
        self.assertEqual('/tmp/Issue_1/stderr.txt', job.job_def['uploads'][1])

    def test_no_job_def_for_tracker(self):
        self.response.json = json_response(responses['Job']['get'])
        self.redscheduler.config = {
            'siteurl': 'http://foo.bar',
            'output_directory': '/tmp',
            'jobschedulerproject': 'foo',
            'job_defs': {}
        }
        job = self.redscheduler.Job.get(1)
        self.assertRaises(
            scheduler.MissingJobDef,
            getattr, job, 'job_def'
        )

    def test_issue_dir_property(self):
        import os.path
        self.response.json = json_response(responses['Job']['get'])
        job = self.redscheduler.Job.get(1)
        self.assertEqual(
            os.path.join(self.config['output_directory'], 'Issue_{0}'.format(job.id)),
            job.issue_dir
        )

    @mock.patch('redmine.open', mock.mock_open(), create=True)
    @mock.patch('redscheduler.scheduler.open', mock.mock_open(), create=True)
    @mock.patch('redscheduler.scheduler.os')
    @mock.patch('redscheduler.scheduler.subprocess')
    def test_run_runs_correct_popen(self, mock_subprocess, mock_os):
        mock_os.path = os.path
        response = responses['Job']['get']
        response['issue']['attachment'] = {'content_url': 'http://foo/bar.txt'}
        issue_status = responses['issue_status']['all']['issue_statuses']
        response['issue_statuses'] = issue_status
        self.response.iter_content = lambda chunk_size: (str(num) for num in range(0, 5))
        response_mock = mock.Mock()
        self.response.json = json_response(response)

        self.redscheduler.config = {
            'siteurl': 'http://foo.bar',
            'output_directory': '/tmp',
            'jobschedulerproject': 'foo',
            'job_defs': {
                'example': {
                    'cli': 'exe foo -bar attachment:bar.txt',
                    'stdout': '{ISSUEDIR}/stdout.txt',
                    'stderr': '{ISSUEDIR}/stderr.txt',
                    'uploads': [
                        '{ISSUEDIR}/stdout.txt',
                        '{ISSUEDIR}/stderr.txt'
                    ]
                }
            }
        }
        job = self.redscheduler.Job.get(1)
        mock_subprocess.Popen.return_value.wait.return_value = 0
        job.run()
        mock_os.mkdir.assert_called_once_with('/tmp/Issue_1')
        popen_call_args, popen_call_kwargs = mock_subprocess.Popen.call_args
        self.assertEqual(popen_call_args[0], job.command_line)
        self.assertEqual(popen_call_kwargs['cwd'], '/tmp/Issue_1')
        #print popen_call_kwargs['stdout']
        stdout, stderr = popen_call_kwargs['stdout']._mock_new_parent.call_args_list
        stdout.assert_called_once_with('/tmp/Issue_1/stdout.txt')
        stderr.assert_called_once_with('/tmp/Issue_1/stderr.txt')
        self.assertEqual('Completed', job.statusname)
        self.assertEqual(job.uploads[0]['path'], '/tmp/Issue_1/stdout.txt')
        self.assertEqual(job.uploads[1]['path'], '/tmp/Issue_1/stderr.txt')

    @mock.patch('redmine.open', mock.mock_open(), create=True)
    @mock.patch('redscheduler.scheduler.open', mock.mock_open(), create=True)
    @mock.patch('redscheduler.scheduler.os')
    @mock.patch('redscheduler.scheduler.subprocess')
    def test_run_job_writes_stdout_stderr_not_specified(self, mock_subprocess, mock_os):
        mock_os.path = os.path
        response = responses['Job']['get']
        response['issue']['attachment'] = {'content_url': 'http://foo/bar.txt'}
        issue_status = responses['issue_status']['all']['issue_statuses']
        response['issue_statuses'] = issue_status
        self.response.iter_content = lambda chunk_size: (str(num) for num in range(0, 5))
        response_mock = mock.Mock()
        self.response.json = json_response(response)
        self.redscheduler.config = {
            'siteurl': 'http://foo.bar',
            'output_directory': '/tmp',
            'jobschedulerproject': 'foo',
            'job_defs': {
                'example': {
                    'cli': 'exe foo -bar'
                }
            }
        }
        job = self.redscheduler.Job.get(1)
        job.run()
        popen_call_args, popen_call_kwargs = mock_subprocess.Popen.call_args
        stdout, stderr = popen_call_kwargs['stdout']._mock_new_parent.call_args_list
        stdout.assert_called_once_with('/tmp/Issue_1/stdout.txt')
        stderr.assert_called_once_with('/tmp/Issue_1/stderr.txt')

    @mock.patch('redmine.open', mock.mock_open(), create=True)
    @mock.patch('redscheduler.scheduler.open', mock.mock_open(), create=True)
    @mock.patch('redscheduler.scheduler.os')
    @mock.patch('redscheduler.scheduler.subprocess')
    def test_run_job_fails_sets_error_status(self, mock_subprocess, mock_os):
        mock_os.path = os.path
        response = responses['Job']['get']
        response['issue']['attachment'] = {'content_url': 'http://foo/bar.txt'}
        response['upload'] = {'token': '123456'}
        issue_status = responses['issue_status']['all']['issue_statuses']
        response['issue_statuses'] = issue_status
        self.response.iter_content = lambda chunk_size: (str(num) for num in range(0, 5))
        response_mock = mock.Mock()
        self.response.json = json_response(response)
        self.redscheduler.config = {
            'siteurl': 'http://foo.bar',
            'output_directory': '/tmp',
            'jobschedulerproject': 'foo',
            'job_defs': {
                'example': {
                    'cli': 'exe foo -bar',
                    'uploads': [
                        '{ISSUEDIR}/foo.txt'
                    ]
                }
            }
        }
        job = self.redscheduler.Job.get(1)
        mock_subprocess.Popen.return_value.wait.return_value = 1
        job.run()
        self.assertEqual('Error', job.statusname)
        self.assertRaises(AttributeError, lambda: job.uploads)
