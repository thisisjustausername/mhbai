# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: automated scraping of mhbs from University of Augsburg
# Status: VERSION 1.0
# FileID: Au-sc-0003


from university_of_augsburg.web_scraping.download_files import fetch_valid_urls, download_async, download_pdfs

# initialize variables
new_pdfs_only = False # whether to download only new pdfs or also old pdfs

# fetch urls
print("Fetching valid mhb urls...")
data = fetch_valid_urls()
data = list(set(data))

# download pdfs
print("Downloading mhb pdfs...")

download_async(data, new_only=new_pdfs_only, adapt_file_names=True)

#download_async(data, new_only=new_pdfs_only, adapt_file_names=True)