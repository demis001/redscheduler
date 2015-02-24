====
Jobs
====

Think of each issue in Redmine as a Job instance that will be run.
So if you make 100 issues in redmine, then 100 jobs will be run on the computer

So what you want to define in each issue in Redmine are the arguments that would change between each
job being run.

Often, this is the input file[s] to the job that will be run

First off, assume we are using the example config that comes shipped with the code and that
output_directory is set to /tmp

Let's say you want a job defined that will convert comma separated files to tab separated files.
We know that in the shell you can simply use the ``tr`` command to do this by substituting 
the tab ``\t`` character any time it sees a comma ``,``::

    tr ',' '\t' < /path/to/input.csv

Ok, so here we have a simple command line that we want to run so lets pick out how we will 
create our job_def and also later we will show how each Job issue will be created to run it

First, what will remain the same every time we run the command?::

    tr ',' '\t' <

We know from reading :ref:`CLI Example <cliexample>` that you cannot directly put this
into the job_def's cli field so we will need to make a shell script to run it for us.

.. code-block:: bash

    cat <<EOF >$HOME/bin/replace-comma-with-tab.sh
    #!/usr/bin/env bash
    tr ',' '\t' < $1 > $2
    EOF
    chmod 755 $HOME/bin/replace-comma-with-tab.sh

Now, we can define our job in our ~/.redscheduler.config::

    job_def:
        ...
        replace-comma-with-tab:
            cli: "/home/username/bin/replace-comma-with-tab.sh"

Make sure to create the tracker called ``replace-comma-with-tab`` and make sure it has a
workflow that includes the statuses:

* New
* In Progress
* Error
* Completed

Now you can create jobs to run this task easily. You can even upload your files you want converted
to the issue and reference them in the issue description.


Here would be an example description::

    attachment:my.csv
    my.tsv

Assuming, you have uploaded the attachment named my.csv to the issue when you created it.

Now, when the job runs, you can expect the following to happen

#. ``/tmp/Issue_1`` is created for you

#. ``/tmp/Issue_1/stdout.txt`` and ``/tmp/Issue_1/stderr.txt`` are created with output from running
   your command

   | In this case, stdout.txt should be empty as you are redirecting output into ``my.tsv``
   | If your command generates errors, you will get output in ``stderr.txt``

#. ``/tmp/Issue_1/my.tsv`` is created with the output from your command.

#. Additionally, your command is run within the ``/tmp/Issue_1`` directory.

    If any relative paths are used for files, they will be relative to that directory
