from django.contrib import auth
from .decorators import protect

auth.authenticate = protect(auth.authenticate)
