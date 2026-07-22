from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sucrawler.cli.crawl_user import crawl_user_main


if __name__ == "__main__":
    asyncio.run(crawl_user_main())
