from django.test import TestCase

# Create your tests here.


def func(x):
    return x + 1


def test_answer():
    assert func(3) == 5
