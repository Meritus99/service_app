from django.conf import settings
from django.db.models import Prefetch, F, Sum
from django.shortcuts import render
from django.core.cache import cache
from rest_framework.viewsets import ReadOnlyModelViewSet

from clients.models import Client
from services.models import Subscription
from services.serializers import SubscriptionSerializer


class SubscriptionView(ReadOnlyModelViewSet):
    queryset = Subscription.objects.all().prefetch_related(
        'plan',
        Prefetch('client',
                 queryset=Client.objects.all().select_related('user').only('company_name', 'user__email'))
    )#.annotate(price=F('service__full_price') -
     #                F('service__full_price') * F('plan__discount_percent') / 100)

    """ F - функция из db.models при помощи которой можно обращаться к какому-то полю.
    annotate - функция ORM (относится к каждому из Subscription) которая позволяет вычислить наше число на уровне базы,
    а не Питона(как если бы я реализовал это в serializers.py)
    Однако способ с дополнением сериализатора через SerializerMethodField так же довольно удобный, не стоит об этом забывать! """
    serializer_class = SubscriptionSerializer

    # Изменение логики работы внутренних методов очень нежелательное действие!
    def list(self, request, *args, **kwargs):
        # в методе list обрабатывается запрос и формируется ответ
        queryset = self.filter_queryset(self.get_queryset())
        response = super().list(request, *args, **kwargs)
        # через super мы обратились к месту откуда переопределили метод, т.е к базовому классу

        price_cache = cache.get(settings.PRICE_CACHE_NAME)

        if price_cache:
            total_price = price_cache
        else:
            total_price = queryset.aggregate(total=Sum('price')).get('total')
            cache.set(settings.PRICE_CACHE_NAME, total_price, 60 * 60)

        """ Агрегационные функции в SQL позволяют вывести суммарную инфу по группе записей (прямое отличие от annotate). Например 
        получая группу Subscription, можем по всей группе посчитать суммарные значения (наприм. сумму всех заказов, минимальный заказ, тд.)"""
        response_data = {'result': response.data}

        response_data['total_amout'] = total_price
        """ Чтобы подсчитать сумму цен на питоне, пришлось бы проитерировать все выводы response и сложить значения в
        переменную, а здесь мы это делаем при помощи функции базы (Sum), но чтобы это было возможно, мы должны 
        с аннотировать и потом с агрегировать уже с анотированные данные """
        response.data = response_data
        return response
