import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import pandas as pd
import jinja2
from datetime import datetime, timedelta

# Determine if a FOI violation is probable
# Read the CSV file
try:
    df = pd.read_csv('AgendaCenter.csv')
except FileNotFoundError:
    print("The file 'AgendaCenter.csv' was not found.")
    exit(1)
except pd.errors.EmptyDataError:
    print("The file 'AgendaCenter.csv' is empty.")
    exit(1)
except pd.errors.ParserError:
    print("Error parsing the file 'AgendaCenter.csv'.")
    exit(1)

# Strip leading and trailing whitespace from the date columns
df['MeetingDate'] = df['MeetingDate'].str.strip()
df['PostedDate'] = df['PostedDate'].str.strip()

# Convert the MeetingDate column to datetime, ignoring errors
df['MeetingDate'] = pd.to_datetime(df['MeetingDate'], format='%b %d, %Y', errors='coerce')

# Handle 'NOT POSTED' in PostedDate separately and convert the rest to datetime
df['PostedDate'] = df['PostedDate'].apply(lambda x: pd.to_datetime(x, format='%b %d, %Y %I:%M %p', errors='coerce') if x != 'NOT POSTED' else 'NOT POSTED')

# Drop rows where MeetingDate is NaT
df = df.dropna(subset=['MeetingDate'])

# Define a specific time to append (e.g., 17:00:00)
specific_time = '17:00:00'

# Append the specific time to the MeetingDate
df['start_date_with_time'] = df['MeetingDate'].astype(str) + ' ' + specific_time
df['start_date_with_time'] = pd.to_datetime(df['start_date_with_time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

# Calculate the difference between the dates for non-'NOT POSTED' entries
df['date_difference'] = df.apply(lambda row: row['PostedDate'] - row['start_date_with_time'] if row['PostedDate'] != 'NOT POSTED' else pd.NaT, axis=1)

# Calculate the difference in hours for non-'NOT POSTED' entries
df['difference_in_hours'] = df['date_difference'].apply(lambda x: x.total_seconds() / 3600 if pd.notnull(x) else None)

# Check if start_date_with_time is before PostedDate for non-'NOT POSTED' entries
df['is_start_before_end'] = df.apply(lambda row: row['start_date_with_time'] < row['PostedDate'] if row['PostedDate'] != 'NOT POSTED' else None, axis=1)

# Define current system time
current_time = datetime.now()

# Check if the current time is within 24 hours of MeetingDate
df['within_24_hours'] = ((df['MeetingDate'] - current_time).dt.total_seconds() <= 24 * 3600) & \
                        ((df['MeetingDate'] - current_time).dt.total_seconds() >= 0)

# Create a new column with a value of 1 if both conditions are met
df['alert'] = df.apply(lambda row: 1 if row['within_24_hours'] or row['PostedDate'] == 'NOT POSTED' else 0, axis=1)

# Drop the temporary 'within_24_hours' column as it's no longer needed
df = df.drop(columns=['within_24_hours'])

# Define a variable for the -24 hour difference
time_difference_threshold = -24

# Filter the DataFrame for records where PostedDate is 'NOT POSTED' or the time difference is greater than -24 hours
filtered_df = df[(df['PostedDate'] == 'NOT POSTED') | (df['difference_in_hours'] > time_difference_threshold)]

# Define a variable for the past week
one_week_ago = current_time - timedelta(days=7)

# Further filter the DataFrame for records where MeetingDate is within the past week
filtered_df = filtered_df[filtered_df['MeetingDate'] >= one_week_ago]



# Set pandas display options to pretty print the entire DataFrame
pd.set_option('display.max_rows', None)  # Show all rows
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', None)  # Adjust the width to the console's width
pd.set_option('display.max_colwidth', None)  # Show full column content


# Select specific columns from the filtered DataFrame and store in a variable
selected_data = filtered_df[['Title', 'MeetingDate', 'PostedDate', 'difference_in_hours']]

renamed_data = selected_data.rename(columns={
    'Title': 'Title',
    'MeetingDate': 'Meeting Date',
    'PostedDate': 'Posted Date',
    'difference_in_hours': 'Difference in Hours'
})


# Style the DataFrame to bold the headers and convert to HTML
styled_data = renamed_data.style.set_table_styles([
    {'selector': 'th', 'props': [('font-weight', 'bold')]}
]).hide(axis="index").to_html()

# Convert the styled DataFrame to an HTML table without row numbers
html_table = styled_data

# Connect to email server and send email


# Read config file and get variables
try:
    with open('config.json', 'r') as file:
        config = json.load(file)
except FileNotFoundError:
    print("Config file not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error decoding the config file.")
    exit(1)

# Email parameters
try:
    smtp_server = config['email']['smtp_server']  # SMTP server address
    smtp_port = int(config['email']['smtp_port'])  # Port for SSL
    smtp_user = config['email']['user']  # SMTP username (usually your email)
    smtp_password = config['email']['password']   # SMTP password
    sender_email = config['email']['sender_email']   # Sender's email address
    receiver_email = config['email']['receiver_email']  # Recipient's email address
    subject = config['email']['subject']
except KeyError as e:
    print(f"Missing key in config file: {e}")
    exit(1)

message = 'There was a potential FOI violation for the following meeting(s). The agenda(s) may not have been posted in accordance with state public meeting law requirements.<br><br><i>Note: This notification system assumes a public meeting start time of 5pm and calculates the hourly difference accordingly.</i> <br><br><hr>'

# Create a multipart message and set headers
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject

# Attach the message to the MIMEMultipart object
msg.attach(MIMEText(message, 'html'))
msg.attach(MIMEText(html_table, 'html'))
# Send email
server = None
try:
    # Connect to the SMTP server
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    server.login(smtp_user, smtp_password)  # Login with your SMTP username and password

    # Send email
    server.sendmail(sender_email, receiver_email, msg.as_string())
    print('Email sent successfully!')
except Exception as e:
    print(f'Failed to send email. Error: {str(e)}')
finally:
    if server is not None:
        server.quit()  # Disconnect from the server