"""
Basic unit tests for the Study Buddy app
These are intentionally general and will be
expanded once the full codebase is available in repo.
"""

import pytest


#mock data to represent multi choice questions 
class MultipleChoiceQuestion:
    def __init__(self, prompt, choices, correct_index):
        self.prompt = prompt
        self.choices = choices
        self.correct_index = correct_index

    def check_answer(self, index):
        return index == self.correct_index


class Quiz:
    
    def __init__(self, title):
        self.title = title
        self.questions = []
        self.score = 0

    def add_question(self, question):
        self.questions.append(question)

    def submit_answer(self, question_index, answer_index):
        question = self.questions[question_index]
        if question.check_answer(answer_index):
            self.score += 1
            return True
        return False

    def get_score(self):
        return self.score

    def get_total(self):
        return len(self.questions)


class StudyContent:
    #srudy content stub
    def __init__(self, title, body):
        self.title = title
        self.body = body


class ContentLibrary:
     #group of study content 
    def __init__(self):
        self.contents = []

    def add_content(self, content):
        self.contents.append(content)

    def remove_content(self, title):
        self.contents = [c for c in self.contents if c.title != title]

    def find_content(self, title):
        for content in self.contents:
            if content.title == title:
                return content
        return None

    def get_all(self):
        return self.contents


 #test setups(?) not sure if needed yet. Added just in case

@pytest.fixture
def sample_question():
    """A basic multiple choice question for reuse in tests."""
    return MultipleChoiceQuestion(
        prompt="What is the capital of France?",
        choices=["Berlin", "Madrid", "Paris", "Rome"],
        correct_index=2
    )


@pytest.fixture
def sample_quiz(sample_question):
    """A quiz pre-loaded with one sample question."""
    quiz = Quiz("Geography Quiz")
    quiz.add_question(sample_question)
    return quiz


@pytest.fixture
def sample_content():
    """A piece of study content for reuse in tests."""
    return StudyContent(
        title="Python Basics",
        body="Python is a high-level programming language."
    )


@pytest.fixture
def content_library(sample_content):
    #pre load content library with one topic
    library = ContentLibrary()
    library.add_content(sample_content)
    return library


# multi choice questions for test 

class TestMultipleChoiceQuestion:

    def test_question_has_prompt(self, sample_question):
        """Question must have a non-empty prompt."""
        assert sample_question.prompt != ""
        assert sample_question.prompt is not None

    def test_question_has_choices(self, sample_question):
        """Question must have at least two choices."""
        assert len(sample_question.choices) >= 2

    def test_correct_answer_returns_true(self, sample_question):
        """Submitting the correct answer index should return True."""
        assert sample_question.check_answer(2) is True

    def test_wrong_answer_returns_false(self, sample_question):
        """Submitting a wrong answer index shouldd return False."""
        assert sample_question.check_answer(0) is False

    def test_correct_index_is_valid(self, sample_question):
        """Correct index must be within the range of choices."""
        assert 0 <= sample_question.correct_index < len(sample_question.choices)


 #unit tests for validating future quizzes 

class TestQuiz:

    def test_quiz_has_title(self, sample_quiz):
        """Quiz must have a non-empty title."""
        assert sample_quiz.title != ""
        assert sample_quiz.title is not None

    def test_quiz_starts_with_zero_score(self):
        """A new quiz should start with a score of zero."""
        quiz = Quiz("New Quiz")
        assert quiz.get_score() == 0

    def test_add_question_increases_total(self, sample_quiz, sample_question):
        """Adding a question should increase the total question count."""
        before = sample_quiz.get_total()
        sample_quiz.add_question(sample_question)
        assert sample_quiz.get_total() == before + 1

    def test_correct_answer_increases_score(self, sample_quiz):
        """Answering correctly should increment the score by one or whatever value we choose."""
        before = sample_quiz.get_score()
        sample_quiz.submit_answer(0, 2)  # index 2 is correct
        assert sample_quiz.get_score() == before + 1

    def test_wrong_answer_does_not_increase_score(self, sample_quiz):
        """Answering incorrectly should not change the score."""
        before = sample_quiz.get_score()
        sample_quiz.submit_answer(0, 0)  # index 0 is wrong
        assert sample_quiz.get_score() == before

    def test_submit_correct_answer_returns_true(self, sample_quiz):
        """Submitting a correct answer should return True."""
        result = sample_quiz.submit_answer(0, 2)
        assert result is True

    def test_submit_wrong_answer_returns_false(self, sample_quiz):
        """Submitting a wrong answer should return False."""
        result = sample_quiz.submit_answer(0, 1)
        assert result is False

    def test_score_does_not_exceed_total(self, sample_quiz):
        """Score should never be greater than the number of questions."""
        sample_quiz.submit_answer(0, 2)
        assert sample_quiz.get_score() <= sample_quiz.get_total()

    def test_empty_quiz_has_zero_total(self):
        """A quiz with no questions added should have a total of zero."""
        quiz = Quiz("Empty Quiz")
        assert quiz.get_total() == 0


#Basic study content tests 

class TestStudyContent:

    def test_content_has_title(self, sample_content):
        """Study content must have a non-empty title."""
        assert sample_content.title != ""
        assert sample_content.title is not None

    def test_content_has_body(self, sample_content):
        """Study content must have a non-empty body."""
        assert sample_content.body != ""
        assert sample_content.body is not None

    def test_content_title_is_string(self, sample_content):
        """Title must be a string."""
        assert isinstance(sample_content.title, str)

    def test_content_body_is_string(self, sample_content):
        """Body must be a string."""
        assert isinstance(sample_content.body, str)


#Content librabry. I will update this when I develop the Content Management System further. 

class TestContentLibrary:

    def test_library_starts_empty(self):
        """A new library should contain no content."""
        library = ContentLibrary()
        assert len(library.get_all()) == 0

    def test_add_content_increases_count(self, content_library, sample_content):
        """Adding content should increase the library size."""
        before = len(content_library.get_all())
        content_library.add_content(
            StudyContent("New Topic", "Some new study material.")
        )
        assert len(content_library.get_all()) == before + 1

    def test_find_content_by_title(self, content_library):
        """Should be able to retrieve content by its title."""
        result = content_library.find_content("Python Basics")
        assert result is not None
        assert result.title == "Python Basics"

    def test_find_nonexistent_content_returns_none(self, content_library):
        """Searching for a title that does not exist should return None."""
        result = content_library.find_content("Nonexistent Topic")
        assert result is None

    def test_remove_content_decreases_count(self, content_library):
        """Removing content should decrease the library size."""
        before = len(content_library.get_all())
        content_library.remove_content("Python Basics")
        assert len(content_library.get_all()) == before - 1

    def test_remove_content_is_no_longer_findable(self, content_library):
        """Removed content should not be retrievable afterwards."""
        content_library.remove_content("Python Basics")
        result = content_library.find_content("Python Basics")
        assert result is None

    def test_library_can_hold_multiple_items(self):
        """Library should be able to store more than one content item."""
        library = ContentLibrary()
        library.add_content(StudyContent("Topic A", "Content A"))
        library.add_content(StudyContent("Topic B", "Content B"))
        library.add_content(StudyContent("Topic C", "Content C"))
        assert len(library.get_all()) == 3
