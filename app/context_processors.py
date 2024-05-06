from .models import *

def cart(request):
    cart_count = 0
    if 'email' in request.session and 'islogin' in request.session and request.session['islogin']:
        user = User.objects.get(user_email=request.session['email'])
        cart_count = user.cart.cart_item_set.count()
    return {'cart_count': cart_count}

