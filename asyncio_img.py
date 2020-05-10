#!/usr/bin/env python3
# asyncio_img.py

import asyncio
from io import BytesIO
import requests
import aiohttp
from requests import RequestException
import logging
import sys
import os
from PIL import Image, ImageOps

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

HOST_ADDR = 'http://142.93.138.114/images/'
IMG_DIR = 'images/'

class RequestError(Exception):
    pass

def get_img_names() -> list:
    try:
        response = requests.get(HOST_ADDR)
    except RequestException:
        logger.warning("Request exception has occured with %s", HOST_ADDR)
        return []

    if response.status_code != 200:
        raise RequestError

    img_list_names = response.text.split()
    logger.info("Got list of image names from source: %s", HOST_ADDR)

    return img_list_names


def mk_dir(dir_name=IMG_DIR) -> None:
    try:
        os.mkdir(dir_name)
        logger.info("Directory %s Created", dir_name) 
    except FileExistsError:
        logger.warning("Directory %s already exists", dir_name)


def mirror_img(b_img_data: bytes) -> Image:
    imageStream = BytesIO(b_img_data)
    img = Image.open(imageStream)
    mirror_image = ImageOps.mirror(img)
    return mirror_image


def post_img(image, image_file_path: str, session) -> None:
    url = HOST_ADDR
    b_image = open(image_file_path, 'rb')
    files = {'image': b_image}
    session.post(url, data=b_image)


async def dowload_file(file_name: str, session) -> None:
    image_url = HOST_ADDR + file_name
    img_data = requests.get(image_url).content
    img = mirror_img(img_data)

    image_file_path = IMG_DIR + file_name
    img.save(image_file_path)
    await post_img(img, image_file_path, session=session)


async def dowload_transform_send_images(img_names_list: list) -> None:
    async with aiohttp.ClientSession() as session:
        tasks = []
        for image_name in img_names_list:
            tasks.append(
                dowload_file(image_name, session=session)
            )
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    mk_dir()
    img_names_list = get_img_names()
    asyncio.run(dowload_transform_send_images(img_names_list))