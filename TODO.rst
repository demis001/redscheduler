====
TODO
====

* Build scraper that can scrape specific trackers/job_defs and run them
  This runs the first job(for reference)

  .. code-block:: python

    from redscheduler import config, scheduler
    c = config.load_user_config()
    jobs = scheduler.RedScheduler(c).Job.all()
    jobs = list(jobs)
    print jobs[0].run()
