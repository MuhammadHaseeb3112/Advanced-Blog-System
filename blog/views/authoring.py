"""Create, update and delete posts (authors and admins)."""
from django.shortcuts import (

    render,
    redirect,
    get_object_or_404

)



from django.contrib.auth.decorators import (
    login_required
)



from blog.models import (

    BlogPost,
    Category,
    Tag,


)



from django.contrib import messages



from django.utils import timezone

from ._common import author_required, clear_blog_cache


@login_required
@author_required
def create_post(request):

    categories = Category.objects.all()

    tags = Tag.objects.all()

    if request.method == 'POST':

        title = request.POST.get(
            'title'
        )

        short_description = request.POST.get(
            'short_description'
        )

        content = request.POST.get(
            'content'
        )

        featured_image = request.FILES.get(
            'featured_image'
        )

        category_id = request.POST.get(
            'category'
        )

        selected_tags = request.POST.getlist(
            'tags'
        )

        status = request.POST.get(
            'status'
        )

        publish_at = request.POST.get(
            'publish_at'
        )

        # =================================
        # VALIDATION
        # =================================

        if not title or not content:

            messages.error(

                request,

                'Title and content are required.'

            )

            return redirect(
                'create_post'
            )

        # =================================
        # AUTO PUBLISH TIME
        # =================================

        if status == 'published' and not publish_at:

            publish_at = timezone.now()

        # =================================
        # CATEGORY
        # =================================

        category = None

        if category_id:

            category = get_object_or_404(

                Category,

                id=category_id

            )

        # =================================
        # CREATE POST
        # =================================

        post = BlogPost.objects.create(

            title=title,

            short_description=short_description,

            content=content,

            featured_image=featured_image,

            category=category,

            author=request.user,

            status=status,

            publish_at=publish_at

        )

        # =================================
        # TAGS
        # =================================

        if selected_tags:

            post.tags.set(
                selected_tags
            )

        
        clear_blog_cache()


        # =================================
        # SUCCESS MESSAGE
        # =================================

        messages.success(

            request,

            'Post created successfully.'

        )

        return redirect(
            'my_posts'
        )

    context = {

        'categories': categories,

        'tags': tags,

    }

    return render(

        request,

        'blog/create_post.html',

        context

    )


# =========================================
# UPDATE POST
# =========================================

@login_required
@author_required
def update_post(request, slug):

    post = get_object_or_404(

        BlogPost.objects.optimized(),

        slug=slug

    )

    # =====================================
    # PERMISSION
    # =====================================

    if request.user != post.author and not request.user.is_superuser:

        messages.error(

            request,

            'You do not have permission.'

        )

        return redirect(
            'dashboard'
        )

    categories = Category.objects.all()

    tags = Tag.objects.all()

    if request.method == 'POST':

        title = request.POST.get(
            'title'
        )

        short_description = request.POST.get(
            'short_description'
        )

        content = request.POST.get(
            'content'
        )

        status = request.POST.get(
            'status'
        )

        publish_at = request.POST.get(
            'publish_at'
        )

        # =================================
        # VALIDATION
        # =================================

        if not title or not content:

            messages.error(

                request,

                'Title and content are required.'

            )

            return redirect(
                'update_post',
                slug=post.slug
            )

        # =================================
        # AUTO PUBLISH TIME
        # =================================

        if status == 'published' and not publish_at:

            publish_at = timezone.now()

        # =================================
        # UPDATE FIELDS
        # =================================

        post.title = title

        post.short_description = short_description

        post.content = content

        post.status = status

        post.publish_at = publish_at

        # =================================
        # CATEGORY
        # =================================

        category_id = request.POST.get(
            'category'
        )

        if category_id:

            post.category = get_object_or_404(

                Category,

                id=category_id

            )

        else:

            post.category = None

        # =================================
        # FEATURED IMAGE
        # =================================

        featured_image = request.FILES.get(
            'featured_image'
        )

        if featured_image:

            post.featured_image = featured_image

        # =================================
        # SAVE POST
        # =================================

        post.save()

        # =================================
        # TAGS
        # =================================

        selected_tags = request.POST.getlist(
            'tags'
        )

        post.tags.set(
            selected_tags
        )

        clear_blog_cache()


        # =================================
        # SUCCESS MESSAGE
        # =================================

        messages.success(

            request,

            'Post updated successfully.'

        )

        return redirect(
            'my_posts'
        )

    context = {

        'post': post,

        'categories': categories,

        'tags': tags,

    }

    return render(

        request,

        'blog/update_post.html',

        context

    )


# =========================================
# DELETE POST
# =========================================

@login_required
@author_required
def delete_post(request, slug):

    post = get_object_or_404(

        BlogPost.objects.optimized(),

        slug=slug

    )

    # =====================================
    # PERMISSION
    # =====================================

    if request.user != post.author and not request.user.is_superuser:

        return redirect(
            'dashboard'
        )

    if request.method == 'POST':

        post.delete()


        clear_blog_cache()


        messages.success(

            request,

            'Post deleted successfully.'

        )

        return redirect(
            'my_posts'
        )

    context = {

        'post': post

    }

    return render(

        request,

        'blog/delete_post.html',

        context

    )


# =========================================
# MANAGE CATEGORIES
# =========================================
