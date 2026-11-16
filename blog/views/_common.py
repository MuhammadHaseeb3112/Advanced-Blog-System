"""Shared helpers for the blog views."""
from django.shortcuts import (

    redirect

)









from django.contrib import messages
from django.core.cache import cache





# =========================================
# CLEAR BLOG CACHE
# =========================================

def clear_blog_cache():

    cache.clear()

    print(
        'BLOG CACHE CLEARED 🚀'
    )



# =========================================
# AUTHOR OR ADMIN CHECK
# =========================================

def author_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:

            return redirect(
                'login'
        )

        if request.user.role not in [

            'admin',
            'author'

        ]:

            messages.error(

                request,

                'Only authors can access this page.'

            )

            return redirect(

                'blog_list'

            )

        return view_func(

            request,
            *args,
            **kwargs

        )

    return wrapper

# =========================================
# BLOG LIST VIEW
# GLOBAL SEARCH SYSTEM
# =========================================
