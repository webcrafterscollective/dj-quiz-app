import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from quiz.models import Quiz, Question, Choice

class Command(BaseCommand):
    help = 'Loads quizzes, questions, and choices from a structured JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file to load.')

    @transaction.atomic
    def handle(self, *args, **options):
        json_file_path = options['json_file']

        self.stdout.write(self.style.SUCCESS(f'Loading quizzes from "{json_file_path}"...'))

        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found at path: {json_file_path}')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in file: {json_file_path}')

        quizzes_data = data.get('quizzes')
        if not quizzes_data:
            raise CommandError('JSON file must have a top-level "quizzes" key containing a list of quizzes.')

        quiz_count = 0
        question_count = 0
        choice_count = 0

        for quiz_data in quizzes_data:
            quiz, created = Quiz.objects.update_or_create(
                title=quiz_data['title'],
                defaults={'time_limit_minutes': quiz_data['time_limit_minutes']}
            )
            if created:
                quiz_count += 1
                self.stdout.write(f'  Created quiz: "{quiz.title}"')
            else:
                self.stdout.write(f'  Updated quiz: "{quiz.title}"')

            for question_data in quiz_data.get('questions', []):
                question, created = Question.objects.update_or_create(
                    quiz=quiz,
                    question_text=question_data['question_text'],
                    defaults={
                        'question_type': question_data['question_type'],
                        'points': question_data.get('points', 0)
                    }
                )
                if created:
                    question_count += 1

                # Clear existing choices for this question to prevent duplicates on update
                question.choices.all().delete()
                
                for choice_data in question_data.get('choices', []):
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_data['choice_text'],
                        is_correct=choice_data.get('is_correct', False)
                    )
                    choice_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully loaded {quiz_count} new quizzes, {question_count} new questions, and {choice_count} choices.'
        ))
