# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: crawl or search webpages and documents using crawl4ai
# Status: PROTOTYPING
# FileID: Un-ws-0005

# NOTE: for testing only
import asyncio
from crawl4ai import *
from database import database as db


def get_unis():
    """
    Fetch all universities from the database

    Returns:
        list[dict[str, Any]]: List of universities with information
    """
    
    # connect to db
    cursor = db.connect()

    db.select(cursor=cursor, )


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        print(result.markdown)

if __name__ == "__main__":
    # asyncio.run(main())
