from sqlalchemy import create_engine, MetaData

from random_pics.settings import config
from random_pics.db import image, label, service

DSN = 'postgresql://{user}:{password}@{host}:{port}/{database}'


def create_tables(engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[image, label, service])


def default_service(engine):
    conn = engine.connect()

    name, address = config['default_service']['name'], config['default_service']['address']

    conn.execute(service.insert(), [
        {
            'name': name,
            'address': address,
        },
    ])
    conn.close()


if __name__ == '__main__':
    db_url = DSN.format(**config['postgres'])
    engine = create_engine(db_url)

    create_tables(engine)
    default_service(engine)
