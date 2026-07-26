# ADR 0004: Zero required approvals for the initial solo repository

Status: accepted for alpha; review at second maintainer

Main requires pull requests, stable checks, conversation resolution, linear history, and prohibits
force pushes and deletion. It initially requires zero GitHub approvals because a one-maintainer
repository would otherwise deadlock. Substantive releases still require the five domain-review
artifacts. Raise the repository approval count to one when a second active maintainer joins.
