import db
import uuid
import asyncio
import aiohttp
import random
from settings import config

GOOGLE_SEARCH_API_URL = 'https://www.googleapis.com/customsearch/v1'
CATEGORIES = config['google_search_api']['categories']


class PeriodicImageRequest:
    def __init__(self, app):
        self.app = app
        self.task = None

    async def __call__(self, *args, **kwargs):
        async with aiohttp.ClientSession() as session:
            while True:
                params = self.get_params()
                await self.image_request(session, params)
                await asyncio.sleep(2)

    def get_params(self):
        params = config['google_search_api']['query_params']
        params.update({'q': random.choice(CATEGORIES)})
        return params

    async def image_request(self, session, params):
        async with session.get(GOOGLE_SEARCH_API_URL, params=params) as resp:
            json_resp = await resp.json()
            async with self.app['db'].acquire() as conn:
                for image in json_resp['items']:
                    image_name = '{}.jpg'.format(uuid.uuid4())
                    print('IMAGE NAME: {}'.format(image_name))
                    await self.download_image(session, image, image_name)
                    try:
                        await db.add_image(conn, image_name)
                        print('SUCCESS')
                    except db.ImageLimitExceeded as e:
                        await start_background_image_check(self.app)
                        self.task.cancel()

    async def download_image(self, session, image, image_name):
        chunk_size = 1024
        resp = await session.get(image['link'])
        with open('media/{}'.format(image_name), 'wb') as fd:
            while True:
                chunk = await resp.content.read(chunk_size)
                if not chunk:
                    break
                fd.write(chunk)
        resp.close()


class PeriodicImageCountCheck:
    def __init__(self, app):
        self.app = app
        self.task = None

    async def __call__(self, *args, **kwargs):
        async with self.app['db'].acquire() as conn:
            while True:
                count = await db.image_count(conn)
                await asyncio.sleep(5)
                if count < 6:
                    print('ALLOW TO DOWNLOAD NEW IMAGES! Image Count: {}'
                          .format(count))
                    self.task.cancel()
                    await start_background_image_request(self.app)
                print('NOT YET')


async def start_background_image_request(app):
    coro = PeriodicImageRequest(app)
    task = asyncio.create_task(coro())
    coro.task = task
    app['periodic_image_request'] = task


async def start_background_image_check(app):
    coro = PeriodicImageCountCheck(app)
    task = asyncio.create_task(coro())
    coro.task = task
    app['check_images'] = task
