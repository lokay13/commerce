from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("categories", views.category_list, name="category_list"),
    path("categories/add", views.add_category, name="add_category"),
    path("categories/<int:category_id>", views.category_auctions, name="category_auctions"),
    path("create_auction", views.create_auction, name="create_auction"),
    path("auctions/<int:auction_id>", views.auction_details, name="auction_details"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("auctions/<int:auction_id>/add_to_watchlist", views.add_to_watchlist, name="add_to_watchlist"),
    path("auctions/<int:auction_id>/remove_from_watchlist", views.remove_from_watchlist, name="remove_from_watchlist"),
    path('auctions/<int:auction_id>/place_bid/', views.place_bid, name='place_bid'),
    path('auctions/<int:auction_id>/close/', views.close_auction, name='close_auction'),
    path("user_bids/", views.user_bids, name="user_bids")
]
