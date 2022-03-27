# Stock-Trading-App
<img width="1439" alt="finance" src="https://user-images.githubusercontent.com/86713957/160282406-90c07922-c822-41ca-9b32-5dece379f8ad.png">
An app to buy and sell stocks using virtual curency, and track your investment portfolio. The app uses the IEX API to fetch stock price data.

The user has access to the following features:

## View holdings
On the main page, you can see your current sock & cash holdings as well as a visual pie chart representing your current portfolio. The chart is created using the Chart.js library by dynamically obtaining the values & values from the table view inside the index.js function and then generating a random colour for each value to be displayed in the pie chart. This generation happens on each page refresh.

## Buy
You can buy stocks by entering the stock symbol and number of shares. Before this, you may want to use the quote feature below to check the price.

## Quote
View current stock prices by looking up stocks by their symbol.

## Sell
Sell stocks by selecting the symbol fromt the list of owned stocks and number of shares you want to sell.

## View transaction history
View transaction history including price, date and number of shares bought for any transaction you have made before. The data is saved in an SQLite databse and saved on the server so history is maintained across sessions.

## Deposit
If you are running low on funds, you can deposit as much (fake) money as you like to buy some more stonks!
