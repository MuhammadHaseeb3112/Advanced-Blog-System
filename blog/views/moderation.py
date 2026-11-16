"""Staff pages: categories, tags and comments."""
from django.shortcuts import (

    render,
    redirect,
    get_object_or_404

)



from django.contrib.auth.decorators import (
    login_required
)


from django.core.paginator import (
    Paginator
)

from blog.models import (

    Comment,
    Category,
    Tag,


)


from django.contrib.admin.views.decorators import staff_member_required

from django.contrib import messages

from django.db.models import Q



from ._common import clear_blog_cache


@staff_member_required
@login_required
def manage_categories(request):

    if not request.user.is_superuser:

        return redirect(
            'dashboard'
        )

    # =====================================
    # EDIT CATEGORY
    # =====================================

    edit_id = request.GET.get(
        'edit'
    )

    edit_category = None

    if edit_id:

        edit_category = get_object_or_404(

            Category,

            id=edit_id

        )

    # =====================================
    # POST ACTIONS
    # =====================================

    if request.method == 'POST':

        # DELETE CATEGORY

        delete_id = request.POST.get(
            'delete_category_id'
        )

        if delete_id:

            category = get_object_or_404(

                Category,

                id=delete_id

            )

            category.delete()

            clear_blog_cache()



            messages.success(

                request,

                'Category deleted successfully.'

            )

            return redirect(
                'manage_categories'
            )

        # CREATE / UPDATE CATEGORY

        category_id = request.POST.get(
            'category_id'
        )

        name = request.POST.get(
            'name'
        )

        if category_id:

            category = get_object_or_404(

                Category,

                id=category_id

            )

            category.name = name

            category.save()

            clear_blog_cache()

            messages.success(

                request,

                'Category updated successfully.'

            )

        else:

            Category.objects.create(
                name=name
            )

            clear_blog_cache()

            messages.success(

                request,

                'Category created successfully.'

            )

        return redirect(
            'manage_categories'
        )

    # =====================================
    # SEARCH
    # =====================================

    search = request.GET.get(
        'search'
    )

    categories = Category.objects.all()

    if search:

        categories = categories.filter(

            name__icontains=search

        )

    context = {

        'categories': categories,

        'edit_category': edit_category,

        'search_query': search,

    }

    return render(

        request,

        'blog/manage_categories.html',

        context

    )


# =========================================
# MANAGE TAGS
# =========================================


@staff_member_required
@login_required
def manage_tags(request):

    if not request.user.is_superuser:

        return redirect(
            'dashboard'
        )

    # =====================================
    # EDIT TAG
    # =====================================

    edit_id = request.GET.get(
        'edit'
    )

    edit_tag = None

    if edit_id:

        edit_tag = get_object_or_404(

            Tag,

            id=edit_id

        )

    # =====================================
    # POST ACTIONS
    # =====================================

    if request.method == 'POST':

        # DELETE TAG

        delete_id = request.POST.get(
            'delete_tag_id'
        )

        if delete_id:

            tag = get_object_or_404(

                Tag,

                id=delete_id

            )

            tag.delete()

            clear_blog_cache()

            messages.success(

                request,

                'Tag deleted successfully.'

            )

            return redirect(
                'manage_tags'
            )

        # CREATE / UPDATE TAG

        tag_id = request.POST.get(
            'tag_id'
        )

        name = request.POST.get(
            'name'
        )

        if tag_id:

            tag = get_object_or_404(

                Tag,

                id=tag_id

            )

            tag.name = name

            tag.save()

            messages.success(

                request,

                'Tag updated successfully.'

            )

        else:

            Tag.objects.create(
                name=name
            )

            messages.success(

                request,

                'Tag created successfully.'

            )

        return redirect(
            'manage_tags'
        )

    # =====================================
    # SEARCH
    # =====================================

    search = request.GET.get(
        'search'
    )

    tags = Tag.objects.all()

    if search:

        tags = tags.filter(

            name__icontains=search

        )

    context = {

        'tags': tags,

        'edit_tag': edit_tag,

        'search_query': search,

    }

    return render(

        request,

        'blog/manage_tags.html',

        context

    )


# =========================================
# MANAGE COMMENTS
# =========================================


@staff_member_required
@login_required
def manage_comments(request):

    if not request.user.is_superuser:

        return redirect(
            'dashboard'
        )

    # =====================================
    # EDIT COMMENT
    # =====================================

    edit_id = request.GET.get(
        'edit'
    )

    edit_comment = None

    if edit_id:

        edit_comment = get_object_or_404(

            Comment,

            id=edit_id

        )

    # =====================================
    # HANDLE POST ACTIONS
    # =====================================

    if request.method == 'POST':

        # DELETE COMMENT

        delete_comment_id = request.POST.get(
            'delete_comment_id'
        )

        if delete_comment_id:

            comment = get_object_or_404(

                Comment,

                id=delete_comment_id

            )

            comment.delete()

            clear_blog_cache()

            messages.success(

                request,

                'Comment deleted successfully.'

            )

            return redirect(
                'manage_comments'
            )

        # UPDATE COMMENT

        comment_id = request.POST.get(
            'comment_id'
        )

        if comment_id:

            content = request.POST.get(
                'content'
            )

            rating = request.POST.get(
                'rating'
            )

            comment = get_object_or_404(

                Comment,

                id=comment_id

            )

            comment.content = content

            comment.rating = rating

            comment.save()

            clear_blog_cache()

            messages.success(

                request,

                'Comment updated successfully.'

            )

            return redirect(
                'manage_comments'
            )

    # =====================================
    # SEARCH
    # =====================================

    search = request.GET.get(
        'search'
    )

    comments = Comment.objects.select_related(

        'author',
        'post'

    ).all().order_by(
        '-created_at'
    )

    if search:

        comments = comments.filter(

            Q(content__icontains=search) |

            Q(author__username__icontains=search) |

            Q(post__title__icontains=search)

        )

    # =====================================
    # PAGINATION
    # =====================================

    paginator = Paginator(

        comments,
        10

    )

    page_number = request.GET.get(
        'page'
    )

    page_obj = paginator.get_page(
        page_number
    )

    context = {

        'comments': page_obj,

        'page_obj': page_obj,

        'edit_comment': edit_comment,

        'search_query': search,

        'results_count': paginator.count,

    }

    return render(

        request,

        'blog/manage_comments.html',

        context

    )
# =========================================
# NOTIFICATIONS
# =========================================
