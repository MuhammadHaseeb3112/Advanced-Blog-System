"""Signed-in user pages: dashboard, saved posts, profile and my posts."""
from django.shortcuts import (

    render,
    redirect

)



from django.contrib.auth.decorators import (
    login_required
)


from django.core.paginator import (
    Paginator
)

from blog.models import (

    BlogPost,
    Comment,
    Category,
    Tag,


)

from accounts.models import CustomUser


from django.contrib import messages
from django.core.cache import cache

from django.db.models import Q, Sum

from django.db.models import Count

from django.utils import timezone
import json



@login_required
def dashboard(request):

    user = request.user

    # =====================================
    # REDIS ANALYTICS CACHE
    # =====================================

    analytics = cache.get('dashboard_analytics')
    if analytics is None:
        # Empty right after a deploy or cache flush: build it once now
        # instead of showing empty charts until the hourly task runs.
        from blog.tasks import calculate_dashboard_analytics
        calculate_dashboard_analytics()
        analytics = cache.get('dashboard_analytics') or {}

    # =====================================
    # USER POSTS    
    # =====================================

    user_posts = BlogPost.objects.by_author(
        user
    ).optimized()

    # =====================================
    # OPTIMIZED ENGAGEMENT
    # =====================================

    annotated_posts = user_posts.annotate(

        likes_total=Count(
            'likes',
            distinct=True
        ),

        comments_total=Count(
            'comments',
            distinct=True
        )
    )

    # =====================================
    # PLATFORM TOTALS
    # =====================================

    total_platform_likes = sum(

        BlogPost.objects.annotate(
            likes_count=Count('likes')
        ).values_list(
            'likes_count',
            flat=True
        )

    )

    total_platform_bookmarks = sum(

        BlogPost.objects.annotate(
            bookmarks_count=Count('bookmarks')
        ).values_list(
            'bookmarks_count',
            flat=True
        )

    )


    # =====================================
    # AUTHOR ENGAGEMENT
    # =====================================

    total_post_likes = sum(
        post.likes.count()
        for post in user_posts
    )

    total_post_comments = Comment.objects.filter(
        post__author=user
    ).count()

    # =====================================
    # USER ACTIVITY
    # =====================================

    liked_posts = BlogPost.objects.filter(

        likes=user

    )

    commented_posts = BlogPost.objects.filter(

        comments__author=user

    ).distinct()

    saved_posts = user.bookmarked_posts.all()



    # =====================================
    # TOP CATEGORIES JSON
    # =====================================

    top_categories = analytics.get(

        'top_categories',

        []

    )

    top_categories_labels = json.dumps([

        category['name']

        for category in top_categories

    ])

    top_categories_counts = json.dumps([

        category['total_posts']

        for category in top_categories

    ])




    # =====================================
    # TRENDING POSTS
    # =====================================

    trending_posts = BlogPost.objects.filter(
        status='published'
    ).order_by(
        '-views'
    )[:5]

    

    # =====================================
    # BASE CONTEXT
    # =====================================

    context = {
            # User Activity
        'total_liked': liked_posts.count(),
        'total_saved': saved_posts.count(),
        'total_commented': commented_posts.count(),

        'my_posts_likes': total_post_likes,
        'my_posts_comments': total_post_comments,

        

        # Real-time Platform Stats
        'total_users': CustomUser.objects.count(),
        'total_blog_posts': BlogPost.objects.count(),
        'total_platform_comments': Comment.objects.count(),
        'total_platform_likes': total_platform_likes,
        'total_platform_bookmarks': total_platform_bookmarks,
        'total_categories': Category.objects.count(),
        'total_tags': Tag.objects.count(),
        'total_views': BlogPost.objects.aggregate(
            total=Sum('views')
        )['total'] or 0,

        # Charts
        'top_categories': top_categories,
        'top_categories_labels': top_categories_labels,
        'top_categories_counts': top_categories_counts,
        'trending_posts': trending_posts,
    }

    # =====================================
    # AUTHOR + ADMIN
    # =====================================

    if user.role in ['author', 'admin']:

        context.update({

            # =================================
            # POSTS
            # =================================

            'total_posts': user_posts.count(),

            'published_posts_count': user_posts.filter(

                status='published'

            ).count(),

            'draft_posts_count': user_posts.filter(

                status='draft'

            ).count(),

            'scheduled_posts_count': user_posts.filter(

                status='draft',

                publish_at__gt=timezone.now()

            ).count(),


        })

    # =====================================
    # AUTHOR
    # =====================================

    if user.role == 'author':

        context.update({

            'is_author': True,

        })

    # =====================================
    # ADMIN
    # =====================================

    elif user.role == 'admin':

        context.update({

            'is_admin': True,

            # =================================
            # PLATFORM STATS
            # =================================

            'total_users': analytics.get(

                'total_users',

                0

            ),

            'total_blog_posts': analytics.get(

                'total_posts',

                0

            ),

            'total_platform_comments': analytics.get(

                'total_comments',

                0

            ),

            'total_categories': analytics.get(

                'total_categories',

                0

            ),

            'total_tags': analytics.get(

                'total_tags',

                0

            ),

        })

    # =====================================
    # SIMPLE USER
    # =====================================

    else:

        context.update({

            'is_user': True,

        })

    return render(

        request,

        'blog/dashboard.html',

        context

    )

    
# =========================================
# SAVED POSTS
# =========================================

@login_required
def saved_posts(request):

    posts = request.user.bookmarked_posts.all(
    ).select_related(

        'author',
        'category'

    ).prefetch_related(

        'tags',
        'likes',
        'comments'

    )

    context = {

        'posts': posts

    }

    return render(

        request,

        'blog/saved_posts.html',

        context

    )


# =========================================
# PROFILE VIEW
# =========================================

@login_required
def profile_view(request):

    user = request.user

    user_posts = BlogPost.objects.by_author(
        user
    ).optimized()

    bookmarked_posts = user.bookmarked_posts.all()

    liked_posts = BlogPost.objects.filter(
        likes=user
    )

    commented_posts = BlogPost.objects.filter(
        comments__author=user
    ).distinct()

    if request.method == 'POST':

        username = request.POST.get(
        'username'
        ).strip()

        if not username:

            messages.error(

            request,

            'Username is required.'

            )

            return redirect(
                'profile'
            )

        user.username = username

        email = request.POST.get('email')

        if CustomUser.objects.exclude(

            id=user.id

        ).filter(

        email=email

        ).exists():

            messages.error(

            request,

            'Email already exists.'

        )

            return redirect('profile')

        user.email = email

        profile_image = request.FILES.get(
            'profile_image'
        )

        if profile_image:

            user.profile_image = profile_image

        user.save()

        messages.success(

            request,

            'Profile updated successfully.'

        )

        return redirect(
            'profile'
        )

    context = {

        'user_posts': user_posts,

        'bookmarked_posts': bookmarked_posts,

        'liked_posts': liked_posts,

        'commented_posts': commented_posts,

    }

    return render(

        request,

        'blog/profile.html',

        context

    )


# =========================================
# MY POSTS
# =========================================

@login_required
def my_posts(request):

    posts = BlogPost.objects.by_author(
        request.user
    ).optimized(
    ).with_likes_count(
    ).with_comments_count(
    ).with_average_rating()

    # =====================================
    # SEARCH
    # =====================================

    search = request.GET.get(
        'search'
    )

    if search:

        search = search.strip()

        posts = posts.filter(

            Q(title__icontains=search) |

            Q(short_description__icontains=search)

        )

    # =====================================
    # STATUS FILTER
    # =====================================

    status = request.GET.get(
        'status'
    )

    if status:

        posts = posts.filter(
            status=status
        )

    posts = posts.distinct()

    # =====================================
    # PAGINATION
    # =====================================

    paginator = Paginator(

        posts,
        9

    )

    page_number = request.GET.get(
        'page'
    )

    page_obj = paginator.get_page(
        page_number
    )

    context = {

        'posts': page_obj,

        'page_obj': page_obj,

        'search_query': search,

        'selected_status': status,

        'results_count': paginator.count,

    }

    return render(

        request,

        'blog/my_posts.html',

        context

    )

# =========================================
# CREATE POST
# =========================================
