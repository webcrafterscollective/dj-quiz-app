import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.DurationField(help_text="Format: HH:MM:SS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = 'MCQ', _('Multiple Choice')
        MSQ = 'MSQ', _('Multiple Select')
        CODING = 'CODE', _('Coding Challenge')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=4, choices=QuestionType.choices)
    points = models.FloatField(default=1.0)
    order = models.PositiveIntegerField(default=0, help_text="Order in which the question appears")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.question_text[:50]}... ({self.question_type})"

class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.choice_text} for {self.question.id}"

class QuizSubmission(models.Model):
    class SubmissionStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        SUBMITTED = 'SUBMITTED', _('Submitted (Awaiting Manual Grade)')
        COMPLETED = 'COMPLETED', _('Completed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.IN_PROGRESS)

    def __str__(self):
        return f"{self.user.username}'s submission for {self.quiz.title}"

    def calculate_final_score(self):
        """
        Calculates and RETURNS the score for the submission by summing up the points
        awarded for all associated answers. This method does NOT save the object.
        """
        total_points_awarded = 0
        for answer in self.answers.all():
            # Use `is not None` to correctly handle cases where points_awarded is 0.
            if answer.points_awarded is not None:
                total_points_awarded += answer.points_awarded
        return total_points_awarded

class UserAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(QuizSubmission, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(Choice, blank=True)
    code_answer = models.TextField(blank=True)
    points_awarded = models.FloatField(null=True, blank=True, help_text="Points awarded for this specific answer")
    feedback = models.TextField(blank=True, help_text="Feedback for coding questions")

    def __str__(self):
        return f"Answer for Q{self.question.order} in submission {self.submission.id}"

