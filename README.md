# py-scraper - Experimental

This is a concept scraper with an specific purpose but the strategy is
easily applicable to any other scenario where we need to process 
a great number of pages.

The main idea is we use a Queue to store the data to scrape and
then asynchronously pull the data and send it to another service
formatted to be stored.

The main pieces can be found in the scraper module which are
`scraper.py` and `formatter.py`.

The handler module `handles` the communication with an external service
to store the data.

To give it a spin you will need to install the latest `chromedriver`
version. I recommend use homebrew to do this on mac.

## Side Note

Due to the challenges in set a productive environment using a Linux server
and Selenium effectively, this project is being used Serverless in AWS,
where the `scraper` and `formatter` are Lambda functions and SQS handles
the entry.

I used this https://github.com/carlosperalta88/lambda-packs to set the chromedriver
environment on a Serverless platform. 