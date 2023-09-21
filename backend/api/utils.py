from datetime import datetime

from django.http import HttpResponse


def create_shopping_cart(ingredients_cart, user):
    today = datetime.today()
    shopping_cart = (
        f'Shopping cart for: {user.get_full_name()}\n\n'
        f'Date: {today:%Y-%m-%d}\n\n'
    )
    shopping_cart += '\n'.join(
        [
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients_cart
        ]
    )
    shopping_cart += f'\n\nFoodgram ({today:%Y})'
    filename = f'{user.username}_shopping_cart.txt'
    response = HttpResponse(shopping_cart, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
