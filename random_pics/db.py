import aiopg.sa
import datetime


from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, DateTime
)

meta = MetaData()

# TABLES
image = Table(
    'image', meta,

    Column('id', Integer, primary_key=True),
    Column('path', String(200), nullable=False),
    Column('created_at', DateTime,
           default=datetime.datetime.now, nullable=False),
)

label = Table(
    'label', meta,

    Column('id', Integer, primary_key=True),
    Column('x_center', Integer, nullable=True),
    Column('y_center', Integer, nullable=True),
    Column('width', Integer, nullable=True),
    Column('height', Integer, nullable=True),
    Column('class', String(55), nullable=True),
    Column('image_id', Integer,
           ForeignKey('image.id', ondelete='CASCADE'))
)

service = Table(
    'service', meta,

    Column('id', Integer, primary_key=True),
    Column('service_name', String(55), nullable=False),
    Column('service_address', String(100), nullable=False),
    Column('last_checkout_date', DateTime, nullable=False,
           default=datetime.datetime.now)
)


# INIT AND CLOSE PG
async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()


# Exceptions
class ImageNotFound(Exception):
    pass


# Queries
async def get_next_image(conn, service_name):
    result = await conn.execute(
        service.select()
        .where(service.c.service_name == service_name))

    service_record = await result.first()
    last_date = service_record.get('last_checkout_date')

    result = await conn.execute(
        image.select()
        .where(image.c.created_at >= last_date)
        .order_by(image.c.id.desc())
    )

    image_record = await result.first()
    return image_record.get('path')
