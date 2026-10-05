# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: crawl a web page and return all the urls it contains
# STATUS: IN DEVELOPMENT
# FileID: Sc-cr-0002


"""
Multiprocess BFS crawler that keeps the multiprocessing architecture but uses
async I/O (aiohttp) inside each worker process for fast network fetches.
"""
from __future__ import annotations
import tldextract
import argparse
import asyncio
import os
from multiprocessing import get_context
from multiprocessing.queues import Queue as MPQueue
from typing import Iterable, List, Optional, Set, Dict
from urllib.parse import urljoin, urldefrag, urlparse

# Network + parsing
import aiohttp
from aiohttp import ClientTimeout

from selectolax.parser import HTMLParser as FastHTMLParser


# --------------------- URL helpers ---------------------
def normalize_href(base: str, href: Optional[str], host: str) -> Optional[str]:
    if not href:
        return None
    href = href.strip()
    if not href or href.startswith("#"):
        return None
    low = href.lower()
    if low.startswith(("javascript:", "mailto:", "tel:", "data:")):
        return None
    href, _ = urldefrag(href)
    try:
        full = urljoin(base, href)
    except Exception:
        return None
    parsed = urlparse(full)
    if parsed.scheme not in ("http", "https"):
        return None
    if host not in full:
        return None
    return full

def extract_links_selectolax(base: str, content: bytes, host: str) -> Set[str]:
    out: Set[str] = set()
    try:
        tree = FastHTMLParser(content)
        for n in tree.css("a"):
            href = n.attributes.get("href")
            v = normalize_href(base, href, host)
            if v:
                out.add(v)
    except Exception:
        return set()
    return out

# --------------------- Worker (async) ---------------------
async def _parse_links(base: str, content: bytes, host: str) -> Set[str]:
    return extract_links_selectolax(base, content, host)

async def _fetch_one(
    session: aiohttp.ClientSession,
    url: str,
    global_sem: asyncio.Semaphore,
    host_sem: asyncio.Semaphore,
    timeout: int,
    host: str
) -> Set[str]:
    
    async with global_sem, host_sem:
        try:
            async with session.get(url, timeout=ClientTimeout(total=timeout)) as resp:
                if resp.status >= 400:
                    return set()
                data = await resp.read()
                return await _parse_links(url, data, host)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return set()
        except Exception:
            return set()

async def worker_async_loop(
    task_queue: MPQueue,
    result_queue: MPQueue,
    host: str, 
    *,
    concurrency: int = 50,
    per_host_limit: int = 10,
    timeout: int = 10,
):
    """
    Async loop that repeatedly takes a batch (list[str]) from the blocking multiprocessing
    task_queue (via run_in_executor) and processes it using asyncio + aiohttp.
    Puts a dict {"worker_pid": pid, "urls": set(...)} on result_queue for each batch.
    """
    url_host = host
    host = None
    loop = asyncio.get_running_loop()
    connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=per_host_limit, ttl_dns_cache=300)
    headers = {"User-Agent": f"mp-async-worker/{os.getpid()}"}

    global_sem = asyncio.Semaphore(concurrency)
    host_semaphores: Dict[str, asyncio.Semaphore] = {}

    # reuse one session per worker for connection pooling
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        while True:
            # Blocking get from multiprocessing.Queue - run in executor to avoid blocking the loop
            batch = await loop.run_in_executor(None, task_queue.get)
            if batch is None:
                # sentinel -> exit
                break
            # If batch is empty list, return empty result quickly
            if not batch:
                result_queue.put({"worker_pid": os.getpid(), "urls": set()})
                continue

            tasks = []
            for url in batch:
                if not url:
                    continue
                host = urlparse(url).netloc
                host_sem = host_semaphores.setdefault(host, asyncio.Semaphore(per_host_limit))
                tasks.append(_fetch_one(session, url, global_sem, host_sem, timeout, url_host))

            # gather defensively
            results = await asyncio.gather(*tasks, return_exceptions=True)
            merged: Set[str] = set()
            for r in results:
                if isinstance(r, Exception) or not r:
                    continue
                merged.update(r)
            # send result back to master process
            result_queue.put({"worker_pid": os.getpid(), "urls": merged})

def worker_process_main(
    task_queue: MPQueue,
    result_queue: MPQueue,
    host: str,
    concurrency: int = 50,
    per_host_limit: int = 10,
    timeout: int = 10,
):
    """
    Process target function: start an asyncio loop running worker_async_loop.
    """
    # start event loop and run worker coroutine
    asyncio.run(worker_async_loop(task_queue, result_queue, host, concurrency=concurrency, per_host_limit=per_host_limit, timeout=timeout))

# --------------------- Master (synchronous) ---------------------
def start_workers(n_workers: int, concurrency: int, per_host_limit: int, timeout: int, host: str):
    ctx = get_context("spawn")
    task_q = ctx.Queue()
    result_q = ctx.Queue()
    procs = []
    for _ in range(n_workers):
        p = ctx.Process(target=worker_process_main, args=(task_q, result_q, host, concurrency, per_host_limit, timeout))
        p.daemon = True
        p.start()
        procs.append(p)
    return procs, task_q, result_q

def stop_workers(procs, task_q: MPQueue):
    # send sentinel to each worker
    for _ in procs:
        task_q.put(None)
    for p in procs:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()

def bfs_master(
    urls: list[str],
    max_depth: int,
    host: str,
    n_workers: Optional[int] = None,
    concurrency: int = 50,
    per_host_limit: int = 10,
    timeout: int = 10,
) -> Set[str]:
    """
    Master BFS that distributes each depth's frontier across worker batches and collects results.
    Returns the set of discovered URLs.
    """
    if n_workers is None:
        n_workers = max(1, os.cpu_count() or 2)
    procs, task_q, result_q = start_workers(n_workers, concurrency, per_host_limit, timeout, host)
    try:
        visited: Set[str] = set()
        frontier: List[str] = [u for u in urls if urlparse(u).scheme in ("http", "https")]

        for _ in range(max_depth):
            # remove already visited
            frontier = [u for u in frontier if u not in visited]
            if not frontier:
                break

            # split frontier into n_workers batches (round-robin distribution)
            batches: List[List[str]] = [[] for _ in range(n_workers)]
            for i, u in enumerate(frontier):
                batches[i % n_workers].append(u)

            # enqueue batches
            for b in batches:
                task_q.put(b)

            # collect a result for each batch
            merged_all: Set[str] = set()
            for _ in batches:
                res = result_q.get()  # blocking get
                urls = res.get("urls", set())
                if urls:
                    merged_all.update(urls)

            # new frontier: discovered URLs that are not visited yet
            new_frontier = [u for u in merged_all if u not in visited]
            # mark current frontier as visited
            visited.update(frontier)
            frontier = new_frontier

        # include leftover frontier
        visited.update(frontier)
        return visited
    finally:
        stop_workers(procs, task_q)

# --------------------- Small CLI and filter ---------------------
def filter_mhb(urls: Iterable[str]) -> Set[str]:
    return {u for u in urls if any(i in u for i in ["mhb", "modulhandb", "modulhandbuch", "modulbeschreibung"])}

def main(url: str, max_depth: int, mhb_only: bool = True):

    ext = tldextract.extract(url)
    host = None
    if ext.domain and ext.suffix:
        host = f"{ext.domain}.{ext.suffix}"
    else:
        host = url

    found = bfs_master(
        urls=[url],
        max_depth=max_depth,
        n_workers=os.cpu_count(),
        concurrency=50,
        per_host_limit=10,
        timeout=10,
        host=host
    )
    if mhb_only:
        found = filter_mhb(found)
    
    return sorted(found)

if __name__ == "__main__":
    url = "https://www.uni-augsburg.de"
    # find mhb page
    urls = main(url=url, max_depth=3, mhb_only=True)
    results = set()
    # also dont take all mhb urls but just the one that is the base one or that the others refer to or if none refers or only a little percentage then take all since then each url probably belongs to one mhb
    for i in urls:
        # fetches a lot twice
        result = main(url=i, max_depth=2, mhb_only=True)
        results.update(result)
        # maybe faster to do depth one and remove duplicates
    for i in results:
        result = main(url=i, max_depth=1, mhb_only=True)
        # so when already at mhb don't ignore it by creating a new overset
        results.update(result)
    for u in results:
        print(u)
    