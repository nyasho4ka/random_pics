import aiohttp_jinja2
import jinja2
from aiohttp import web
from random_pics.routes import setup_routes
from random_pics.settings import config, BASE_DIR
from random_pics.db import init_pg, close_pg
from random_pics.background.manager import background_task_manager


app = web.Application()
app['config'] = config
aiohttp_jinja2.setup(
    app,
    loader=jinja2.FileSystemLoader(str(BASE_DIR / 'random_pics' / 'templates'))
)
setup_routes(app)
app.on_startup.append(init_pg)
app.on_startup.append(background_task_manager.add_background_task('periodic_image_request', app))
app.on_cleanup.append(close_pg)
web.run_app(app)
