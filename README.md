# What is it?
This is a collection of Python scripts that monitors local government websites and checks if agendas are being posted in compliance with freedom of information and public meeting laws. This has been contributed as an [opengovernment.io](https://opengovernment.io) project.

# Requirements
All scripts are compatible with Python 3.x. 
Install required Python libraries in requirements.txt file.
An email address with SMTP enabled is required for sending email notifications.

# How-to Use
Modify the config.json with the URL you wish to scrape. The scraper should work out of the box with most government websites that use and older version of the CivicPlus CMS, but you will need to modify the code for other websites. For example: https://www.hamden.com/agendacenter

# Future Improvements
A newer version of the agenda center named CivicClerk is used by some municipalities. We will release a new main.py file compatible with this version. 
