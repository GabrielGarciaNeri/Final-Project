from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Quiz
from .forms import CustomUserCreationForm
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactForm
from openai import OpenAI
import json
import re

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
            prompt = f"""
                        In the voice of a lazy, sarcastic teacher who doesn't really want to make this quiz, create a 3-question multiple choice quiz using the word '{word}'.

                        Add a sarcastic comment at the start and a closing remark after the last question.

                        Format like this exactly:
                        [Intro message]

                        Q: Question text?
                        A) Option 1
                        B) Option 2
                        C) Option 3
                        ANSWER: [Correct Letter]

                        Repeat for 3 questions, then add a final sarcastic message at the end.
                    """
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
            quiz = Quiz.objects.create(word=word, quiz_text=result, user=request.user)

            return redirect("take_quiz", quiz_id=quiz.id)

    return render(request, "pages/learn.html", {"result": result})

@login_required
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)

    # Extract intro and outro
    lines = quiz.quiz_text.strip().split("\n")
    q_indexes = [i for i, l in enumerate(lines) if re.match(r"Q\d?:", l.strip())]
    answer_indexes = [i for i, l in enumerate(lines) if l.startswith("ANSWER:")]

    intro = "\n".join(lines[:q_indexes[0]]).strip() if q_indexes else ""
    outro = "\n".join(lines[answer_indexes[-1] + 1:]).strip() if answer_indexes and answer_indexes[-1] + 1 < len(lines) else ""

    # Parse questions
    raw_questions = re.split(r"\nQ\d?: ", quiz.quiz_text.strip())[1:]
    questions = []
    for i, block in enumerate(raw_questions):
        lines = block.strip().split("\n")
        question = lines[0]
        options = [line for line in lines if line.startswith(("A)", "B)", "C)", "D)"))]
        answer = next((line[-1] for line in lines if line.startswith("ANSWER:")), None)
        questions.append({
            'id': i,
            'question': question,
            'options': options,
            'answer': answer,
        })

    # Grading
    if request.method == "POST":
        score = 0
        user_answers = {}

        for q in questions:
            selected = request.POST.get(f"q{q['id']}")
            user_answers[str(q['id'])] = selected  # save user answer
            if selected == q['answer']:
                score += 1
        quiz.score = score
        quiz.user_answers = user_answers
        quiz.save()

        return render(request, "pages/quiz_result.html", {
            "quiz": quiz,
            "score": score,
            "total": len(questions),
            "questions": questions,
            "intro": intro,
            "outro": outro,
        })

    return render(request, "pages/take_quiz.html", {
        "quiz": quiz,
        "questions": questions,
        "intro": intro,
        "outro": outro,
    })

# User's quiz history (requires login)
@login_required
def quiz_history(request):
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')

    for quiz in quizzes:
        # Handle JSON field
        if isinstance(quiz.user_answers, str):
            try:
                quiz.user_answers = json.loads(quiz.user_answers)
            except json.JSONDecodeError:
                quiz.user_answers = {}

        # Extract intro/outro
        lines = quiz.quiz_text.strip().split("\n")
        q_indexes = [i for i, l in enumerate(lines) if re.match(r"Q\d?:", l.strip())]
        answer_indexes = [i for i, l in enumerate(lines) if l.startswith("ANSWER:")]

        quiz.intro = "\n".join(lines[:q_indexes[0]]).strip() if q_indexes else ""
        quiz.outro = "\n".join(lines[answer_indexes[-1] + 1:]).strip() if answer_indexes and answer_indexes[-1] + 1 < len(lines) else ""

        # Parse questions for display
        raw_questions = re.split(r"\nQ\d?: ", quiz.quiz_text.strip())[1:]
        parsed_questions = []
        for i, block in enumerate(raw_questions):
            lines = block.strip().split("\n")
            question = lines[0]
            options = [line for line in lines if line.startswith(("A)", "B)", "C)", "D)"))]
            answer = next((line[-1] for line in lines if line.startswith("ANSWER:")), None)
            parsed_questions.append({
                'id': i,
                'question': question,
                'options': options,
                'answer': answer,
            })

        quiz.parsed_questions = parsed_questions

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

def contact_view(request):
    form = ContactForm()

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            full_message = f"Message from {name} <{email}>:\n\n{message}"

            send_mail(
                subject="New Contact Form Submission",
                message=full_message,
                from_email=email,  # Can use your site default
                recipient_list=['19gjr98@gmail.com'],  # Change this
            )

            messages.success(request, "Your message was sent successfully!")
            form = ContactForm()  # reset form

    return render(request, 'pages/contact.html', {'form': form})