"""Staff page: user management."""
from django.shortcuts import (

    render,
    redirect

)



from django.contrib.auth.decorators import (
    login_required
)




from accounts.models import CustomUser

from django.contrib.admin.views.decorators import staff_member_required







@staff_member_required
@login_required
def manage_users(request):

    # ADMIN ONLY

    if not request.user.is_superuser:

        return redirect(
            'dashboard'
        )

    users = CustomUser.objects.all().order_by(
        '-date_joined'
    )

    context = {

        'users': users,

    }

    return render(

        request,

        'blog/manage_users.html',

        context

    )
