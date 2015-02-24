=============
Configuration
=============

Configuration is split into two parts

* Redmine setup
* Local config file

Redmine Setup
=============

The redmine setup is quite simple.
You just need to have a project created that you will put issues in that will run your jobs.

Then you need to create a tracker wit the same name as the job_defs you define.

Example
-------

If you have a job_def like the following::

    job_defs:
        example_job:
            cli: "echo"

Then you need a tracker named ``example_job``

Local Config File
=================

You will need to ensure that you have setup your config file which needs 
to be located under your home directory as .redscheduler.config

If you are already familiar with the yaml format, then you will notice that the config file utilized
yaml. If you are not familiar with yaml format, then you may want to go read about that 
`here <http://www.yaml.org/start.html>`_

There is an example config file you can copy as your template in the repository called 
redscheduler.config.example that contains comments about what each configuration item
means.

Options
-------

siteurl
^^^^^^^

This simply defines the url to your Redmine instance

apikey
^^^^^^

You can get this from the My Account page in Redmine

jobschedulerproject
^^^^^^^^^^^^^^^^^^^

This is the project identifier(*not project name*) that jobs will be pulled
from

output_directory
^^^^^^^^^^^^^^^^

When each job is run, it creates an Issue_#### directory inside this path and then
is run within that issue directory.

The issue directory can be referenced inside any job_def via::

    {ISSUEDIR}

job_defs
--------

Here we will focus more on the job_defs section as that is the most complex.

The job_defs section simply lists all the jobs that you want to be able to run.
Each job_def name needs to coorespond to a tracker name in Redmine.

This is how issues are mapped to what job_def to run.

Each job_def has to define at least, cli, but here is a list of all available configurable options
at this point.

cli
^^^

This is the command line that will be run for the job. This should include the command that you
want to execute when the job runs.

Only include the arguments that are static for this command and don't change
between each time the command is run.

A good example is, if your command has an argument that defines the output directory of where any
output files should be sent should usually be set in the cli as you can then force the output to
always go into the output_directory option

You cannot have more than one command in the cli field. That is, you cannot use shell operators
such as ``|``, ``&&``, ``>``, ``;`` to create complex pipelines.

If you need to create a more complex pipeline, then you will need to create a shell script that 
runs that pipeline and then specify that shell script in the cli

**Note**: Environmental variables are not replaced such as ``$HOME`` and ``~/`` so you will have
to specify the absolute path to your executables and other files

.. _cliexample:

Example:

    You want to run a shell pipeline as follows::

        cat /proc/cpus | grep

    The goal is to be able to have your Redmine tracker issue specify what you want to grep out
    of /proc/cpus

    Since you cannot have the ``|`` in the cli, you will need a shell script to do that for you

    .. code-block:: bash

        cat <<EOF > ~/catgrepcpus.sh
        #!/usr/bin/env bash
        cat /proc/cpus | grep $1
        EOF
        
        chmod 755 ~/catgrepcpus.sh

    Then configure the job_def as follows::

        job_defs:
            pipeline_example:
                cli: /home/username/catgrepcpus.sh

    Now in the description of your redmine issue you would put the following to have it
    grep out the term ``Physical``::

        Physical

    Pretty simple!

stdout
^^^^^^

This is an optional option that specifies the location of the file where to place any
output that gets generated on STDOUT from running the cli directive

Ommitting this option will use the default of {ISSUEDIR}/stdout.txt

stderr
^^^^^^

This is an optional option that specifies the location of the file where to place any
output that gets generated on STDERR from running the cli directive

Ommitting this option will use the default of {ISSUEDIR}/stderr.txt
