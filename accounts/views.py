from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django.contrib.sites.shortcuts import get_current_site
from blog.tasks import send_welcome_email
from django.conf import settings

from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode
)

from django.utils.encoding import (
    force_bytes,
    force_str
)

from .forms import (
    CustomUserCreationForm,
    UserUpdateForm
)

from .models import CustomUser

from .tokens import account_activation_token



# =========================================
# SIGNUP VIEW
# =========================================

def signup_view(request):

    if request.method == 'POST':

        form = CustomUserCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save(
                commit=False
            )

            # =================================
            # USER INACTIVE UNTIL VERIFICATION
            # =================================

            user.is_active = False

            user.save()

            # =================================
            # CURRENT DOMAIN
            # =================================

            current_site = get_current_site(request)


            domain = current_site.domain

            # =================================
            # EMAIL SUBJECT
            # =================================

            mail_subject = (
                'Activate your account'
            )

            # =================================
            # RENDER EMAIL TEMPLATE
            # =================================

            message = render_to_string(

    'accounts/verify_email.html',

    {

        'user': user,

        'domain': domain,

        'uid': urlsafe_base64_encode(

            force_bytes(user.pk)

        ),

        'token': account_activation_token.make_token(
            user
        ),

    }

)

            # =================================
            # SEND ACTIVATION EMAIL
            # =================================

            email = EmailMessage(

                mail_subject,

                message,

                to=[user.email]

            )

            email.content_subtype = 'html'

            email.send()

            print("DOMAIN =", domain)

            return render(
    request,
    'accounts/email_sent.html'
)
    else:

        form = CustomUserCreationForm()

    return render(

        request,

        'accounts/signup.html',

        {

            'form': form

        }

    )


# =========================================
# ACCOUNT ACTIVATION
# =========================================

def activate(request, uidb64, token):

    try:

        uid = force_str(

            urlsafe_base64_decode(
                uidb64
            )

        )

        user = CustomUser.objects.get(
            pk=uid
        )

    except Exception:

        user = None

    # =====================================
    # VALID TOKEN
    # =====================================

    if (

        user is not None

        and

        account_activation_token.check_token(
            user,
            token
        )

    ):

        # =================================
        # ACTIVATE USER
        # =================================

        user.is_active = True

        user.email_verified = True

        user.save()

        # =================================
        # SEND WELCOME EMAIL WITH CELERY
        # =================================

        send_welcome_email.delay(

            user.username,

            user.email

        )

        return render(
    request,
    'accounts/activation_success.html'
)

    # =====================================
    # INVALID TOKEN
    # =====================================

    else:

        return render(
    request,
    'accounts/activation_failed.html'
)

@login_required
def dashboard(request):

    return render(
        request,
        'accounts/dashboard.html'
    )


@login_required
def profile_view(request):

    if request.method == 'POST':

        form = UserUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            return redirect('profile')

    else:

        form = UserUpdateForm(
            instance=request.user
        )

    return render(
        request,
        'accounts/profile.html',
        {'form': form}
    )