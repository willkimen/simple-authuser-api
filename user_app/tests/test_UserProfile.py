import pytest
from django.db import IntegrityError
from user_app.models import UserProfile


@pytest.fixture
def user_dict():
    return {'email': 'user@email.com',
            'password': '1234',
            'first_name': 'my_name',
            'last_name': 'my_last_name'}


@pytest.mark.django_db
def test_create_instance_UserProfile(user_dict):

    user_instance = UserProfile.objects.create_user(
        email=user_dict['email'],
        password=user_dict['password'],
        first_name=user_dict['first_name'],
        last_name=user_dict['last_name'])

    assert user_instance.email == user_dict['email']
    assert user_instance.check_password(user_dict['password'])
    assert user_instance.first_name == user_dict['first_name']
    assert user_instance.last_name == user_dict['last_name']
    assert not user_instance.is_staff
    assert not user_instance.is_superuser


@pytest.mark.django_db
def test_user_without_email_is_not_created(user_dict):
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(
            password=user_dict['password'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'])


@pytest.mark.django_db
def test_normalize_domain_email(user_dict):
    user = UserProfile.objects.create_user(
        email='email@DOMAINUPPERCASE.com',
        password=user_dict['password'],
        first_name=user_dict['first_name'],
        last_name=user_dict['last_name'])

    assert user.email.islower()


@pytest.mark.django_db
def test_user_without_password_is_not_created(user_dict):
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(
            email=user_dict['email'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'])


@pytest.mark.django_db
def test_unique_email(user_dict):
    with pytest.raises(IntegrityError):
        persisted_user = UserProfile.objects.create_user(
            email=user_dict['email'],
            password=user_dict['password'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'])

        UserProfile.objects.create_user(
            email=persisted_user.email,
            password=user_dict['password'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'])


@pytest.mark.django_db
def test_create_superuser(user_dict):
    superuser = UserProfile.objects.create_superuser(
            email=user_dict['email'],
            password=user_dict['password'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'])

    assert superuser.is_staff
    assert superuser.is_superuser
