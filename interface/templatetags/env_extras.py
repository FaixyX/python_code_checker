from os import getenv as env
from django import template

register = template.Library()


@register.simple_tag
def get_baseurl():
    return env("url")


@register.simple_tag
def get_resetlink():
    return env("resetlink")