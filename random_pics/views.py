import db
import json
import pathlib
from settings import config
from aiohttp import web


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
                return web.json_response(text=json.dumps(response))
            except db.ServiceNotFound as e:
                response = {
                    'result': str(e)
                }
            else:
                response = {
                    'id': current_id,
                    'path': str(config['settings']['address'] / pathlib.Path('media') / path),
                }
            return web.json_response(text=json.dumps(response))


class ConfirmReceiptView(web.View):
    async def get(self):
        service_name = self.request.rel_url.query.get('s_name')
        last_id = self.request.rel_url.query.get('last_id')
        if service_name is None:
            return web.json_response(data={'result': 'service is not defined'})
        async with self.request.app['db'].acquire() as conn:
            try:
                await db.service_last_checkout_update(
                    conn, service_name, last_id
                )
            except db.ServiceNotFound as e:
                raise web.HTTPNotFound(text=str(e))
            except db.ConfirmError as e:
                response = {
                    'result': str(e)
                }
                return web.json_response(text=json.dumps(response))
            response = {
                'result': 'ok'
            }
            return web.json_response(text=json.dumps(response))
