# Coding on topo-imagery

The `topo-imagery` repository is made of a Docker container containing Python scripts where the main goal is to run those scripts on the cloud (AWS) using a workflow/ETL system (Argo Workflows).

## Software stack

[Python](https://www.python.org/) - Application code
[GitHub](https://github.com/) - Source code distribution and integration pipeline
[Docker](https://www.docker.com/) - Container to run the code

## Developement conventions

### Git

#### Pull Requests (PR)

Any new code should first go on a branch.
When the code is ready, submit a pull request for a branch, wait for two reviews and passing pipeline before merging.

The PR should be linked to the associated JIRA ticket when there is one. To do this, either the branch name or/and the PR title must mention the JIRA ticket id in it. Example:
branch: `feat/tde-123-my-feature`
PR title: `feat: new feature (TDE-123)`

Every PR should have a description about why and what is changed. Provide information for testing if there are some tricky parts.

> **_NOTE:_** It is better to make several small PR than a large one when a feature can be split in several independant parts. This have multiple advantages: make the review easier, understand how something broke, etc.

#### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) style commit messages.
Make sure the unit tests pass and run the `pre-commit` script before commiting the code. It will check and fix the formatting, check that typing is repected, etc.

> **_NOTE:_** It is a good habbit to have to commit the code frequently.

#### Releases

## Python dependencies

## Docker local environment

## Python scripts implementation

### Input/Output
