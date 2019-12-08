import factory
from django.contrib.auth.models import User, Group
from users.models import AerosimpleUser, Role
from airport.models import Airport
from django.db.models.signals import post_save, pre_save


@factory.django.mute_signals(pre_save, post_save)
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = 'john'


@factory.django.mute_signals(pre_save, post_save)
class AirportFactory(factory.DjangoModelFactory):
    class Meta:
        model = Airport
        django_get_or_create = ('name', 'code')

    name = 'Barcelona'
    code = 'BCN'


@factory.django.mute_signals(pre_save, post_save)
class AerosimpleUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = AerosimpleUser
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    airport = factory.SubFactory(AirportFactory)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


# factories.py
class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    name = "Super Role"

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for perm in extracted:
                self.permissions.add(perm)


class RoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ('name', 'permission_group')

    name = "Super Role"

