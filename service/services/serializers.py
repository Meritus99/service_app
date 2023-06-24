from rest_framework import serializers

from services.models import Subscription, Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('__all__')


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()
    client_name = serializers.CharField(source='client.company_name')
    email = serializers.CharField(source='client.user.email')

    price = serializers.SerializerMethodField()
    """ Здесь сработает соглашение об использовании имен. Когда используется SerializerMethodField, сериализатор ищет функцию
   с названием поля и префиксом get_, в нашем случае поле имеет имя price, и метод сериализатора будет искать функцию с именем
   get_price, дабы подставить результат её работы в поле """

    def get_price(self, instance):
        return instance.price
        #return (instance.service.full_price -
        #        instance.service.full_price * (instance.plan.discount_percent / 100))

    class Meta:
        model = Subscription
        fields = ('id', 'plan_id', 'client_name', 'email', 'plan', 'price')
        # В филдах можем указывать два вида филдов, те что приписаны в модели Subscription и те что мы прописали
        # самостоятельно (в классе SubscriptionSerializer)

