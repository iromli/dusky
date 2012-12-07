Usage
=====

1.  Make sure `dusky` and `sqlalchemy` is available in your `PYTHONPATH`.
2.  Copy `config.py` to `local_config.py` and override `DB_*` names to suit your
    MySQL settings.
3.  Run the `python app.py`.
4.  Open new console window, use `siege` or `ab` tool to start load testing:

        ab -c 100 -n 10000 localhost:8888/

    Open new console window (again):

        ab -c 100 -n 10000 localhost:8888/posts

    You'll see that those two URLs running in concurrent without blocking each
    other.
