from celery import shared_task
from store_app.models import Product


@shared_task
def inform_product_creation(product_id):
    """
    Асинхронная задача Celery для информирования о создании продукта.
    Выполняется в фоновом режиме через Celery Worker. Получает ID продукта,
    загружает его из базы данных и выводит информацию о названии и времени создания.

    Args:
        product_id (int): Уникальный идентификатор продукта в базе данных.
            Должен соответствовать существующему объекту Product.
    """
    product = Product.objects.get(id=product_id)
    print(f"{product.name} был создан в {product.created_at}")


