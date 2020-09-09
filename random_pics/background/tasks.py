import uuid
import asyncio
import aiohttp
import random

from random_pics import db
from random_pics.settings import config

GOOGLE_SEARCH_API_URL = config['google_search_api']['url']
CATEGORIES = config['google_search_api']['categories']


class BaseTask:
    def __init__(self, app, task_manager):
        self.app = app
        self.task = None
        self.task_manager = task_manager

    @classmethod
    def as_task(cls, app, task_manager):
        """
        Representation of any Class Based Task
        :param app:
        :param task_manager:
        :return:
        """
        coro = cls(app, task_manager)
        task = asyncio.create_task(coro.run())
        coro.task = task
        return task

    def run(self, *args, **kwargs):
        """
        Should return coroutine
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplemented


class PeriodicImageRequest(BaseTask):
    async def run(self, *args, **kwargs):
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
                        print(f'{e}')
                        await self.task_manager.start_background_task('periodic_image_count_check', self.app)
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


class PeriodicImageCountCheck(BaseTask):
    async def run(self, *args, **kwargs):
        async with self.app['db'].acquire() as conn:
            while True:
                count = await db.image_count(conn)
                await asyncio.sleep(5)
                if count < 6:
                    print('ALLOW TO DOWNLOAD NEW IMAGES! Image Count: {}'
                          .format(count))
                    self.task.cancel()
                    await self.task_manager.start_background_task(self.app)
                print('NOT YET')
