from views import (
    get_next_image
)


def setup_routes(app):
    app.router.add_get('/get-next-image', get_next_image)
