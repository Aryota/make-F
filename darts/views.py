from django.shortcuts import render
from django.http.response import HttpResponse

# Create your views here.
def index(request):
    return render(request,'darts/darts.html')

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.views import generic
from .forms import LoginForm

# 会員登録
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import get_template
from django.views import generic
from .forms import (
    LoginForm, UserCreateForm
)


User = get_user_model()
class Top(generic.TemplateView):
    template_name = 'darts/top.html'


class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'darts/login.html'


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = 'darts/top.html'

# ユーザー登録
# def Registration(request):
#     """登録ページ"""
#     return render(request,'darts/registration.html')
def Service(request):
    """サービス案内"""
    return render(request,'darts/service.html')

class UserCreate(generic.CreateView):
    """ユーザー仮登録"""
    template_name = 'darts/user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性を使うと簡単です。
        # 退会処理も、is_activeをFalseにするだけにしておくと捗ります。
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject_template = get_template('darts/mail_template/create/subject.txt')
        subject = subject_template.render(context)

        message_template = get_template('darts/mail_template/create/message.txt')
        message = message_template.render(context)

        user.email_user(subject, message)
        return redirect('darts:user_create_done')


class UserCreateDone(generic.TemplateView):
    """ユーザー仮登録したよ"""
    template_name = 'darts/user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'darts/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()
