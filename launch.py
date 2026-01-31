import os
import asyncio


if __name__ == '__main__':
    if os.path.exists("app.lock"):
        exit(1)

    import main
    asyncio.run(main.main())
