# stock-trading-app

This application is a straightforward and effective tool designed for individual investors who want to manage their portfolios, execute trades, and monitor market conditions. Users can create an account, view their portfolio, buy and sell stocks, look up individual stocks, and calculate the total value of their portfolio. 

Documentation of routes:

Route: /register
- Request Type: GET, POST
- Purpose: Allows a user to create an account with a username and password.
- Request Body (POST):
  - username (String): User’s chosen username.
  - password (String): User’s chosen password.
  - confirm_password (String): Confirmation of the password.
- Response Format: JSON
  - Success Response Example:
    - Code: 201
    - Content: 
      {
          "message": "Registration successful",
          "status": "201",
          "redirect": "/login"
      }
  - Failure Response Example:
    - Code: 400
    - Content: 
      {
          "message": "Passwords do not match",
          "status": "400"
      }
- Example Request:
  {
      "username": "newuser123",
      "password": "securepassword",
      "confirm_password": "securepassword"
  }
- Example Response:
  {
      "message": "Registration successful",
      "status": "201",
      "redirect": "/login"
  }

Route: /login
- Request Type: GET, POST
- Purpose: Authenticates a user and redirects them to their portfolio.
- Request Body (POST):
  - username (String): The username of the user.
  - password (String): The user's password.
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "message": "Login successful",
          "status": "200",
          "redirect": "/portfolio"
      }
  - Failure Response Example:
    - Code: 401
    - Content: 
      {
          "message": "Invalid username or password",
          "status": "401"
      }
- Example Request:
  {
      "username": "testuser",
      "password": "mypassword"
  }
- Example Response:
  {
      "message": "Login successful",
      "status": "200",
      "redirect": "/portfolio"
  }

Route: /logout
- Request Type: GET
- Purpose: Logs out the current user and redirects to the login page.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "message": "Logout successful",
          "status": "200",
          "redirect": "/login"
      }
- Example Request:
  None
- Example Response:
  {
      "message": "Logout successful",
      "status": "200",
      "redirect": "/login"
  }

Route: /lookup
- Request Type: GET, POST
- Purpose: Allows users to search for stock information by symbol.
- Request Body (POST):
  - symbol (String): The stock symbol to search for.
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "symbol": "AAPL",
          "name": "Apple Inc.",
          "current_price": 150.25,
          "exchange": "NASDAQ",
          "sector": "Technology"
      }
  - Failure Response Example:
    - Code: 404
    - Content: 
      {
          "message": "Stock symbol not found",
          "status": "404"
      }
- Example Request:
  {
      "symbol": "AAPL"
  }
- Example Response:
  {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "current_price": 150.25,
      "exchange": "NASDAQ",
      "sector": "Technology"
  }

Route: /portfolio
- Request Type: GET
- Purpose: Displays the current user’s stock portfolio.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "portfolio": [ { "symbol": "AAPL", "shares": 10, "current_price": 150.25 }, { "symbol": "TSLA", "shares": 5, "current_price": 700.50 } ], "total_value": 4251.75 }
  - Failure Response Example:
    - Code: 500
    - Content: { "message": "Unable to fetch portfolio at this time", "status": "500" }
- Example Request: None
- Example Response: { "portfolio": [ { "symbol": "AAPL", "shares": 10, "current_price": 150.25 }, { "symbol": "TSLA", "shares": 5, "current_price": 700.50 } ], "total_value": 4251.75 }


Route: /buy
- Request Type: GET, POST
- Purpose: Allows users to purchase shares of a stock.
- Request Body (POST):
  - symbol (String): The stock symbol to purchase.
  - shares (Integer): The number of shares to purchase.
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "symbol": "AAPL",
          "shares": 5,
          "price_per_share": 150.25,
          "total_cost": 751.25
      }
  - Failure Response Example:
    - Code: 400
    - Content: 
      {
          "message": "Invalid input. Please provide a valid stock symbol and positive number of shares.",
          "status": "400"
      }
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 5
  }
- Example Response:
  {
      "symbol": "AAPL",
      "shares": 5,
      "price_per_share": 150.25,
      "total_cost": 751.25
  }

Route: /execute-buy
- Request Type: POST
- Purpose: Processes the purchase of a specified stock for the logged-in user.
- Request Body:
  - symbol (String): The stock symbol to buy.
  - shares (Integer): Number of shares to buy.
  - price (Float): Purchase price per share.
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "message": "Successfully purchased stock",
          "symbol": "AAPL",
          "shares": 5,
          "price": 150.25,
          "total_cost": 751.25
      }
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 5,
      "price": 150.25
  }
- Example Response:
  {
      "message": "Successfully purchased stock",
      "symbol": "AAPL",
      "shares": 5,
      "price": 150.25,
      "total_cost": 751.25
  }

Route: /sell
- Request Type: GET, POST
- Purpose: Allows users to sell shares of a stock.
- Request Body (POST):
  - symbol (String): The stock symbol to sell.
  - shares (Integer): The number of shares to sell.
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "symbol": "AAPL",
          "shares_sold": 5,
          "price_per_share": 150.25,
          "total_value": 751.25
      }
  - Failure Response Example:
    - Code: 400
    - Content: 
      {
          "message": "Invalid input. Please provide a valid stock symbol and positive number of shares.",
          "status": "400"
      }
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 5
  }
- Example Response:
  {
      "symbol": "AAPL",
      "shares_sold": 5,
      "price_per_share": 150.25,
      "total_value": 751.25
  }

Route: /execute-sell
- Request Type: POST
- Purpose: Processes the sale of a specified stock for the logged-in user.
- Request Body:
  - symbol (String): The stock symbol to sell.
  - shares (Integer): Number of shares to sell.
  - price (Float): Sale price per share.
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: 
      {
          "message": "Successfully sold stock",
          "symbol": "AAPL",
          "shares": 10,
          "price": 150.25,
          "total_value": 1502.50
      }
- Example Request:
  {
      "symbol": "AAPL",
      "shares": 10,
      "price": 150.25
  }
- Example Response:
  {
      "message": "Successfully sold stock",
      "symbol": "AAPL",
      "shares": 10,
      "price": 150.25,
      "total_value": 1502.50
  }

