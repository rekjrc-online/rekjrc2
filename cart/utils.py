from .models import Cart


def get_or_create_cart(request, store):
    """
    Returns the open (not checked-out) Cart for the current visitor at this
    specific store, creating one if needed. A shopper can have separate
    open carts at different stores at the same time -- each is independent.
    Logged-in users get a cart tied to their account; anonymous visitors
    get one tied to their session key.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(store=store, user=request.user, checked_out=False)
        return cart

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(
        store=store,
        session_key=session_key,
        user=None,
        checked_out=False,
    )
    return cart
