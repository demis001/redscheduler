from redmine import Redmine
from redmine.resources import Issue
from redmine.managers import ResourceManager

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
    _members = Issue._members + ('arguments', 'percent_done', 'status')

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
        '''
        return self.description.replace('\r','').split('\n')

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

    def _status_for_status_attr(self, attr, value):
        '''
        Return the status object for a given status id

        :param str attr: status attribute to use to lookup
        :param str value: value to match for attribute
        '''
        all_statuses = self.manager.redmine.issue_status.all()
        for status in all_statuses:
            if status.id == self.status_id:
                return status
        raise ValueError('No status for status id {0}'.format(statusid))

    @property
    def status(self):
        '''
        Read the .status_id and return the name for the current
        status
        '''


    @status.setter
    def status(self, status):
        '''
        Set the status_id of the job
        Finds the correct status_id based on the status name given
        and then uses that to set the status
        
        - New
        - In Progress
        - Completed
        - Error

        :param str status: Status name to set
        '''
