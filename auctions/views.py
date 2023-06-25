from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

from . import models


def index(request):
    active_auctions = models.Auction.objects.filter(active=True)
    return render(request, "auctions/index.html", {"active_auctions": active_auctions})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = models.User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    

def category_list(request):
    categories = models.Category.objects.all()
    return render(request, "auctions/category_list.html", {"categories": categories})


def add_category(request):
    if request.method == "POST":
        name = request.POST["name"]
        category = models.Category(name=name)
        category.save()
        return HttpResponseRedirect(reverse("category_list"))
    else:
        return render(request, "auctions/add_category.html")


def category_auctions(request, category_id):
    category = models.Category.objects.get(id=category_id)
    active_auctions = models.Auction.objects.filter(category=category, active=True)
    return render(request, "auctions/category_auctions.html", {"category": category, "active_auctions": active_auctions})


def create_auction(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        start_price = request.POST["start_price"]
        image_url = request.POST["image_url"]
        category_id = request.POST["category"]
        
        category = models.Category.objects.get(id=category_id)
        
        auction = models.Auction(
            title=title,
            description=description,
            start_price=start_price,
            current_price=start_price,
            created_by=request.user,
            image_url=image_url,
            category=category
        )
        auction.save()
        
        return HttpResponseRedirect(reverse("index"))
    else:
        categories = models.Category.objects.all()
        return render(request, "auctions/create_auction.html", {"categories": categories})
    

def auction_details(request, auction_id):
    auction = models.Auction.objects.get(id=auction_id)
    comments = models.Comment.objects.filter(auction=auction).order_by('created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        comment_text = request.POST['comment_text']
        comment = models.Comment(auction=auction, commenter=request.user, text=comment_text)
        comment.save()
        return redirect('auction_details', auction_id=auction_id)

    return render(request, "auctions/auction_details.html", {"auction": auction, "comments": comments})


def user_bids(request):
    user = request.user
    auctions = models.Auction.objects.filter(bid__bidder=user).distinct()
    return render(request, "auctions/user_bids.html", {"auctions": auctions})


def add_to_watchlist(request, auction_id):
    user = request.user
    auction = models.Auction.objects.get(id=auction_id)
    user.watchlist.add(auction)
    return redirect('auction_details', auction_id=auction_id)


def remove_from_watchlist(request, auction_id):
    user = request.user
    auction = models.Auction.objects.get(id=auction_id)
    user.watchlist.remove(auction)
    return redirect('auction_details', auction_id=auction_id)


def watchlist(request):
    user = request.user
    watchlist = user.watchlist.all()
    return render(request, "auctions/watchlist.html", {"watchlist": watchlist})


def place_bid(request, auction_id):
    if request.method == "POST":
        bid_amount = request.POST["bid_amount"]
        try:
            bid_amount = float(bid_amount)
        except ValueError:
            messages.error(request, "Invalid bid amount.")
            return redirect('auction_details', auction_id=auction_id)

        auction = models.Auction.objects.get(id=auction_id)
        if not auction.active:
            messages.error(request, "This auction is no longer active.")
            return redirect('auction_details', auction_id=auction_id)

        if bid_amount <= auction.current_price:
            messages.error(request, "Bid amount should be greater than the current price.")
            return redirect('auction_details', auction_id=auction_id)

        highest_bid = models.Bid.objects.filter(auction=auction).order_by('-amount').first()
        if highest_bid and bid_amount <= highest_bid.amount:
            messages.error(request, "Bid amount should be higher than any other existing bids.")
            return redirect('auction_details', auction_id=auction_id)

        auction.current_price = bid_amount
        auction.save()

        bid = models.Bid(auction=auction, bidder=request.user, amount=bid_amount)
        bid.save()

        messages.success(request, "Your bid has been placed successfully.")
        return redirect('auction_details', auction_id=auction_id)

    else:
        return redirect('auction_details', auction_id=auction_id)
    

def close_auction(request, auction_id):
    auction = models.Auction.objects.get(id=auction_id)
    if auction.created_by == request.user:
        auction.active = False
        highest_bid = models.Bid.objects.filter(auction=auction).order_by('-amount').first()
        if highest_bid:
            auction.winner = highest_bid.bidder
            auction.save()
            messages.success(request, "Auction closed. The winner has been notified.")
        else:
            messages.error(request, "No bids were placed for this auction.")
    return redirect('auction_details', auction_id=auction_id)
