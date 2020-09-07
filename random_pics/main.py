import aiohttp_jinja2
import jinja2
from aiohttp import web
from routes import setup_routes
from settings import config, BASE_DIR
from db import init_pg, close_pg


app = web.Application()
app['config'] = config
aiohttp_jinja2.setup(
    app,
    loader=jinja2.FileSystemLoader(str(BASE_DIR / 'random_pics' / 'templates'))
)
setup_routes(app)
app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)
web.run_app(app)
