from django.contrib import admin, messages
from .models import Quiz, Question, Choice, QuizSubmission, UserAnswer
from django.utils.html import format_html

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('question_text', 'quiz', 'question_type', 'points', 'order')
    list_filter = ('quiz', 'question_type')

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'created_at')

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    # Make points/feedback editable, but other fields read-only
    readonly_fields = ('question', 'selected_choices_display', 'code_answer_display')
    fields = ('question', 'selected_choices_display', 'code_answer_display', 'points_awarded', 'feedback')

    def selected_choices_display(self, obj):
        return ", ".join([choice.choice_text for choice in obj.selected_choices.all()])
    selected_choices_display.short_description = "Selected Choices"

    def code_answer_display(self, obj):
        # Display code in a preformatted block for readability
        return format_html("<pre><code>{}</code></pre>", obj.code_answer) if obj.code_answer else "N/A"
    code_answer_display.short_description = "Code Submission"
    
    def has_change_permission(self, request, obj=None):
        # Allows editing of the fields not in readonly_fields (i.e., points_awarded and feedback)
        return True

    def has_add_permission(self, request, obj=None):
        # Users create answers through the quiz interface, not admins
        return False

    def has_delete_permission(self, request, obj=None):
        # Don't want admins accidentally deleting answer history
        return False

class QuizSubmissionAdmin(admin.ModelAdmin):
    inlines = [UserAnswerInline]
    list_display = ('user', 'quiz', 'status', 'score', 'end_time')
    list_filter = ('status', 'quiz')
    # We make score readonly here because it should only be set via the 'finalize_grades' action
    readonly_fields = ('user', 'quiz', 'start_time', 'end_time', 'score')
    actions = ['finalize_grades']

    def finalize_grades(self, request, queryset):
        """
        Custom admin action to calculate the final score, update the status,
        and save the submission.
        """
        updated_count = 0
        for submission in queryset:
            if submission.status == QuizSubmission.SubmissionStatus.SUBMITTED:
                # The model method now simply calculates and returns the score
                final_score = submission.calculate_final_score()
                submission.score = final_score
                submission.status = QuizSubmission.SubmissionStatus.COMPLETED
                submission.save() # Single save call for all changes
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f"{updated_count} submission(s) have been graded and finalized.", messages.SUCCESS)
        else:
            self.message_user(request, "No submissions were updated. Action can only be run on submissions 'Awaiting Manual Grade'.", messages.WARNING)

    finalize_grades.short_description = "Finalize grades for selected submissions"

# Register your models here
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizSubmission, QuizSubmissionAdmin)

