from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from werkzeug.exceptions import BadRequest, Unauthorized
# from flask_cors import CORS

from config import ProductionConfig
from stock_trading.db import db
from stock_trading.models.battle_model import BattleModel
from stock_trading.models.kitchen_model import Stock
from stock_trading.models.mongo_session_model import login_user, logout_user
from stock_trading.clients.alpha_vantage_client import get_stock_price, get_historical_data, update_all_stock_prices
from stock_trading.models.user_model import Users

# Load environment variables from .env file
load_dotenv()

def create_app(config_class=ProductionConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)  # Initialize db with app
    with app.app_context():
        db.create_all()  # Recreate all tables

    battle_model = BattleModel()

    ####################################################
    #
    # Healthchecks
    #
    ####################################################


    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """
        Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.
        """
        app.logger.info('Health check')
        return make_response(jsonify({'status': 'healthy'}), 200)

    ##########################################################
    #
    # User management
    #
    ##########################################################

    @app.route('/api/create-user', methods=['POST'])
    def create_user() -> Response:
        """
        Route to create a new user.

        Expected JSON Input:
            - username (str): The username for the new user.
            - password (str): The password for the new user.

        Returns:
            JSON response indicating the success of user creation.
        Raises:
            400 error if input validation fails.
            500 error if there is an issue adding the user to the database.
        """
        app.logger.info('Creating new user')
        try:
            # Get the JSON data from the request
            data = request.get_json()

            # Extract and validate required fields
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return make_response(jsonify({'error': 'Invalid input, both username and password are required'}), 400)

            # Call the User function to add the user to the database
            app.logger.info('Adding user: %s', username)
            Users.create_user(username, password)

            app.logger.info("User added: %s", username)
            return make_response(jsonify({'status': 'user added', 'username': username}), 201)
        except Exception as e:
            app.logger.error("Failed to add user: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/delete-user', methods=['DELETE'])
    def delete_user() -> Response:
        """
        Route to delete a user.

        Expected JSON Input:
            - username (str): The username of the user to be deleted.

        Returns:
            JSON response indicating the success of user deletion.
        Raises:
            400 error if input validation fails.
            500 error if there is an issue deleting the user from the database.
        """
        app.logger.info('Deleting user')
        try:
            # Get the JSON data from the request
            data = request.get_json()

            # Extract and validate required fields
            username = data.get('username')

            if not username:
                return make_response(jsonify({'error': 'Invalid input, username is required'}), 400)

            # Call the User function to delete the user from the database
            app.logger.info('Deleting user: %s', username)
            Users.delete_user(username)

            app.logger.info("User deleted: %s", username)
            return make_response(jsonify({'status': 'user deleted', 'username': username}), 200)
        except Exception as e:
            app.logger.error("Failed to delete user: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/login', methods=['POST'])
    def login():
        """
        Route to log in a user and load their combatants.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The user's password.

        Returns:
            JSON response indicating the success of the login.

        Raises:
            400 error if input validation fails.
            401 error if authentication fails (invalid username or password).
            500 error for any unexpected server-side issues.
        """
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            app.logger.error("Invalid request payload for login.")
            raise BadRequest("Invalid request payload. 'username' and 'password' are required.")

        username = data['username']
        password = data['password']

        try:
            # Validate user credentials
            if not Users.check_password(username, password):
                app.logger.warning("Login failed for username: %s", username)
                raise Unauthorized("Invalid username or password.")

            # Get user ID
            user_id = Users.get_id_by_username(username)

            # Load user's combatants into the battle model
            login_user(user_id, battle_model)

            app.logger.info("User %s logged in successfully.", username)
            return jsonify({"message": f"User {username} logged in successfully."}), 200

        except Unauthorized as e:
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            app.logger.error("Error during login for username %s: %s", username, str(e))
            return jsonify({"error": "An unexpected error occurred."}), 500


    @app.route('/api/logout', methods=['POST'])
    def logout():
        """
        Route to log out a user and save their combatants to MongoDB.

        Expected JSON Input:
            - username (str): The username of the user.

        Returns:
            JSON response indicating the success of the logout.

        Raises:
            400 error if input validation fails or user is not found in MongoDB.
            500 error for any unexpected server-side issues.
        """
        data = request.get_json()
        if not data or 'username' not in data:
            app.logger.error("Invalid request payload for logout.")
            raise BadRequest("Invalid request payload. 'username' is required.")

        username = data['username']

        try:
            # Get user ID
            user_id = Users.get_id_by_username(username)

            # Save user's combatants and clear the battle model
            logout_user(user_id, battle_model)

            app.logger.info("User %s logged out successfully.", username)
            return jsonify({"message": f"User {username} logged out successfully."}), 200

        except ValueError as e:
            app.logger.warning("Logout failed for username %s: %s", username, str(e))
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error("Error during logout for username %s: %s", username, str(e))
            return jsonify({"error": "An unexpected error occurred."}), 500


    ####################################################
    #
    # Stock Management
    #
    ####################################################

    @app.route('/api/add-stock', methods=['POST'])
    def add_stock():
        """
        Add a new stock to the portfolio.

        Expected JSON Input:
            - symbol (str): Stock ticker symbol.
            - name (str): Stock company name.
            - quantity (int): Number of shares purchased.
            - buy_price (float): Price per share at purchase.

        Returns:
            JSON response with status and added stock details.
        """
        data = request.get_json()
        try:
            symbol = data['symbol']
            name = data['name']
            quantity = data['quantity']
            buy_price = data['buy_price']

            if not symbol or not name or quantity <= 0 or buy_price <= 0:
                raise BadRequest("Invalid input. Ensure all fields are valid and positive.")

            Stock.add_stock(symbol, name, quantity, buy_price)
            return jsonify({'status': 'success', 'message': 'Stock added successfully.'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/update-stock/<int:stock_id>', methods=['PUT'])
    def update_stock(stock_id):
        """
        Update stock details.

        Expected JSON Input:
            - Any updatable fields (e.g., quantity, current_price).

        Returns:
            JSON response indicating success or failure.
        """
        data = request.get_json()
        try:
            Stock.update_stock(stock_id, **data)
            return jsonify({'status': 'success', 'message': 'Stock updated successfully.'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/delete-stock/<int:stock_id>', methods=['DELETE'])
    def delete_stock(stock_id):
        """
        Delete a stock from the portfolio.

        Path Parameter:
            - stock_id (int): ID of the stock to delete.

        Returns:
            JSON response indicating success or failure.
        """
        try:
            Stock.delete_stock(stock_id)
            return jsonify({'status': 'success', 'message': 'Stock deleted successfully.'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/get-stock/<string:symbol>', methods=['GET'])
    def get_stock(symbol):
        """
        Retrieve stock details by symbol.

        Path Parameter:
            - symbol (str): The ticker symbol of the stock.

        Returns:
            JSON response with stock details or error.
        """
        try:
            stock = Stock.get_stock_by_symbol(symbol)
            return jsonify({'status': 'success', 'stock': stock}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 404

    ####################################################
    #
    # Portfolio Management
    #
    ####################################################

    @app.route('/api/portfolio', methods=['GET'])
    def get_portfolio():
        """
        Get the portfolio details, including total value.

        Returns:
            JSON response with portfolio value and stocks.
        """
        try:
            stocks = Stock.query.all()
            total_value = Stock.get_portfolio_value()
            portfolio = [{'symbol': s.symbol, 'name': s.name, 'quantity': s.quantity, 'current_price': s.current_price}
                         for s in stocks]
            return jsonify({'status': 'success', 'portfolio': portfolio, 'total_value': total_value}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/portfolio-leaderboard', methods=['GET'])
    def get_leaderboard():
        """
        Retrieve the leaderboard of stocks.

        Query Parameter:
            - sort_by (str): Sorting criteria ('value' or 'quantity').

        Returns:
            JSON response with the leaderboard.
        """
        sort_by = request.args.get('sort_by', 'value')
        try:
            leaderboard = Stock.get_leaderboard(sort_by=sort_by)
            return jsonify({'status': 'success', 'leaderboard': leaderboard}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    ####################################################
    #
    # Alpha Vantage API Integration
    #
    ####################################################

    @app.route('/api/fetch-stock/<string:symbol>', methods=['GET'])
    def fetch_stock(symbol):
        """
        Fetch the latest stock price for a given symbol.

        Path Parameter:
            symbol (str): The ticker symbol of the stock (e.g., "AAPL").

        Returns:
            JSON: 
                - status (str): "success" or "error".
                - data (dict, optional): Contains stock details on success.
                - message (str, optional): Error message on failure.
        """
        try:
            stock_data = get_stock_price(symbol)
            return jsonify({'status': 'success', 'data': stock_data}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400


    @app.route('/api/historical-stock/<string:symbol>', methods=['GET'])
    def historical_stock(symbol):
        """
        Fetch historical stock price data for a given symbol.

        Path Parameter:
            symbol (str): The ticker symbol of the stock (e.g., "AAPL").

        Query Parameters:
            interval (str): Time interval for data points (default: "1d").
            output_size (str): Size of the data set ("compact" or "full", default: "compact").

        Returns:
            JSON: 
                - status (str): "success" or "error".
                - data (dict, optional): Contains historical stock data on success.
                - message (str, optional): Error message on failure.
        """
        interval = request.args.get('interval', '1d')
        output_size = request.args.get('output_size', 'compact')
        try:
            historical_data = get_historical_data(symbol, interval, output_size)
            return jsonify({'status': 'success', 'data': historical_data}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400


    @app.route('/api/update-prices', methods=['POST'])
    def update_prices():
        """
        Updates the current prices for all stocks in the database.

        Returns:
            JSON: 
                - status (str): "success" or "error".
                - result (dict, optional): Summary of updated stocks on success.
                - message (str, optional): Error message on failure.
        """
        try:
            result = update_all_stock_prices()
            return jsonify({'status': 'success', 'result': result}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)