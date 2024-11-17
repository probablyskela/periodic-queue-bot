We welcome any Issues and Pull Requests.
If you want to contribute, please make sure you enable pre-commit hooks.
```
pre-commit install
```

Also that would be nice if you test your code. You can run tests using following command
```
make test
```

If you want to add a feature create a new branch and then create a pull request to dev branch.
Basic rules for branch names:
1. Lowercase and hyphen-separated.
2. Only use alphanumeric characters (a-z, 0-9).
3. Be as descriptive as possible
4. Use prefixes:
    1. Feature branches: `feat/<branch-name>`
    2. Bugfix branches: `bug/<branch-name>`
    3. Hotfix branches: `hot/<branch-name>`
    4. Release branches: `rel/<branch-name>`
    5. Refactor branches: `ref/<branch-name>`
    6. Documentation branches: `docs/<branch-name>`
    7. General branches: `gen/<branch-name>`

Current tasks:
* Consider using APScheduler instead of Celery.
* Allow modifying event parameters without overwriting other settings.
* Allow exporting chat config (it's already being saved in database so should be easy).
* Add caching to service layer.
* Refactor service layer.
* Refactor handlers layer.
* General refactoring.
* Rename app folder to bot.
* Fix skipping logic.
* Allow creating notification channel to notify next person in the queue for an event.
