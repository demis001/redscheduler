from . import (
    unittest, mock, json_response,
    CONFIG_EXAMPLE, builtins, RequestBase,
    responses
)

import os
from os.path import *
import sys
import shutil

import tempdir
import yaml

from redscheduler import runissue, config

class RunIssueBase(RequestBase):
    def setUp(self):
        super(RunIssueBase,self).setUp()
        self.args = ['runissue', '1']
        self.patch_sys = mock.patch('argparse._sys')
        self.mock_sys = self.patch_sys.start()
        self.mock_sys.argv = self.args
        self.addCleanup(self.mock_sys.stop)

class TestRunIssueMain(RunIssueBase):
    def setUp(self):
        super(TestRunIssueMain,self).setUp()
        self.config = config.load_config(CONFIG_EXAMPLE)
        self.tdir = tempdir.TempDir()
        self.config['output_directory'] = self.tdir.name
        self.config_file = join(self.tdir.name, 'config.yaml')
        with open(self.config_file, 'w') as fh:
            yaml.dump(self.config, fh, default_flow_style=False)
        self.args += ['-c', self.config_file]

    def test_warns_user_issue_directory_already_exists(self):
        issue_dir = join(self.tdir.name, 'Issue_1')
        runissue.main()
        with mock.patch('redscheduler.runissue.sys.stderr') as mock_stderr:
            r = runissue.main()
            self.assertEqual(
                ('Refusing to overwrite existing directory ' + issue_dir + '\n',),
                mock_stderr.write.call_args[0]
            )
        self.assertEqual(17, r)

    def test_reruns_issue_issue_dir_exists(self):
        issue_dir = join(self.tdir.name, 'Issue_1')
        runissue.main()
        self.args += ['--rerun']
        with mock.patch('redscheduler.runissue.sys.stdout') as mock_stdout:
            runissue.main()
            self.assertEqual(
                ('Overwriting existing directory ' + issue_dir + '\n',),
                mock_stdout.write.call_args_list[0][0]
            )
        issue_dir = join(self.tdir.name, 'Issue_1')
        self._check_issue_dir(issue_dir)

    def test_runs_issue(self):
        runissue.main()
        issue_dir = join(self.tdir.name, 'Issue_1')
        self._check_issue_dir(issue_dir)

    def _check_issue_dir(self, issue_dir):
        self.assertTrue(
            exists(issue_dir),
            'Did not create issue dir'
        )
        self.assertTrue(
            exists(join(issue_dir, 'output.stdout')),
            'Did not create output.stdout in issue dir'
        )

    def test_job_run_raises_exception(self):
        with mock.patch('redscheduler.runissue.scheduler') as mock_scheduler:
            job = mock.Mock()
            mock_scheduler.RedScheduler.return_value.Job.get.return_value = job
            job.issue_dir = join(self.tdir.name, 'Issue_1')
            class RedmineException(Exception): pass
            job.run.side_effect = RedmineException('Redmine Test failure')
            self.assertRaises(RedmineException, runissue.main)
            self.assertIn(job.notes, 'Redmine Test failure')
            self.assertEqual('Error', job.statusname)
            job.save.assert_called_once_with()
