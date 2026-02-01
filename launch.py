import os
import asyncio
import sys


if __name__ == '__main__':
    if os.path.exists("app.lock"):
        exit(1)

    import main

    try:
        asyncio.run(main.main())
    except Exception as e:
        print(f"An critical error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
