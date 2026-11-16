"""Notifications and the user's liked and commented posts."""
from django.shortcuts import (

    render,
    redirect

)



from django.contrib.auth.decorators import (
    login_required
)



from blog.models import (

    BlogPost,


)



from django.contrib import messages






@login_required
def notifications(request):

    # =====================================
    # ROLE PROTECTION
    # =====================================

    if request.user.role not in [

        'admin',
        'author'

    ]:

        messages.error(

            request,
            'You are not allowed to access notifications.'

        )

        return redirect(

            'blog_list'

        )

    # =====================================
    # GET ALL NOTIFICATIONS
    # =====================================

    notifications = request.user.notifications.select_related(

        'sender',
        'post'

    ).order_by(

        '-created_at'

    )

    # =====================================
    # UNREAD COUNT
    # =====================================

    unread_count = notifications.filter(

        is_read=False

    ).count()

    # =====================================
    # MARK AS READ AFTER OPENING PAGE
    # =====================================

    notifications.filter(

        is_read=False

    ).update(

        is_read=True

    )

    context = {

        'notifications': notifications,
        'unread_count': unread_count,

    }

    return render(

        request,
        'blog/notifications.html',
        context

    )


# =========================================
# LIKED POSTS
# =========================================

@login_required
def liked_posts(request):

    posts = BlogPost.objects.filter(
        likes=request.user
    ).optimized()

    context = {

        'posts': posts,

    }

    return render(

        request,

        'blog/liked_posts.html',

        context

    )


# =========================================
# COMMENTED POSTS
# =========================================

@login_required
def commented_posts(request):

    posts = BlogPost.objects.filter(

        comments__author=request.user

    ).distinct().optimized()

    context = {

        'posts': posts,

    }

    return render(

        request,

        'blog/commented_posts.html',

        context

    )


# =========================================
# MANAGE USERS
# =========================================
