import json
import logging
import pathlib
from aiohttp import web
from random_pics.settings import config
from random_pics import db

logger = logging.getLogger('dev')


class GetNextImageView(web.View):
    async def get(self):
        service_name = self.request.rel_url.query.get('s_name')
        if service_name is None:
            return web.json_response(data={'result': 'service is not defined'})
        async with self.request.app['db'].acquire() as conn:
            try:
                current_id, path = await db.get_next_image(
                    conn, service_name
                )
            except db.ImageNotFound as e:
                response = {
                    'result': str(e)
                }
                logger.error(f'[{self.__class__.__name__}] Image not found: {e}')
            except db.ServiceNotFound as e:
                response = {
                    'result': str(e)
                }
                logger.error(f'[{self.__class__.__name__}] Service not found: {e}')
            except Exception as e:
                response = {
                    'result': str(e)
                }
                logger.error(f'[{self.__class__.__name__}] Unknown error: {e}')
            else:
                response = {
                    'id': current_id,
                    'path': str(pathlib.Path(config['settings']['address']) / pathlib.Path('media') / path),
                }
            return web.json_response(text=json.dumps(response))


class ConfirmReceiptView(web.View):
    async def get(self):
        service_name = self.request.rel_url.query.get('s_name')
        if service_name is None:
            return web.json_response(data={'result': 'service is not defined'})
        last_id = self.request.rel_url.query.get('last_id')
        if last_id is None:
            return web.json_response(data={'result': 'last_id is not defined'})

        async with self.request.app['db'].acquire() as conn:
            try:
                await db.service_last_checkout_update(
                    conn, service_name, last_id
                )
            except db.ServiceNotFound as e:
                response = {
                    'result': str(e)
                }
                logger.error(f'[{self.__class__.__name__}] Service not found: {e}')
            except Exception as e:
                response = {
                    'result': str(e)
                }
                logger.error(f'[{self.__class__.__name__}] Unexpected exception: {e}')
            else:
                response = {
                    'result': 'ok'
                }
            return web.json_response(text=json.dumps(response))
