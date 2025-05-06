from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from banking import views as banking_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', banking_views.home, name='home'),
    path('register/', banking_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='banking/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='banking/logout.html'), name='logout'),
    path('profile/', banking_views.profile, name='profile'),
    # Add this line to urlpatterns
    path('accounts/', include('allauth.urls')),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='banking/password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='banking/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='banking/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='banking/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    # Banking functionality URLs
    path('dashboard/', banking_views.dashboard, name='dashboard'),
    path('account/<str:account_number>/', banking_views.account_detail, name='account_detail'),
    path('transactions/', banking_views.transaction_history, name='transaction_history'),
    path('transfer/', banking_views.transfer, name='transfer'),
    path('create-account/', banking_views.create_account, name='create_account'),
    # Add this to your existing urlpatterns
    path('admin-topup/', banking_views.admin_topup, name='admin_topup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
