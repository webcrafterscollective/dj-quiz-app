from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from .models import Quiz, Question, Choice, QuizSubmission, UserAnswer

@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all()
    return render(request, 'quiz/quiz_list.html', {'quizzes': quizzes})

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    return render(request, 'quiz/quiz_detail.html', {'quiz': quiz})

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        submission = QuizSubmission.objects.create(
            user=request.user,
            quiz=quiz
        )

        for question in questions:
            user_answer = UserAnswer(question=question, submission=submission)
            
            if question.question_type == 'MCQ':
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    selected_choice = get_object_or_404(Choice, pk=choice_id)
                    user_answer.save() 
                    user_answer.selected_choices.add(selected_choice)
            
            elif question.question_type == 'MSQ':
                choice_ids = request.POST.getlist(f'question_{question.id}')
                user_answer.save()
                if choice_ids:
                    for choice_id in choice_ids:
                        selected_choice = get_object_or_404(Choice, pk=choice_id)
                        user_answer.selected_choices.add(selected_choice)

            elif question.question_type == 'CODE':
                code = request.POST.get(f'question_{question.id}')
                user_answer.code_answer = code
                user_answer.save()
        
        submission.grade_mcq_msq()
        return redirect('quiz:submission_result', submission_id=submission.id)

    return render(request, 'quiz/take_quiz.html', {'quiz': quiz, 'questions': questions})

@login_required
def submission_result(request, submission_id):
    submission = get_object_or_404(QuizSubmission, pk=submission_id, user=request.user)
    return render(request, 'quiz/submission_result.html', {'submission': submission})

@login_required
def submission_history(request):
    submissions = QuizSubmission.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'quiz/submission_history.html', {'submissions': submissions})


@login_required
def submission_detail(request, submission_id):
    submission = get_object_or_404(
        QuizSubmission.objects.select_related('quiz'), 
        pk=submission_id, 
        user=request.user
    )
    quiz = submission.quiz
    
    total_points = quiz.questions.aggregate(total=Sum('points'))['total'] or 0

    questions = quiz.questions.all().prefetch_related('choices')
    user_answers = submission.answers.all().prefetch_related('selected_choices')
    user_answers_map = {ua.question_id: ua for ua in user_answers}

    questions_data = []
    for q in questions:
        user_answer = user_answers_map.get(q.id)
        selected_choice_ids = set()
        if user_answer:
            selected_choice_ids = set(user_answer.selected_choices.values_list('id', flat=True))

        choices_data = []
        for c in q.choices.all():
            choices_data.append({
                'id': c.id,
                'text': c.choice_text, 
                'is_correct': c.is_correct,
            })
        
        questions_data.append({
            # FIX: Changed q.text to q.question_text to match your model
            'text': q.question_text,
            'points': q.points,
            'question_type': q.question_type,
            'user_answer': user_answer,
            'selected_choice_ids': selected_choice_ids,
            'choices': choices_data,
        })

    context = {
        'submission': submission,
        'questions_with_answers': questions_data,
        'total_points': total_points,
    }
    return render(request, 'quiz/submission_detail.html', context)

