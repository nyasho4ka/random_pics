from views import (
    GetNextImageView, ConfirmReceiptView
)


def setup_routes(app):
    app.router.add_view('/get-next-image', GetNextImageView)
    app.router.add_view('/confirm-receipt', ConfirmReceiptView)
