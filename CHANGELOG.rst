Changelog
---------

0.0.3-dev
+++++++++

- Added runissue command and documentation

0.0.2-dev
+++++++++

- No longer requires a jobschedulerproject to be defined as that was to restricting
  and didn't make sense in the long run
- Reports errors as notes more specifically now for missing executables and 
  permissions issues and other exceptions
- Now checks that upload files exist and reports notes if they do not instead of
  raising top level exception. Sets status as Error in this case.

0.0.1-dev
+++++++++

- Added uploads to job_defs for files that should be uploaded back to the issue
  after it is completed
- Restructured tests to conform to python_template better
