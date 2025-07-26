from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Quiz
from .forms import CustomUserCreationForm
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from openai import OpenAI
import json

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
                        Create a 3-question multiple choice quiz using the word '{word}'.

                        Format like this exactly:
                        Q: Question text?
                        A) Option 1
                        B) Option 2
                        C) Option 3
                        ANSWER: [Correct Letter]

                        Repeat for 3 questions.
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

    # quiz text
    questions = []
    blocks = quiz.quiz_text.strip().split("Q: ")[1:]
    for i, block in enumerate(blocks):
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
            "questions": questions
        })

    return render(request, "pages/take_quiz.html", {
        "quiz": quiz,
        "questions": questions
    })

# User's quiz history (requires login)
@login_required
def quiz_history(request):
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')

    for quiz in quizzes:
        # Convert JSONField if it's a string (for safety, though probably not needed)
        if isinstance(quiz.user_answers, str):
            try:
                quiz.user_answers = json.loads(quiz.user_answers)
            except json.JSONDecodeError:
                quiz.user_answers = {}

        # Build structured questions list (same as take_quiz_view)
        questions = []
        blocks = quiz.quiz_text.strip().split("Q: ")[1:]
        for i, block in enumerate(blocks):
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

        quiz.parsed_questions = questions  # add custom attribute

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

