from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.db.models import Q
from .models import DiscussionThread, DiscussionReply
from .forms import ThreadForm, ReplyForm

def forum_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')
    
    threads = DiscussionThread.objects.select_related('author', 'course').prefetch_related('replies').all()

    if query:
        threads = threads.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query)
        )

    if status_filter == 'unresolved':
        threads = threads.filter(is_resolved=False)
    elif status_filter == 'resolved':
        threads = threads.filter(is_resolved=True)

    context = {
        'threads': threads,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'community/forum_list.html', context)


def thread_detail(request, thread_id):
    thread = get_object_or_404(
        DiscussionThread.objects.select_related('author', 'course').prefetch_related('replies__author', 'replies__upvotes'),
        id=thread_id
    )

    # Increment view count
    thread.views_count += 1
    thread.save(update_fields=['views_count'])

    replies = thread.replies.all()
    form = ReplyForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be signed in to post a reply.")
            return redirect('accounts:login')

        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()
            request.user.award_xp('reply_created', reply.id, 15)
            messages.success(request, "Your reply has been posted! +15 XP")
            return redirect('community:thread_detail', thread_id=thread.id)

    context = {
        'thread': thread,
        'replies': replies,
        'form': form,
    }
    return render(request, 'community/thread_detail.html', context)


@login_required
def create_thread(request):
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            request.user.award_xp('thread_created', thread.id, 25)
            messages.success(request, "Your question has been posted to the global community! +25 XP")
            return redirect('community:thread_detail', thread_id=thread.id)
    else:
        form = ThreadForm()

    return render(request, 'community/create_thread.html', {'form': form})


@login_required
def upvote_reply(request, reply_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    reply = get_object_or_404(DiscussionReply, id=reply_id)
    if request.user in reply.upvotes.all():
        reply.upvotes.remove(request.user)
        messages.info(request, "Upvote removed.")
    else:
        reply.upvotes.add(request.user)
        # Prevent self-upvoting XP and prevent repeated farming
        if reply.author != request.user:
            reply.author.award_xp('reply_upvoted', f"{reply.id}_{request.user.id}", 5)
        messages.success(request, "Upvoted!")

    return redirect('community:thread_detail', thread_id=reply.thread.id)


@login_required
def toggle_solution(request, reply_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    reply = get_object_or_404(DiscussionReply, id=reply_id)
    thread = reply.thread
    if request.user != thread.author and not request.user.is_staff:
        messages.error(request, "Only the author of the question can mark the accepted solution.")
        return redirect('community:thread_detail', thread_id=thread.id)

    reply.is_solution = not reply.is_solution
    reply.save(update_fields=['is_solution'])

    # Update thread status
    has_solution = thread.replies.filter(is_solution=True).exists()
    thread.is_resolved = has_solution
    thread.save(update_fields=['is_resolved'])

    if reply.is_solution:
        # Prevent repeated solution toggle XP farming
        reply.author.award_xp('solution_accepted', thread.id, 40)
        messages.success(request, "Marked as accepted answer! 40 XP awarded to the helper.")
    else:
        messages.info(request, "Solution unmarked.")

    return redirect('community:thread_detail', thread_id=thread.id)
