# stock-trading-app

This application is a straightforward and effective tool designed for individual investors who want to manage their portfolios, execute trades, and monitor market conditions. Users can create an account, view their portfolio, buy and sell stocks, look up individual stocks, and calculate the total value of their portfolio. 

Route: /login
- Request Type: GET, POST
- Purpose: Authenticates a user and redirects them to their portfolio.
- Request Body (POST):
  - username (String): The username of the user.
  - password (String): The user's password.
- Response Format: Redirect
  - Success Response Example:
    - Code: 302
    - Redirect to /portfolio or /login with a flash message.
- Example Request:
  {
      "username": "testuser",
      "password": "mypassword"
  }
- Example Response:
  Redirect to /portfolio or /login with appropriate messages.

Route: /logout
- Request Type: GET
- Purpose: Logs out the current user and redirects to the login page.
- Request Body: None
- Response Format: Redirect
  - Success Response Example:
    - Code: 302
    - Redirect to /login with a flash message.
- Example Request:
  None
- Example Response:
  Redirect to /login.

Route: /register
- Request Type: GET, POST
- Purpose: Allows a user to create an account with a username and password.
- Request Body (POST):
  - username (String): User’s chosen username.
  - password (String): User’s chosen password.
  - confirm_password (String): Confirmation of the password.
- Response Format: Redirect
  - Success Response Example:
    - Code: 302
    - Redirect to /login with a success flash message.
- Example Request:
  {
      "username": "newuser123",
      "password": "securepassword",
      "confirm_password": "securepassword"
  }
- Example Response:
  Redirect to /login.

Route: /lookup
- Request Type: GET, POST
- Purpose: Allows users to search for stock information by symbol.
- Request Body (POST):
  - symbol (String): The stock symbol to search for.
- Response Format: HTML Page
  - Success Response Example:
    - Code: 200
    - Renders a stock lookup page with details.
- Example Request:
  {
      "symbol": "AAPL"
  }
- Example Response:
  Renders an HTML page with stock details.

Route: /portfolio
- Request Type: GET
- Purpose: Displays the current user’s stock portfolio.
- Request Body: None
- Response Format: HTML Page
  - Success Response Example:
    - Code: 200
    - Renders the portfolio page with the user’s portfolio data.
- Example Request:
  None
- Example Response:
  Renders an HTML page with portfolio details.

Route: /buy
- Request Type: GET, POST
- Purpose: Allows users to purchase shares of a stock.
- Request Body (POST):
  - symbol (String): The stock symbol to purchase.
  - shares (Integer): The number of shares to purchase.
- Response Format: HTML Page
  - Success Response Example:
    - Code: 200
    - Renders a confirmation page (`trade/confirm_buy.html`) showing stock details and total cost.
  - Failure Response Example:
    - Code: 302
    - Redirects to `/buy` with an error message flashed.
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 5
  }
- Example Response:
  Renders a confirmation page (`trade/confirm_buy.html`) or redirects with an error.

Route: /execute-buy
- Request Type: POST
- Purpose: Processes the purchase of a specified stock for the logged-in user.
- Request Body:
  - symbol (String): The stock symbol to buy.
  - shares (Integer): Number of shares to buy.
  - price (Float): Purchase price per share.
- Response Format: Redirect
  - Success Response Example:
    - Code: 302
    - Redirect to /portfolio with a success message.
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 5,
      "price": 150.25
  }
- Example Response:
  Redirect to /portfolio.

Route: /sell
- Request Type: GET, POST
- Purpose: Allows users to sell shares of a stock.
- Request Body (POST):
  - symbol (String): The stock symbol to sell.
  - shares (Integer): The number of shares to sell.
- Response Format: HTML Page
  - Success Response Example:
    - Code: 200
    - Renders a confirmation page (`trade/confirm_sell.html`) showing stock details and total value.
  - Failure Response Example:
    - Code: 302
    - Redirects to `/sell` with an error message flashed.
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 5
  }
- Example Response:
  Renders a confirmation page (`trade/confirm_sell.html`) or redirects with an error.


Route: /execute-sell
- Request Type: POST
- Purpose: Processes the sale of a specified stock for the logged-in user.
- Request Body:
  - symbol (String): The stock symbol to sell.
  - shares (Integer): Number of shares to sell.
  - price (Float): Sale price per share.
- Response Format: Redirect
  - Success Response Example:
    - Code: 302
    - Redirect to /portfolio with a success message.
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 10,
      "price": 150.25
  }
- Example Response:
  Redirect to /portfolio.
