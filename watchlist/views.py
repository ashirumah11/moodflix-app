import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from .models import Watchlist

def _is_ajax(request):
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.content_type == 'application/json'
    )


@login_required
def watchlist_index_view(request):
    """
    Displays the user's saved movies and TV shows, with filters for
    watched/unwatched status and media type.
    """
    filter_status = request.GET.get('status', 'all')
    filter_media = request.GET.get('type', 'all')
    sort_by = request.GET.get('sort', 'recent')

    qs = Watchlist.objects.filter(user=request.user)

    total_count = qs.count()
    watched_count = qs.filter(watched=True).count()
    unwatched_count = total_count - watched_count

    if filter_status == 'watched':
        qs = qs.filter(watched=True)
    elif filter_status == 'unwatched':
        qs = qs.filter(watched=False)

    if filter_media in ('movie', 'tv'):
        qs = qs.filter(media_type=filter_media)

    if sort_by == 'title':
        qs = qs.order_by('title')
    elif sort_by == 'rating':
        qs = qs.order_by('-vote_average')
    else:
        qs = qs.order_by('-added_at')

    context = {
        'items': qs,
        'total_count': total_count,
        'watched_count': watched_count,
        'unwatched_count': unwatched_count,
        'current_status': filter_status,
        'current_media': filter_media,
        'current_sort': sort_by,
    }
    return render(request, 'watchlist/index.html', context)


@login_required
@require_POST
def watchlist_toggle_view(request):
    """
    Toggles an item in/out of the user's watchlist.
    Works seamlessly with both standard HTML form POST and AJAX/Fetch.
    """
    # Parse payload from form or JSON
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
    else:
        data = request.POST

    tmdb_id = data.get('tmdb_id')
    media_type = data.get('media_type', 'movie')
    title = data.get('title', 'Untitled')
    poster_path = data.get('poster_path')
    backdrop_path = data.get('backdrop_path')
    vote_average = data.get('vote_average', 0.0)
    release_date = data.get('release_date', '')

    if not tmdb_id:
        if _is_ajax(request):
            return JsonResponse({'status': 'error', 'message': 'Missing tmdb_id'}, status=400)
        messages.error(request, "Unable to save item: Missing movie identifier.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    try:
        tmdb_id_int = int(tmdb_id)
        vote_avg_float = float(vote_average) if vote_average else 0.0
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Invalid numeric format")

    existing = Watchlist.objects.filter(
        user=request.user,
        tmdb_id=tmdb_id_int,
        media_type=media_type
    ).first()

    if existing:
        existing.delete()
        in_watchlist = False
        msg = f"'{title}' removed from your watchlist."
    else:
        Watchlist.objects.create(
            user=request.user,
            tmdb_id=tmdb_id_int,
            media_type=media_type,
            title=title,
            poster_path=poster_path or '',
            backdrop_path=backdrop_path or '',
            vote_average=vote_avg_float,
            release_date=release_date or '',
        )
        in_watchlist = True
        msg = f"'{title}' added to your watchlist!"

    current_count = Watchlist.objects.filter(user=request.user).count()

    if _is_ajax(request):
        return JsonResponse({
            'status': 'success',
            'in_watchlist': in_watchlist,
            'watchlist_count': current_count,
            'message': msg
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'watchlist:index'))


@login_required
@require_POST
def watchlist_toggle_watched_view(request, item_id):
    """
    Toggles watched state for a watchlist item owned by request.user.
    """
    item = get_object_or_404(Watchlist, id=item_id, user=request.user)
    item.watched = not item.watched
    item.save()

    status_str = "marked as watched" if item.watched else "marked as unwatched"
    msg = f"'{item.title}' {status_str}."

    if _is_ajax(request):
        return JsonResponse({
            'status': 'success',
            'watched': item.watched,
            'message': msg
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'watchlist:index'))


@login_required
@require_POST
def watchlist_remove_view(request, item_id):
    """
    Deletes an item from the watchlist. Strictly verified by user ownership.
    """
    item = get_object_or_404(Watchlist, id=item_id, user=request.user)
    title = item.title
    item.delete()

    current_count = Watchlist.objects.filter(user=request.user).count()
    msg = f"'{title}' removed from your watchlist."

    if _is_ajax(request):
        return JsonResponse({
            'status': 'success',
            'in_watchlist': False,
            'watchlist_count': current_count,
            'message': msg
        })

    messages.info(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'watchlist:index'))
