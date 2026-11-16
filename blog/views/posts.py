"""Public post pages: list with search, detail, category and tag pages."""
from django.shortcuts import (

    render,
    get_object_or_404

)


from django.views.generic import (

    ListView,
    DetailView

)



from django.core.paginator import (
    Paginator
)

from blog.models import (

    BlogPost,
    Category,
    Tag,


)



from django.core.cache import cache

from django.db.models import F





class BlogListView(
    ListView
):

    model = BlogPost

    template_name = 'blog/blog_list.html'

    context_object_name = 'posts'

    paginate_by = 9

    def get_queryset(self):

        # =====================================
        # REQUEST PARAMETERS
        # =====================================

        search = self.request.GET.get(
            'search',
            ''
        ).strip()

        category = self.request.GET.get(
            'category',
            ''
        ).strip()

        tag = self.request.GET.get(
            'tag',
            ''
        ).strip()

        page = self.request.GET.get(
            'page',
            1
        )

        # =====================================
        # UNIQUE CACHE KEY
        # =====================================

        cache_key = (

            f'blog_list_'

            f'{search}_'

            f'{category}_'

            f'{tag}_'

            f'page_{page}'

        )

        # =====================================
        # CHECK REDIS CACHE
        # =====================================

        cached_queryset = cache.get(
            cache_key
        )

        if cached_queryset:

            print(
                'CACHE HIT 🚀'
            )

            return cached_queryset

        print(
            'DATABASE HIT 🔥'
        )

        # =====================================
        # BASE QUERYSET
        # =====================================

        queryset = BlogPost.objects.published(
        ).optimized(
        ).with_likes_count(
        ).with_comments_count(
        ).with_average_rating()

        # =====================================
        # GLOBAL SEARCH
        # =====================================

        if search:

            queryset = queryset.search(
                search
            )

        # =====================================
        # CATEGORY FILTER
        # =====================================

        if category:

            queryset = queryset.by_category(
                category
            )

        # =====================================
        # TAG FILTER
        # =====================================

        if tag:

            queryset = queryset.by_tag(
                tag
            )

        queryset = queryset.distinct().order_by(
    '-created_at'
)

        # =====================================
        # SAVE QUERYSET TO REDIS
        # =====================================

        cache.set(

            cache_key,

            queryset,

            timeout=60 * 5

        )

        return queryset

    # =========================================
    # CONTEXT
    # =========================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        # =====================================
        # CACHED CATEGORIES
        # =====================================

        categories = cache.get(
            'all_categories'
        )

        if not categories:

            print(
                'CATEGORIES DB HIT 🔥'
            )

            categories = Category.objects.all()

            cache.set(

                'all_categories',

                categories,

                timeout=60 * 30

            )

        else:

            print(
                'CATEGORIES CACHE HIT 🚀'
            )

        # =====================================
        # CACHED TAGS
        # =====================================

        tags = cache.get(
            'all_tags'
        )

        if not tags:

            print(
                'TAGS DB HIT 🔥'
            )

            tags = Tag.objects.all()

            cache.set(

                'all_tags',

                tags,

                timeout=60 * 30

            )

        else:

            print(
                'TAGS CACHE HIT 🚀'
            )

        # =====================================
        # CONTEXT DATA
        # =====================================

        context['categories'] = categories

        context['tags'] = tags

        context['search_query'] = self.request.GET.get(
            'search',
            ''
        )

        context['selected_category'] = self.request.GET.get(
            'category',
            ''
        )

        context['selected_tag'] = self.request.GET.get(
            'tag',
            ''
        )

        context['results_count'] = self.get_queryset().count()

        return context


# =========================================
# BLOG DETAIL VIEW
# =========================================

class BlogDetailView(

    DetailView

):

    model = BlogPost

    template_name = 'blog/blog_detail.html'

    context_object_name = 'post'

    slug_field = 'slug'

    slug_url_kwarg = 'slug'

    # =====================================
    # QUERYSET
    # =====================================

    def get_queryset(self):

        return BlogPost.objects.published(

        ).optimized(

        ).with_average_rating()

    # =====================================
    # UNIQUE VIEW COUNTER
    # =====================================

    def get_object(self, queryset=None):

        obj = super().get_object(
            queryset
        )

        viewed_posts = self.request.session.get(

            'viewed_posts',

            []

        )

        if obj.id not in viewed_posts:

            BlogPost.objects.filter(

                id=obj.id

            ).update(

                views=F('views') + 1

            )

            viewed_posts.append(
                obj.id
            )

            self.request.session[
                'viewed_posts'
            ] = viewed_posts

            print(
                'UNIQUE VIEW COUNTED 🚀'
            )

        else:

            print(
                'DUPLICATE VIEW BLOCKED 🚫'
            )

        obj.refresh_from_db()

        return obj

    # =====================================
    # RECOMMENDED POSTS
    # =====================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        related_posts = BlogPost.objects.recommended(

            self.object

        )[:4]

        # =================================
        # FALLBACK TO TRENDING
        # =================================

        if not related_posts.exists():

            related_posts = BlogPost.objects.trending(

            ).exclude(

                id=self.object.id

            )[:4]

        context['related_posts'] = related_posts

        return context

# =========================================
# CATEGORY POSTS
# =========================================

def category_posts(request, slug):

    category = get_object_or_404(

        Category,

        slug=slug

    )

    posts = BlogPost.objects.published(
    ).optimized(
    ).with_likes_count(
    ).with_comments_count(
    ).filter(

        category=category

    )

    # =====================================
    # SEARCH INSIDE CATEGORY
    # =====================================

    search = request.GET.get(
        'search'
    )

    if search:

        search = search.strip()

        posts = posts.filter(

            title__icontains=search

        )

    # =====================================
    # TAG FILTER
    # =====================================

    tag = request.GET.get(
        'tag'
    )

    if tag:

        posts = posts.by_tag(
            tag
        )

    posts = posts.distinct()

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

        'category': category,

        'posts': page_obj,

        'page_obj': page_obj,

        'tags': Tag.objects.all(),

        'search_query': search,

        'selected_tag': tag,

        'results_count': paginator.count,

    }

    return render(

        request,

        'blog/category_posts.html',

        context

    )


# =========================================
# TAG POSTS
# =========================================

def tag_posts(request, slug):

    tag = get_object_or_404(

        Tag,

        slug=slug

    )

    posts = BlogPost.objects.published(
    ).optimized(
    ).with_likes_count(
    ).with_comments_count(
    ).filter(

        tags=tag

    ).distinct()

    # =====================================
    # SEARCH INSIDE TAG
    # =====================================

    search = request.GET.get(
        'search'
    )

    if search:

        search = search.strip()

        posts = posts.filter(

            title__icontains=search

        )

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

        'tag': tag,

        'posts': page_obj,

        'page_obj': page_obj,

        'search_query': search,

        'results_count': paginator.count,

    }

    return render(

        request,

        'blog/tag_posts.html',

        context

    )


# =========================================
# AJAX BOOKMARK SYSTEM
# =========================================
