import db
import json
import pathlib
from aiohttp import web


async def get_next_image(request):
    async with request.app['db'].acquire() as conn:
        service_name = request.rel_url.query.get('s_name')
        if service_name is None:
            return service_not_found()
        try:
            path = await db.get_next_image(
                conn, service_name
            )
        except db.ImageNotFound as e:
            raise web.HTTPNotFound(text=str(e))
        return web.FileResponse(path=pathlib.Path('media') / path)


def service_not_found():
    response = {'response': 'service is not defined'}
    return web.json_response(text=json.dumps(response))
