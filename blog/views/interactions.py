"""AJAX endpoints: like, bookmark and comment."""
from django.shortcuts import (

    get_object_or_404

)



from django.contrib.auth.decorators import (
    login_required
)



from blog.models import (

    BlogPost,
    Comment,
    Notification,


)

from django.http import JsonResponse

from django.template.loader import render_to_string




from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from ._common import clear_blog_cache


@login_required
def bookmark_post(request, slug):

    if request.method != 'POST':

        return JsonResponse({

            'success': False,
            'message': 'Invalid request'

        }, status=400)

    post = get_object_or_404(

        BlogPost.objects.published(),
        slug=slug

    )

    bookmarked = False

    # =====================================
    # REMOVE BOOKMARK
    # =====================================

    if request.user in post.bookmarks.all():

        post.bookmarks.remove(request.user)

    # =====================================
    # ADD BOOKMARK
    # =====================================

    else:

        post.bookmarks.add(request.user)

        bookmarked = True


    clear_blog_cache()

    # =====================================
    # REALTIME BOOKMARK UPDATE
    # =====================================

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(
        f'blog_{post.id}',

        {

            'type': 'bookmark_update',

            'bookmarks_count': (

                post.bookmarks.count()

            ),

        }

    )

    return JsonResponse({

        'success': True,

        'bookmarked': bookmarked,

        'total_bookmarks': (

            post.bookmarks.count()

        ),

    })

# =========================================
# AJAX LIKE POST
# =========================================

@login_required
def like_post(request, slug):

    if request.method != 'POST':

        return JsonResponse({

            'success': False,
            'message': 'Invalid request method'

        }, status=400)

    post = get_object_or_404(

        BlogPost.objects.published(),
        slug=slug

    )

    liked = False

    # =====================================
    # REMOVE LIKE
    # =====================================

    if post.likes.filter(id=request.user.id).exists():

        post.likes.remove(request.user)

        # DELETE OLD LIKE NOTIFICATION

        Notification.objects.filter(

            sender=request.user,
            receiver=post.author,
            post=post,
            notification_type='like'

        ).delete()

    # =====================================
    # ADD LIKE
    # =====================================

    else:

        post.likes.add(request.user)

        liked = True

        # CREATE NOTIFICATION ONLY ONCE

        if request.user != post.author:

            notification_exists = Notification.objects.filter(

                sender=request.user,
                receiver=post.author,
                post=post,
                notification_type='like'

            ).exists()

            if not notification_exists:

                Notification.objects.create(

                    receiver=post.author,
                    sender=request.user,
                    notification_type='like',
                    post=post

                )

            # =====================================
            # REALTIME NOTIFICATION
            # =====================================

            unread_count = Notification.objects.filter(

                receiver=post.author,
                is_read=False

            ).count()

            channel_layer = get_channel_layer()

            async_to_sync(
                channel_layer.group_send
            )(

                f'user_{post.author.id}',

                {

                    'type': 'send_notification',

                    'message': f'{request.user.username} liked your post ❤️',

                    'unread_count': unread_count,

                }

            )

    clear_blog_cache()

    # =====================================
    # REALTIME LIKE UPDATE
    # =====================================

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(
        f'blog_{post.id}',

        {

            'type': 'like_update',

            'likes_count': (

                post.likes.count()

            ),

        }

    )

    return JsonResponse({

        'success': True,

        'liked': liked,

        'total_likes': (

            post.likes.count()

        ),

    })

# =========================================
# AJAX COMMENT SYSTEM
# =========================================

@login_required
def add_comment(request, slug):

    if request.method != 'POST':

        return JsonResponse({

            'success': False,
            'message': 'Invalid request'

        }, status=400)

    post = get_object_or_404(

        BlogPost.objects.published(),
        slug=slug

    )

    content = request.POST.get(

        'content'

    )

    # Rating is optional (defaults to 5) and kept within 1-5.
    try:
        rating = int(request.POST.get('rating') or 5)
    except ValueError:
        rating = 5
    rating = min(max(rating, 1), 5)

    # =====================================
    # VALIDATION
    # =====================================

    if not content:

        return JsonResponse({

            'success': False,
            'message': 'Comment cannot be empty'

        }, status=400)

    # =====================================
    # CREATE COMMENT
    # =====================================

    comment = Comment.objects.create(

        post=post,
        author=request.user,
        content=content,
        rating=rating

    )

    clear_blog_cache()

    # =====================================
    # CHANNEL LAYER
    # =====================================

    channel_layer = get_channel_layer()

    # =====================================
    # CREATE NOTIFICATION
    # =====================================

    if request.user != post.author:

        Notification.objects.create(

            receiver=post.author,
            sender=request.user,
            notification_type='comment',
            post=post

        )

        unread_count = Notification.objects.filter(

            receiver=post.author,
            is_read=False

        ).count()

        # =====================================
        # REALTIME NOTIFICATION
        # =====================================

        async_to_sync(
            channel_layer.group_send
        )(

            f'user_{post.author.id}',

            {

                'type': 'send_notification',

                'message': f'{request.user.username} commented on your post 💬',

                'unread_count': unread_count,

            }

        )

    # =====================================
    # RENDER COMMENT HTML
    # =====================================

    html = render_to_string(

        'includes/comment_card.html',

        {

            'comment': comment

        },

        request=request

    )

    # =====================================
    # REALTIME COMMENT UPDATE
    # =====================================

    async_to_sync(
        channel_layer.group_send
    )(
        f'blog_{post.id}',

        {

            'type': 'comment_update',

            'comments_count': (

                post.comments.count()

            ),

            'comment_html': html,

        }

    )

    return JsonResponse({

        'success': True,

        'comment_html': html,

        'total_comments': (

            post.comments.count()

        ),

    })

    
# =========================================
# DASHBOARD
# =========================================
