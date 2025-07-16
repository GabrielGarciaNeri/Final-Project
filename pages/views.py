from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Quiz
from .forms import CustomUserCreationForm
from openai import OpenAI

# Pages — open to all users
def home_view(request):
    return render(request, "pages/home.html")

def about_view(request):
    return render(request, "pages/about.html")

def contact_view(request):
    return render(request, "pages/contact.html")

# language learning view (requires login)
@login_required
def learn_view(request):
    
    result = ""
    if request.method == "POST":
        word = request.POST.get("word")
        mode = request.POST.get("mode")

        # Prompt based on mode
        if mode == "definition":
            prompt = f"Give me the definition and 1 example sentence using the word '{word}' in simple English."
        elif mode == "quiz":
            prompt = f"Create a simple 3-question multiple choice vocabulary quiz using the word '{word}'. Include correct answers."
        elif mode == "translate":
            prompt = f"Translate the word '{word}' into Spanish, French, and Japanese. Include pronunciation help."

        # Send request to OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a lazy, sarcastic teacher who answers only when you feel like it."},
                {"role": "user", "content": prompt},
            ]
        )

        result = response.choices[0].message.content

        # Save quiz if in quiz mode
        if mode == "quiz":
            Quiz.objects.create(word=word, quiz_text=result, user=request.user)

    return render(request, "pages/learn.html", {"result": result})

# User's quiz history (requires login)
@login_required
def quiz_history(request):
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "pages/quiz_history.html", {"quizzes": quizzes})


# User creation
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'registration/register_success.html')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

