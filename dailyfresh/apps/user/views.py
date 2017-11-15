from django.shortcuts import render, redirect
from apps.user import models
from django.views.generic import View
from django.core.urlresolvers import reverse
import re
from django.conf import settings
from django.contrib.auth import authenticate,login
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
from django.core.mail import send_mail
from celery_task.tasks import send_active_mail
from django.http import HttpResponse
from apps.user.models import User

# Create your views here.


class RegisterView(View):
    def get(self,request):
        return render(request,'user/register.html')
    def post(self,request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱不合法'})

        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})
        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            # 用户不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'user/register.html', {'errmsg':'用户名已存在'})

        # 进行业务处理：完成用户的注册
        user = models.User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        serializer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info).decode()
        send_active_mail(email,username,token)
        print('already token')
        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''用户激活'''
        # 解密获取用户的身份信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取激活用户的id
            user_id = info['confirm']

            # 根据user_id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已失效
            return HttpResponse('激活链接已失效')


class LoginView(View):
    def get(self,request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        # 使用模板
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        if not all([username, password]):
            # 数据不完整
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        user = authenticate(username=username,password=password)
        if user:
            if user.is_active:
                login(request,user)
                response = redirect(reverse('goods:index'))

                # 是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '请验证邮箱'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码输入错误'})