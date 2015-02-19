from redmine import Redmine
from redmine.resources import Issue
from redmine.managers import ResourceManager

class RedScheduler(Redmine):
    def __init__(self, config):
        self.config = config
        super(RedScheduler, self).__init__(url=config['siteurl'], key=config['apikey'])
        self.custom_resource_paths = (__name__,)

    def __getattr__(self, resource):
        if resource == 'Jobs':
            resource = JobsManager(self, 'Jobs')
            resource.resource_class.project_id = self.config['jobschedulerproject']
        else:
            resource = super(RedScheduler, self).__getattr__(resource)
        return resource

class JobsManager(ResourceManager):
    def __init__(self, redmine, resource_name):
        self.redmine = redmine
        self.resource_class = Jobs
        
class Jobs(Issue):
    @classmethod
    def translate_params(cls, params):
        # Inject specific project_id and tracker_id for Jobs based on config
        params['project_id'] = cls.project_id
        return super(Jobs, cls).translate_params(params)
