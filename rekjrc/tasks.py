from celery import shared_task
from PIL import Image

@shared_task
def resize_avatar(app_label, model_name, pk):
    from django.apps import apps
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=pk)
    if instance.avatar and hasattr(instance.avatar, 'path'):
        try:
            img = Image.open(instance.avatar.path)
            img.thumbnail((300, 300))
            img.save(instance.avatar.path, optimize=True, quality=85)
        except Exception as e:
            print("Avatar resize failed:", e)

@shared_task
def resize_product_thumbnail(product_id):
    """
    Regenerates Product.thumbnail from whichever ProductImage currently
    sorts first (products.models.Product.primary_image). Triggered by
    ProductImage.save()/delete() -- see products/models.py -- so it
    re-runs whenever images are added, removed, or re-sorted, which keeps
    "image 0" behaving as the thumbnail source regardless of how it got
    that way.

    Writes a resized *copy* into Product.thumbnail rather than resizing
    the ProductImage file in place (unlike resize_avatar above) -- the
    original upload stays full quality for the product detail page's
    gallery; only the derived thumbnail is small.
    """
    import io
    from django.apps import apps
    from django.core.files.base import ContentFile

    Product = apps.get_model('products', 'Product')
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return

    primary = product.images.first()
    if not primary or not primary.image or not hasattr(primary.image, 'path'):
        if product.thumbnail:
            product.thumbnail.delete(save=False)
            product.thumbnail = None
            product.save(update_fields=['thumbnail'])
        return

    try:
        img = Image.open(primary.image.path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((500, 500))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', optimize=True, quality=85)
        if product.thumbnail:
            product.thumbnail.delete(save=False)
        product.thumbnail.save(
            f"product-{product.pk}-thumb.jpg", ContentFile(buffer.getvalue()), save=False)
        product.save(update_fields=['thumbnail'])
    except Exception as e:
        print("Product thumbnail resize failed:", e)