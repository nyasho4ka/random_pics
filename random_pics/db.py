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
    Column('name', String(55), nullable=False),
    Column('address', String(100), nullable=False),
    Column('last_checkout_id', Integer, nullable=False,
           server_default='1')
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


class ImageLimitExceeded(Exception):
    pass


class ConfirmError(Exception):
    pass


class ServiceNotFound(Exception):
    pass


# Queries
async def get_next_image(conn, service_name):
    result = await conn.execute(
        service.select()
        .where(service.c.name == service_name))

    service_record = await result.first()
    last_id = service_record.get('last_checkout_id')

    result = await conn.execute(
        image.select()
        .where(image.c.id >= last_id)
        .order_by(image.c.id.desc())
    )

    image_record = await result.first()
    if image_record is None:
        raise ImageNotFound('there is no new image yet')
    return image_record.get('id'), image_record.get('path')


async def service_last_checkout_update(conn, service_name):
    image_id = await get_last_image_id(conn)
    service_last_checkout_id = await get_service_last_checkout_id(conn, service_name)

    if (service_last_checkout_id - image_id) >= 1:
        raise ConfirmError("image receipt can't be confirmed. unreachable index")

    await conn.execute(
        service.update()
        .values(last_checkout_id=service.c.last_checkout_id + 1)
        .where(service.c.name == service_name)
    )


async def get_last_image_id(conn):
    result = await conn.execute(
        image.select()
        .order_by(image.c.id)
    )

    image_record = await result.first()
    return image_record.get('id')


async def get_service_last_checkout_id(conn, service_name):
    result = await conn.execute(
        service.select()
        .where(service.c.name == service_name)
    )

    service_record = await result.first()
    if service_record is None:
        raise ServiceNotFound('there is no {service_name} service'.
                              format(service_name=service_name))

    return service_record.get('last_checkout_id')


async def add_image(conn, image_name):
    count = await image_count(conn)
    if count < 6:
        await insert_image(conn, image_name)
    else:
        raise ImageLimitExceeded('too much images!')


async def image_count(conn):
    result = await conn.execute(
        image.select()
    )
    count = result.rowcount
    return count


async def insert_image(conn, image_name):
    await conn.execute(
        image.insert()
        .values(
            path=image_name
        )
    )
