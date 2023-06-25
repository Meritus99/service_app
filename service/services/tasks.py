import datetime
import time

from celery import shared_task
from celery_singleton import Singleton
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import F


@shared_task(base=Singleton)
def set_price(subscription_id):
    from services.models import Subscription

    with transaction.atomic():
        # Транзакция такая процедура в базе, когда все действия внутри неё будут применяться атомарно,
        # т.е либо всё вместе исполнится либо всё вместе НЕ исполнится.
        # База накапливает изменения внутри транзакции и по окончанию она эти изменения применяет. Атомарно означает что
        # это не может быть применено частично, только всё вместе

        subscription = Subscription.objects.select_for_update().filter(id=subscription_id).annotate(
                annotated_price=F('service__full_price') -
                F('service__full_price') * F('plan__discount_percent') / 100).first()

        subscription.price = subscription.annotated_price
        subscription.save()
    cache.delete(settings.PRICE_CACHE_NAME)

@shared_task(base=Singleton)
def set_comment(subscription_id):
    from services.models import Subscription

    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(id=subscription_id)

        subscription.comment = str(datetime.datetime.now())
        subscription.save()
    cache.delete(settings.PRICE_CACHE_NAME)