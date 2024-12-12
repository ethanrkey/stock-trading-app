#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://127.0.0.1:5000"

# Flag to control whether to echo JSON output
ECHO_JSON=false

#test user credentials
TEST_USERNAME="testuser_smoke"
TEST_PASSWORD="password123"

#test stock details
TEST_STOCK_SYMBOL="TEST"
TEST_STOCK_NAME="Test Company"
TEST_STOCK_QUANTITY=10
TEST_STOCK_BUY_PRICE=100.0

#function to print usage
usage() {
  echo "Usage: $0 [--echo-json]"
  exit 1
}

#parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    -h|--help) usage ;;
    *) echo "Unknown parameter passed: $1"; usage ;;
  esac
  shift
done

###############################################
#
# Health Checks
#
###############################################

#function to check the health of the service
check_health() {
  echo "Checking health status..."
  response=$(curl -s -X GET "$BASE_URL/api/health")
  if echo "$response" | grep -q '"status": "healthy"'; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

###############################################
#
# User Management
#
###############################################

#function to create a user
create_user() {
  echo "Creating a new user..."
  response=$(curl -s -X POST "$BASE_URL/api/register" -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USERNAME\", \"password\":\"$TEST_PASSWORD\"}")
  
  if echo "$response" | grep -q '"status": "user added"'; then
    echo "User created successfully."
  else
    echo "Failed to create user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to log in a user
login_user() {
  echo "Logging in user..."
  response=$(curl -s -X POST "$BASE_URL/api/login" -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USERNAME\", \"password\":\"$TEST_PASSWORD\"}")
  
  if echo "$response" | grep -q "\"message\": \"User $TEST_USERNAME logged in successfully.\""; then
    echo "User logged in successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Login Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to log in user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to log out a user
logout_user() {
  echo "Logging out user..."
  response=$(curl -s -X POST "$BASE_URL/api/logout" -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USERNAME\"}")
  
  if echo "$response" | grep -q "\"message\": \"User $TEST_USERNAME logged out successfully.\""; then
    echo "User logged out successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Logout Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to log out user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to delete a user
delete_user() {
  echo "Deleting user..."
  response=$(curl -s -X DELETE "$BASE_URL/api/delete-user" -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USERNAME\"}")
  
  if echo "$response" | grep -q '"status": "user deleted"'; then
    echo "User deleted successfully."
  else
    echo "Failed to delete user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

###############################################
#
# Stock Lookup
#
###############################################

#function to test stock lookup
test_stock_lookup() {
  echo "Testing stock lookup..."
  response=$(curl -s -X POST "$BASE_URL/lookup" -H "Content-Type: application/json" \
    -d "symbol=$TEST_STOCK_SYMBOL")
  
  if [ $? -eq 0 ]; then
    echo "Stock lookup successful."
  else
    echo "Failed to lookup stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to test stock lookup with invalid symbol
test_stock_lookup_invalid_symbol() {
  echo "Testing stock lookup with invalid symbol..."
  response=$(curl -s -X POST "$BASE_URL/lookup" -H "Content-Type: application/json" \
    -d "symbol=INVALID_SYMBOL")
  
  if [ $? -eq 0 ]; then
    echo "Failed to return error for invalid symbol."
    exit 1
  else
    echo "Successfully returned error for invalid symbol."
  fi
}

#function to test stock lookup with empty symbol
test_stock_lookup_empty_symbol() {
  echo "Testing stock lookup with empty symbol..."
  response=$(curl -s -X POST "$BASE_URL/lookup" -H "Content-Type: application/json" \
    -d "symbol=")
  
  if [ $? -eq 0 ]; then
    echo "Failed to return error for empty symbol."
    exit 1
  else
    echo "Successfully returned error for empty symbol."
  fi
}

###############################################
#
# Stock Management
#
###############################################

#function to add a new stock
add_stock() {
  echo "Adding a new stock..."
  response=$(curl -s -X POST "$BASE_URL/api/add-stock" -H "Content-Type: application/json" \
    -d "{\"symbol\":\"$TEST_STOCK_SYMBOL\", \"name\":\"$TEST_STOCK_NAME\", \"quantity\":$TEST_STOCK_QUANTITY, \"buy_price\":$TEST_STOCK_BUY_PRICE}")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Stock added successfully."
  else
    echo "Failed to add stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to update the stock details
update_stock() {
  echo "Updating the stock..."
  #retrieve the stock ID first
  stock_id=$(curl -s -X GET "$BASE_URL/api/get-stock/$TEST_STOCK_SYMBOL" | jq '.stock.id')
  
  if [ "$stock_id" == "null" ] || [ -z "$stock_id" ]; then
    echo "Failed to retrieve stock ID for updating."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      curl -s -X GET "$BASE_URL/api/get-stock/$TEST_STOCK_SYMBOL" | jq .
    fi
    exit 1
  fi
  
  #update fields (e.g., quantity and buy_price)
  UPDATED_QUANTITY=20
  UPDATED_BUY_PRICE=150.0
  
  response=$(curl -s -X PUT "$BASE_URL/api/update-stock/$stock_id" -H "Content-Type: application/json" \
    -d "{\"quantity\":$UPDATED_QUANTITY, \"buy_price\":$UPDATED_BUY_PRICE}")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Stock updated successfully."
  else
    echo "Failed to update stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to retrieve the stock information
get_stock() {
  echo "Retrieving the stock information..."
  response=$(curl -s -X GET "$BASE_URL/api/get-stock/$TEST_STOCK_SYMBOL")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Stock retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Stock Details:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to delete the stock
delete_stock() {
  echo "Deleting the stock..."
  #retrieve the stock id first
  stock_id=$(curl -s -X GET "$BASE_URL/api/get-stock/$TEST_STOCK_SYMBOL" | jq '.stock.id')
  
  if [ "$stock_id" == "null" ] || [ -z "$stock_id" ]; then
    echo "Failed to retrieve stock ID for deletion."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      curl -s -X GET "$BASE_URL/api/get-stock/$TEST_STOCK_SYMBOL" | jq .
    fi
    exit 1
  fi
  
  response=$(curl -s -X DELETE "$BASE_URL/api/delete-stock/$stock_id")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Stock deleted successfully."
  else
    echo "Failed to delete stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

###############################################
#
# Portfolio Management
#
###############################################

#function to retrieve the portfolio details
get_portfolio() {
  echo "Retrieving portfolio details..."
  response=$(curl -s -X GET "$BASE_URL/api/portfolio")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Portfolio retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Portfolio Details:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve portfolio."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to retrieve the portfolio leaderboard
get_leaderboard() {
  echo "Retrieving portfolio leaderboard..."
  #sort by value
  response=$(curl -s -X GET "$BASE_URL/api/portfolio-leaderboard?sort_by=value")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Portfolio leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve portfolio leaderboard."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

###############################################
#
# Trade
#
###############################################

#function to test buying stock
test_buy_stock() {
  echo "Testing buying stock..."
  response=$(curl -s -X POST "$BASE_URL/buy" -H "Authorization: Bearer $TEST_TOKEN" -H "Content-Type: application/json" \
    -d "symbol=$TEST_STOCK_SYMBOL&shares=1")
  
  if [ $? -eq 0 ]; then
    echo "Stock purchase successful."
  else
    echo "Failed to purchase stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to test selling stock
test_sell_stock() {
  echo "Testing selling stock..."
  response=$(curl -s -X POST "$BASE_URL/sell" -H "Authorization: Bearer $TEST_TOKEN" -H "Content-Type: application/json" \
    -d "symbol=$TEST_STOCK_SYMBOL&shares=1")
  
  if [ $? -eq 0 ]; then
    echo "Stock sale successful."
  else
    echo "Failed to sell stock."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to test executing buy
test_execute_buy() {
  echo "Testing executing buy..."
  response=$(curl -s -X POST "$BASE_URL/execute-buy" -H "Authorization: Bearer $TEST_TOKEN" -H "Content-Type: application/json" \
    -d "symbol=$TEST_STOCK_SYMBOL&shares=1&price=100.00")
  
  if [ $? -eq 0 ]; then
    echo "Buy execution successful."
  else
    echo "Failed to execute buy."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to test executing sell
test_execute_sell() {
  echo "Testing executing sell..."
  response=$(curl -s -X POST "$BASE_URL/execute-sell" -H "Authorization: Bearer $TEST_TOKEN" -H "Content-Type: application/json" \
    -d "symbol=$TEST_STOCK_SYMBOL&shares=1&price=100.00")
  
  if [ $? -eq 0 ]; then
    echo "Sell execution successful."
  else
    echo "Failed to execute sell."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

###############################################
#
# Alpha Vantage API Integration
#
###############################################

#function to fetch the latest stock price
fetch_stock() {
  echo "Fetching the latest stock price..."
  response=$(curl -s -X GET "$BASE_URL/api/fetch-stock/$TEST_STOCK_SYMBOL")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Latest stock price fetched successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Stock Price Data:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to fetch latest stock price."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to fetch historical stock data
historical_stock() {
  echo "Fetching historical stock data..."
  #example
  INTERVAL="1d"
  OUTPUT_SIZE="compact"
  
  response=$(curl -s -X GET "$BASE_URL/api/historical-stock/$TEST_STOCK_SYMBOL?interval=$INTERVAL&output_size=$OUTPUT_SIZE")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Historical stock data fetched successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Historical Data:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to fetch historical stock data."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

#function to update all stock prices
update_prices() {
  echo "Updating all stock prices..."
  response=$(curl -s -X POST "$BASE_URL/api/update-prices")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All stock prices updated successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Update Prices Result:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to update stock prices."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

###############################################
#
# Run All Tests in Sequence
#
###############################################

# Execute tests
check_health
create_user
login_user
logout_user
login_user
add_stock
update_stock
test_stock_lookup
test_stock_lookup_invalid_symbol
test_stock_lookup_empty_symbol
get_stock
get_portfolio
test_view_portfolio
test_view_portfolio_without_login
get_leaderboard
fetch_stock
test_buy_stock
test_sell_stock
test_execute_buy
test_execute_sell
historical_stock
update_prices
delete_stock
logout_user
delete_user

echo "All smoke tests passed successfully!"
