"""Allow ``python -m facts_svc`` after installation."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
