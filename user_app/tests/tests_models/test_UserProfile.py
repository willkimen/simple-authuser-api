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
def test_creates_user_instance(user_dict):

    user_instance = UserProfile.objects.create_user(**user_dict)

    assert user_instance.email == user_dict['email']
    assert user_instance.check_password(user_dict['password'])
    assert user_instance.first_name == user_dict['first_name']
    assert user_instance.last_name == user_dict['last_name']
    assert not user_instance.is_staff
    assert not user_instance.is_superuser


@pytest.mark.django_db
def test_does_not_create_user_without_email(user_dict):
    del user_dict['email']
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(**user_dict)


@pytest.mark.django_db
def test_normalizes_email_domain(user_dict):
    user_dict['email'] = 'email@DOMAINUPPERCASE.com' 
    user = UserProfile.objects.create_user(**user_dict)

    assert user.email.islower()


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(user_dict):
    with pytest.raises(IntegrityError):
        UserProfile.objects.create_user(**user_dict)
        UserProfile.objects.create_user(**user_dict)


@pytest.mark.django_db
def test_does_not_create_user_without_password(user_dict):
    del user_dict['password']
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(**user_dict)


@pytest.mark.django_db
def test_creates_superuser(user_dict):
    superuser = UserProfile.objects.create_superuser(**user_dict)

    assert superuser.is_staff
    assert superuser.is_superuser
