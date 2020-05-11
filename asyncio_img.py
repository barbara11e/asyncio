#!/usr/bin/env python3
# asyncio_img.py

"""Asynchronously get, process and post images."""
import asyncio
import sys
import time
import logging
import requests
from io import BytesIO
from PIL import Image, ImageOps
from asyncio import TimeoutError
from aiohttp import ClientSession, ClientResponseError, \
                    ClientError, \
                    ClientOSError, \
                    ServerTimeoutError

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


HOST_ADDR = 'http://142.93.138.114/images/'

def get_img_urls(url=HOST_ADDR) -> list:
    '''
        Request list of image names & returns images urls

        params: host url
        returns: urls of images (list)
    '''
    try:
        response = requests.get(url)
    except requests.RequestException:
        logger.warning("Request exception has occured with %s", url)
        return []

    img_list_names = [url + _ for _ in response.text.split()]
    return img_list_names


async def process_img(session: ClientSession, url: str) -> None:
    '''
        Request & mirror & upload by POST for multiple images.
        params:
            session: created as a context manager ClientSession
            url: url of image
    '''
    async with session.get(url) as response:
        logger.debug("Read %i from %s with code %i", response.content_length, url, response.status)
        if response.status == 200:
            data = await response.read()
            img = Image.open(BytesIO(data))
            mirrored_image = ImageOps.mirror(img)
            byte_data = BytesIO(ImageOps.mirror(img).tobytes())
            try:
                async with session.post(HOST_ADDR, data=byte_data) as post_response:
                    logger.debug("Data sent with status %s", post_response.status)
            except (ClientResponseError,
                    ClientError,
                    ClientOSError,
                    ServerTimeoutError,
                    TimeoutError) as e:
                logger.warning("Exception was occured in POST request %s", e)
                

async def download_all_img(urls: list) -> None:
    '''
        Share the session across all tasks. 
        Session context works until all of the tasks have completed.
        params:
            urls: urls of images (list)
    '''
    async with ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.ensure_future(process_img(session, url))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=False)


if __name__ == "__main__":

    urls = get_img_urls()

    start_time = time.time()
    asyncio.get_event_loop().run_until_complete(download_all_img(urls))
    duration = time.time() - start_time
    print(duration)
