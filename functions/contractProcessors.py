from services.LLMutils import client
import PyPDF2
import pdfplumber
import streamlit as st
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging

@st.cache_data
def load_contract_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    df["Renewal Date"] = pd.to_datetime(df["Renewal Date"])
    required_columns = [
        "Contract ID",
        "Company Name",
        "Renewal Date",
        "Status",
        "Value",
        "Email"
    ]
    return df[required_columns]


def generate_automated_reminders(df):
    today = pd.Timestamp.now().date()
    reminders = []
    for _, contract in df.iterrows():
        if contract["Status"] in ["Upcoming", "Pending"]:
            renewal_date = contract["Renewal Date"].date()
            days_until_renewal = (renewal_date - today).days

            if 0 < days_until_renewal <= 90:
                if days_until_renewal <= 30:
                    reminder_type = "Urgent Renewal"
                elif days_until_renewal <= 60:
                    reminder_type = "Upcoming Renewal (60 days)"
                else:
                    reminder_type = "Upcoming Renewal (90 days)"

                reminders.append(
                    {
                        "Client": contract["Company Name"],
                        "Contract ID": contract["Contract ID"],
                        "Renewal Date": renewal_date,
                        "Days Until Renewal": days_until_renewal,
                        "Reminder Type": reminder_type,
                        "Email": contract["Email"],
                    }
                )
    return pd.DataFrame(reminders)


def send_email_reminder(recipient_email, subject, message_body):
    sender_email = "saif_p@trigent.com"
    password = "Saif@1431Pasha@1431"
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message_body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        logging.info(f"Email sent to {recipient_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {recipient_email}: {e}")

def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
        return pdf_text
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"


def extract_contract_data_with_gpt(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts contract details.",
                },
                {
                    "role": "user",
                    "content": f""""Extract contract details like start date, end date, parties involved, and key terms from the following text: {text}. 
                    Please return the result in a dictionary format with the following keys:
                    - company name 
                    - start_date
                    - end_date
                    - status 
                    - value 
                    - key terms
                    - parties involved
                                    
                    """,
                },
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        if "DeploymentNotFound" in str(e):
            st.error(
                "Azure OpenAI deployment not found. Please check your configuration and try again in a few minutes."
            )
        else:
            st.error(f"An error occurred: {str(e)}")
        return None