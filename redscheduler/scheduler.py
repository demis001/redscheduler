import shlex
import os.path
import subprocess
import re
import os

from redmine import Redmine
from redmine.resources import Issue
from redmine.managers import ResourceManager

class InvalidStatus(Exception):
    '''
    Raised for invalid status specified
    '''
    pass

class MissingJobDef(Exception):
    '''
    Raised when there is no job_def in config for
    the Job's tracker
    '''
    pass

class RedScheduler(Redmine):
    def __init__(self, config):
        self.config = config
        super(RedScheduler, self).__init__(url=config['siteurl'], key=config['apikey'])
        self.custom_resource_paths = (__name__,)

    def __getattr__(self, resource):
        if resource == 'Job':
            resource = JobManager(self, 'Jobs')
            resource.resource_class.project_id = self.config['jobschedulerproject']
        else:
            resource = super(RedScheduler, self).__getattr__(resource)
        return resource

class JobManager(ResourceManager):
    def __init__(self, redmine, resource_name):
        self.redmine = redmine
        self.resource_class = Job
        
class Job(Issue):
    _members = Issue._members + (
        'arguments','percent_done', 'statusname',
        'command_line', 'job_def', 'issue_dir'
    )

    @classmethod
    def translate_params(cls, params):
        # Inject specific project_id and tracker_id for Job based on config
        params['project_id'] = cls.project_id
        return super(Job, cls).translate_params(params)

    @property
    def arguments(self):
        '''
        Pulls arguments out of the .description of the job
        Each line is an argument for the job

        :return: single list of all arguments
        '''
        args = []
        for line in self.description.splitlines():
            args += shlex.split(line.encode('utf-8'))
        return args

    @property
    def percent_done(self):
        '''
        Returns the current done_ratio
        '''
        return self.done_ratio

    @percent_done.setter
    def percent_done(self, percentage):
        '''
        Sets the done_ratio of a job

        :param int percentage: 0 - 100
        '''
        self.done_ratio = int(percentage)

    @property
    def statusname(self):
        '''
        Return the status name
        '''
        return self.status#.name

    @statusname.setter
    def statusname(self, statusname):
        '''
        Set the status_id of the job
        Finds the correct status_id based on the status name given
        and then uses that to set the status
        
        - New
        - In Progress
        - Completed
        - Error

        :param str statusname: Status name to set
        '''
        valid_statuses = (
            'New',
            'In Progress',
            'Completed',
            'Error'
        )
        # First locate the status resource by name
        all_status = self.manager.redmine.issue_status.all()
        _status = None
        for status in all_status:
            if status.name == statusname:
                _status = status
                break
        # Ensure it is a valid status
        if _status is None or statusname not in valid_statuses:
            raise InvalidStatus("{0} is an invalid status".format(statusname))
        # set the status_id of this resource
        self.status_id = _status.id

    @property
    def command_line(self):
        '''
        Mesh together the config's cli and the arguments supplied by the user in the
        job description(arguments attribute)

        :return: list of arguments suitable for Popen
        '''
        jobdef = self.job_def
        cli_str = self._replace_attachment_with_path(jobdef['cli'], self.attachments)
        cli = shlex.split(cli_str)
        return cli + self.arguments

    def _replace_attachment_with_path(self, text):
        '''
        Replace all attachment:... with job_def output_directory + issue_dir paths

        :param str text: any string of text that might contain one or more attachment:... 
        :param list attachments: iterable of attachment resources
        '''
        print 'Retrieving attachments'
        print
        attachments = self.attachments
        print 'Retrieved attachments'
        print
        for attach in attachments:
            p = 'attachment:{0}'.format(attach.filename)
            text = re.sub(p, os.path.join(self.issue_dir,attach.filename), text)
        return text

    @property
    def job_def(self):
        '''
        Return the job_def from the config for this job

        :return: dictionary from job_def for tracker this job is for
        '''
        jobdef = None
        config = self.manager.redmine.config
        try:
            jobdef = config['job_defs'][self.tracker.name]
        except KeyError as e:
            raise MissingJobDef('config is missing job defenition {0}'.format(e))

        # Replace ISSUEDIR in all values with issue id
        # Define all replacements
        replaces = {
            'ISSUEDIR': self.issue_dir
        }
        _jobdef = {}
        for k,v in jobdef.iteritems():
            _jobdef[k] = v.format(**replaces)
        return _jobdef

    @property
    def issue_dir(self):
        return os.path.join(
            self.manager.redmine.config['output_directory'],
            'Issue_{0}'.format(self.id)
        )

    def _replace_command_line_attachments(self, command_line):
        '''
        '''

    def run(self):
        '''
        Spawn a new process using this job's specs

        set status to In Progress
        save issue
        Create issue_dir directory
        chdir issue_dir
        download all attachment:.* items in command_line to issue_dir
        replace command_line with paths to downloaded items
        run command_line with stdout and stderr set approprietly
        wait for complete
        set status to Completed or Error based on return code
        set notes to issue_dir path
        save issue
        TODO: upload all paths defined in job_def['uploads']
        return returncode from popen
        '''
        # Set status to in progress
        self.statusname = 'In Progress'
        self.notes = 'Output will be located in {0}'.format(self.issue_dir)
        self.save()
    
        # Create issue dir
        os.mkdir(self.issue_dir)

        # The command line that will be run
        # Needs attachment:(.*) replaced
        cli = self.command_line

        # Download attachments into issue dir
        # and replace all attachment:... in command_line with download path
        for attach in self.attachments:
            # Download into issue_dir
            filepath = attach.download(savepath=self.issue_dir)
            # Pattern to replace
            p = 'attachment:{0}'.format(attach.filename)
            # Loop through all command line options and replace any attachment:....
            for i in range(len(cli)):
                cli[i] = re.sub(p, filepath, cli[i])

        # Run the command with correct stdout/stderr and cwd
        jobdef = self.job_def
        stdout_path = jobdef.get('stdout', os.path.join(self.issue_dir,'stdout.txt'))
        stderr_path = jobdef.get('stderr', os.path.join(self.issue_dir,'stderr.txt'))
        stdout_fh = open(stdout_path, 'w')
        stderr_fh = open(stderr_path, 'w')
        try:
            p = subprocess.Popen(cli, stdout=stdout_fh, stderr=stderr_fh, cwd=self.issue_dir)
            # Wait for job to complete or error
            retcode = p.wait()
        except:
            retcode = -1

        if retcode != 0:
            self.statusname = 'Completed'
        else:
            self.statusname = 'Error'

        # Save issue with new status
        self.save()

        return retcode
