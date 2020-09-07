import db
import json
import pathlib
from aiohttp import web


class GetNextImageView(web.View):
    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            service_name = self.request.rel_url.query.get('s_name')
            if service_name is None:
                return self.service_not_found()
            try:
                current_id, path = await db.get_next_image(
                    conn, service_name
                )
            except db.ImageNotFound as e:
                response = {
                    'result': str(e)
                }
                return web.json_response(text=json.dumps(response))
            response = {
                'id': current_id,
                'path': str('http://94.41.84.170' / pathlib.Path('media') / path),
            }
            return web.json_response(text=json.dumps(response))

    def service_not_found(self):
        response = {'result': 'service is not defined'}
        return web.json_response(text=json.dumps(response))


class ConfirmReceiptView(web.View):
    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            service_name = self.request.rel_url.query.get('s_name')
            last_id = self.request.rel_url.query.get('last_id')
            if service_name is None:
                return self.service_not_found()
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

    def service_not_found(self):
        response = {'result': 'service is not defined'}
        return web.json_response(text=json.dumps(response))