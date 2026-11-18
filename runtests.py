#!/usr/bin/env python
"""Run the test-suite with Django's test runner: ``python runtests.py``."""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    django.setup()
    runner = get_runner(settings)(verbosity=2)
    failures = runner.run_tests(sys.argv[1:] or ["tests"])
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
