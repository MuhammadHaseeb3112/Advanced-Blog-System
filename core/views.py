from django.shortcuts import render


# =========================================
# HOME PAGE
# =========================================

from django.core.cache import cache

from django.db.models import Count, Q

from accounts.models import CustomUser
from blog.models import BlogPost, Category, Comment


def home(request):

    # =====================================
    # FEATURED POSTS
    # =====================================

    featured_posts = BlogPost.objects.published(
    ).optimized(
    ).with_likes_count(
    ).with_comments_count(
    ).order_by('-publish_at', '-created_at')[:8]

    # =====================================
    # TRENDING POSTS FROM REDIS
    # =====================================

    trending_posts = cache.get(
        'trending_posts'
    )

    # =====================================
    # FALLBACK IF CACHE EMPTY
    # =====================================

    if not trending_posts:

        print(
            'TRENDING POSTS DB HIT 🔥'
        )

        trending_posts = BlogPost.objects.published(
        ).optimized(
        ).trending()[:5]

        cache.set(

            'trending_posts',

            trending_posts,

            timeout=60 * 60

        )

    else:

        print(
            'TRENDING POSTS CACHE HIT 🚀'
        )

    published = BlogPost.objects.published()
    context = {
        'featured_posts': featured_posts,
        'trending_posts': trending_posts,
        'stats': {
            'posts': published.count(),
            'authors': CustomUser.objects.filter(posts__in=published).distinct().count(),
            'members': CustomUser.objects.count(),
            'comments': Comment.objects.filter(post__in=published).count(),
        },
        'categories': Category.objects.annotate(
            total=Count('posts', filter=Q(posts__in=published))
        ).filter(total__gt=0).order_by('-total', 'name'),
    }

    return render(

        request,

        'home.html',

        context

    )