import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={'/': {'origins': '*'}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Header",
                             "Content-Type, Authorization, true")
        response.headers.add("Access-Control-Allow-Methods",
                             "GET,POST,DELETE,OPTIONS, PUT")
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]
        return current_questions

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        formated_categories = {
            category.id: category.type for category in categories}
        return jsonify({
            'success': True,
            'categories': formated_categories,
            'total_categories': len(formated_categories)
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        categories = Category.query.all()
        current_questions = paginate_questions(request, questions)
        formated_categories = {
            category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'questions': current_questions,
            'categories': formated_categories,
            'totalQuestions': len(questions)
        })
    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()
            questions = Question.query.order_by(Question.id).all()

            return jsonify({
                'success': True,
                'deleted': question_id,
                'status_code': 200
            })
        except:
            abort(422)
    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()

        if not ('question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
            abort(422)

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        try:
            question = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id
            })
        except:
            abort(422)
    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        searchTerm = body.get('searchTerm', None)

        if searchTerm:
            search_results = Question.query.filter(
                Question.question.ilike('%'+searchTerm+'%')).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in search_results],
                'total_questions': len(search_results),
                'current_category': None
            })
        abort(404)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def get_questions_by_category(id):
        questions = Question.query.filter(
            Question.category == id).all()
        category = Category.query.filter(Category.id == id).one_or_none()

        if (len(questions) == 0) or (category == None):
            abort(404)

        return jsonify({
            'success': True,
            'questions': [question.format() for question in questions],
            'totalQuestions': len(questions),
            'currentCategory': id
        })
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        body = request.get_json()

        if not ('previous_questions' in body and 'quiz_category' in body):
            abort(422)

        previous_questions = body.get('previous_questions')
        category = body.get('quiz_category')

        if category['type'] == 'click':
            questions = Question.query.filter(
                Question.id.not_in(previous_questions)).all()
        else:
            questions = Question.query.filter(Question.category == category['id']).filter(
                Question.id.not_in(previous_questions)).all()

        if len(questions) == 0:
            abort(404)

        totalQuestions = len(questions)
        question = questions[random.randrange(
            0, totalQuestions)].format() if totalQuestions > 0 else None

        return jsonify({
            'success': True,
            'question': question
        })
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Not found'
        }), 404

    @app.errorhandler(405)
    def request_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'Method not allowed'
        })

    @app.errorhandler(422)
    def unprocesable_request(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable request'
        })

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Server error'
        })
    return app
