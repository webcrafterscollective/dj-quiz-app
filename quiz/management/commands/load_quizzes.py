import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from quiz.models import Quiz, Question, Choice

class Command(BaseCommand):
    """
    A Django management command to load quiz data from a JSON file into the database.

    This command clears existing quiz data to prevent duplicates and ensures a clean import.
    It reads a specified JSON file, processes each quiz, its questions, and their choices,
    and populates the database accordingly. It handles the conversion of a time limit in
    minutes from the JSON file to a DurationField in the Quiz model.

    Usage:
        python manage.py load_quizzes <path_to_your_json_file>
    """
    help = 'Loads quizzes from a specified JSON file into the database.'

    def add_arguments(self, parser):
        """
        Adds the required positional argument for the JSON file path.
        """
        parser.add_argument('json_file', type=str, help='The path to the JSON file to load quizzes from.')

    @transaction.atomic
    def handle(self, *args, **options):
        """
        The main logic for the command. It orchestrates the reading of the JSON file
        and the creation of quiz objects in the database.
        """
        json_file_path = options['json_file']
        self.stdout.write(self.style.SUCCESS(f'Attempting to load quizzes from {json_file_path}...'))

        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Error: The file at {json_file_path} was not found.'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Error: The JSON file is malformed.'))
            return

        # Determine the list of quizzes, whether it's the top-level object or nested
        if isinstance(data, dict) and 'quizzes' in data:
            quizzes_data = data['quizzes']
        elif isinstance(data, list):
            quizzes_data = data
        else:
            self.stdout.write(self.style.ERROR('Error: The JSON file is not in the expected format (a list of quizzes or a dictionary with a "quizzes" key).'))
            return

        # Clear existing data to avoid duplication
        self.stdout.write(self.style.WARNING('Clearing existing quiz data...'))
        Quiz.objects.all().delete()

        # Load new data
        for quiz_data in quizzes_data:
            self.create_quiz_from_data(quiz_data)

        self.stdout.write(self.style.SUCCESS('Successfully loaded all quizzes.'))

    def create_quiz_from_data(self, quiz_data):
        """
        Creates a single Quiz object and its related Questions and Choices from a
        dictionary of data.
        """
        # Get the time_limit_minutes and convert it to a timedelta for the duration field
        time_limit_minutes = quiz_data.get('time_limit_minutes')
        duration = timedelta(minutes=time_limit_minutes) if time_limit_minutes else None

        quiz = Quiz.objects.create(
            title=quiz_data['title'],
            description=quiz_data.get('description', ''),
            duration=duration
        )
        self.stdout.write(f'  Created quiz: "{quiz.title}"')

        for question_data in quiz_data.get('questions', []):
            self.create_question_for_quiz(question_data, quiz)

    def create_question_for_quiz(self, question_data, quiz):
        """
        Creates a Question and its related Choices for a given Quiz.
        """
        question = Question.objects.create(
            quiz=quiz,
            question_text=question_data['question_text'],
            question_type=question_data['question_type'],
            points=question_data.get('points', 1.0),
            order=question_data.get('order', 0)
        )

        for choice_data in question_data.get('choices', []):
            Choice.objects.create(
                question=question,
                choice_text=choice_data['choice_text'],
                is_correct=choice_data.get('is_correct', False)
            )