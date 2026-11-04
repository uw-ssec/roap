# Security Policy

## Supported Versions

Only the latest release of ROAP receives security fixes. Please upgrade to the
latest release before reporting an issue.

## Reporting a Vulnerability

Report security concerns through the repository's
[GitHub Discussions](https://github.com/uw-ssec/roap/discussions).

Discussions are public. If you think you have found a vulnerability, **do not
post its details there.** Open a Discussion that says you have a security issue
to report and ask a maintainer to contact you privately. Share the details only
through that private channel.

When you share the details, include as much of the following as you can:

- A description of the issue and its potential impact
- The affected ROAP version
- Steps to reproduce, or a minimal example
- Your operating system and Python version

## What Counts as a Security Issue

ROAP processes scientific data, so in addition to the usual concerns (arbitrary
code execution, unsafe file or path handling, compromised dependencies), we
treat bugs that **silently produce incorrect scientific results** as security
relevant.

Crashes that don't expose data or allow code execution, and issues in
third-party dependencies, should be reported as ordinary
[issues](https://github.com/uw-ssec/roap/issues) or to the dependency's
maintainers.

## Questions

For security questions that aren't vulnerability reports, open a
[GitHub Discussion](https://github.com/uw-ssec/roap/discussions).
