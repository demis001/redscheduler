from . import (
    unittest, mock, json_response,
    CONFIG_EXAMPLE, builtins, RequestBase,
    responses
)

import os.path
from nose.plugins.attrib import attr

from redmine.managers import ResourceManager

from redscheduler import scheduler, config

class TestRedScheduler(unittest.TestCase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)

    def test_initializes_correctly(self):
        self.assertEqual(self.redscheduler.url, self.config['siteurl'])
        self.assertEqual(self.redscheduler.key, self.config['apikey'])
        self.assertEqual(self.redscheduler.custom_resource_paths, ('redscheduler.scheduler',))

    def test_contains_config(self):
        self.assertEqual(self.redscheduler.config, self.config)

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

class JobResourceBase(RequestBase):
    def setUp(self):
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.redscheduler = scheduler.RedScheduler(self.config)
        self.redscheduler.config = self.config
        super(JobResourceBase,self).setUp()

class TestJobResource(JobResourceBase):
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

    def test_split_args_unicode(self):
        response = responses['Job']['get']
        response['issue']['attachments'] = responses['attachments']['all']
        self.response.json = json_response(response)
        job = self.redscheduler.Job.get(1)

        a = u'foo bar'
        self.assertEqual(['foo','bar'], job._split_args(a))

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


class TestRunningJob(JobResourceBase):
    def setUp(self):
        super(TestRunningJob,self).setUp()
        self.patch_redmineopen = mock.patch(
            'redmine.open', mock.mock_open(), create=True
        )
        self.patch_scheduleropen = mock.patch(
            'redscheduler.scheduler.open', mock.mock_open(), create=True
        )
        self.patch_scheduleros = mock.patch('redscheduler.scheduler.os')
        self.patch_schedulersubprocess = mock.patch(
            'redscheduler.scheduler.subprocess'
        )
        self.patch_redmineopen.start()
        self.patch_scheduleropen.start()
        self.mock_os = self.patch_scheduleros.start()
        self.mock_subprocess = self.patch_schedulersubprocess.start()
        self.mock_os.path = os.path
        self.addCleanup(self.patch_redmineopen.stop)
        self.addCleanup(self.patch_scheduleropen.stop)
        self.addCleanup(self.patch_scheduleros.stop)
        self.addCleanup(self.patch_schedulersubprocess.stop)
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
        self.mock_os.path.exists = mock.Mock(side_effect = [True,True])

    def test_run_runs_correct_popen(self):
        job = self.redscheduler.Job.get(1)
        self.mock_subprocess.Popen.return_value.wait.return_value = 0
        job.run()
        self.mock_os.mkdir.assert_called_once_with('/tmp/Issue_1')
        popen_call_args, popen_call_kwargs = self.mock_subprocess.Popen.call_args
        self.assertEqual(popen_call_args[0], job.command_line)
        self.assertEqual(popen_call_kwargs['cwd'], '/tmp/Issue_1')
        #print popen_call_kwargs['stdout']
        stdout, stderr = popen_call_kwargs['stdout']._mock_new_parent.call_args_list
        stdout.assert_called_once_with('/tmp/Issue_1/stdout.txt')
        stderr.assert_called_once_with('/tmp/Issue_1/stderr.txt')
        self.assertEqual('Completed', job.statusname)
        self.assertEqual(job.uploads[0]['path'], '/tmp/Issue_1/stdout.txt')
        self.assertEqual(job.uploads[1]['path'], '/tmp/Issue_1/stderr.txt')

    def test_run_job_writes_stdout_stderr_not_specified(self):
        del self.redscheduler.config['job_defs']['example']['stdout']
        del self.redscheduler.config['job_defs']['example']['stderr']
        job = self.redscheduler.Job.get(1)
        job.run()
        popen_call_args, popen_call_kwargs = self.mock_subprocess.Popen.call_args
        stdout, stderr = popen_call_kwargs['stdout']._mock_new_parent.call_args_list
        stdout.assert_called_once_with('/tmp/Issue_1/stdout.txt')
        stderr.assert_called_once_with('/tmp/Issue_1/stderr.txt')

    def test_run_popen_non_retcode_1_sets_error_status(self):
        job = self.redscheduler.Job.get(1)
        self.mock_subprocess.Popen.return_value.wait.return_value = 1
        r = job.run()
        self.assertEqual('Error', job.statusname)
        self.assertRaises(AttributeError, lambda: job.uploads)

    def test_run_popen_exception_sets_error_status(self):
        job = self.redscheduler.Job.get(1)
        self.mock_subprocess.Popen.side_effect = Exception("foo")
        r = job.run()
        self.assertEqual(job.notes, 'Error: foo')
        self.assertEqual(job.statusname, 'Error')
        self.assertEqual(-1, r)

    def test_cli_executable_non_executable_makes_correct_note(self):
        job = self.redscheduler.Job.get(1)
        e = OSError('[Errno 13] Permission denied')
        e.errno = 13
        self.mock_subprocess.Popen.side_effect = e
        r = job.run()
        self.assertEqual(
            job.notes,
            'Error: cli executable in redsample config is not executable'
        )
        self.assertEqual(job.statusname, 'Error')
        self.assertEqual(-1, r)

    def test_cli_executable_missing_makes_correct_note(self):
        job = self.redscheduler.Job.get(1)
        e = OSError('[Errno 2] No such file or directory')
        e.errno = 2
        self.mock_subprocess.Popen.side_effect = e
        r = job.run()
        self.assertEqual(
            job.notes, 'Error: cli executable in redsample config cannot be found'
        )
        self.assertEqual(job.statusname, 'Error')
        self.assertEqual(-1, r)

    def test_oserror_non_13_or_2(self):
        job = self.redscheduler.Job.get(1)
        e = OSError('[Errno 1] Some error')
        e.errno = 1
        self.mock_subprocess.Popen.side_effect = e
        r = job.run()
        self.assertEqual(
            job.notes, 'Error: [Errno 1] Some error'
        )
        self.assertEqual(job.statusname, 'Error')
        self.assertEqual(-1, r)

    def test_upload_file_missing(self):
        self.redscheduler.config['job_defs']['example']['uploads'].append(
            '{ISSUEDIR}/missing.txt'
        )
        self.redscheduler.config['job_defs']['example']['uploads'].append(
            '{ISSUEDIR}/missing2.txt'
        )
        job = self.redscheduler.Job.get(1)
        self.mock_os.path.exists.side_effect = [True, True, False, False]
        self.mock_subprocess.Popen.return_value.wait.return_value = 0
        r = job.run()
        self.assertEqual(
            job.notes,
            'Output will be located in /tmp/Issue_1\r\n'
            'Warning: /tmp/Issue_1/missing.txt does not exist\r\n' \
            'Warning: /tmp/Issue_1/missing2.txt does not exist\r\n'
        )
        self.assertEqual(2, len(job.uploads))
        self.assertEqual(job.statusname, 'Error')
        self.assertEqual(-1, r)
