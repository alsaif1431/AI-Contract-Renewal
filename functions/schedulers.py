import time
from datetime import datetime
from functions.contractProcessors import (
    send_email_reminder,
    generate_automated_reminders,
    load_contract_data_from_csv,
)

from services.constants import CSV_FILE_PATH

df = load_contract_data_from_csv(CSV_FILE_PATH)


def send_automated_reminders(reminders_df):
    for _, reminder in reminders_df.iterrows():
        subject = f"Important: {reminder['Reminder Type']} for Contract {reminder['Contract ID']}"

        renewal_date = reminder["Renewal Date"].strftime("%B %d, %Y")

        if reminder["Days Until Renewal"] <= 30:
            urgency = "Urgent"
        elif reminder["Days Until Renewal"] <= 60:
            urgency = "Important"
        else:
            urgency = "Reminder"

        message = f"""
        Dear {reminder['Client']},

        {urgency}: Contract Renewal Notification

        This is an automated reminder regarding your contract with the following details:

        Contract ID: {reminder['Contract ID']}
        Renewal Date: {renewal_date}
        Days Until Renewal: {reminder['Days Until Renewal']}
        Current Status: {reminder['Reminder Type']}

        Action Required:
        Please review the terms of your contract and take the necessary steps to ensure timely renewal. If you have any questions or need to discuss the renewal process, please don't hesitate to contact our support team.

        Next Steps:
        1. Review your contract terms
        2. Prepare any necessary documentation
        3. Contact your account manager if you need any clarifications
        4. Complete the renewal process before the due date

        If you have already taken action on this renewal, please disregard this message.

        For any questions or assistance, please contact:
        Email: support@contrak.com
        Phone: 8971449502

        Thank you for your prompt attention to this matter. We value your business and look forward to continuing our partnership.

        Best regards,
        The ConTrak Team

        ---
        This is an automated message from ConTrak. Please do not reply directly to this email.
        Sent on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        send_email_reminder(reminder["Email"], subject, message)

    with open("last_reminder.log", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def automated_reminder_scheduler():
    while True:
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:
            try:
                with open("last_reminder.log", "r") as f:
                    last_reminder = datetime.strptime(
                        f.read().strip(), "%Y-%m-%d %H:%M:%S"
                    )
                if last_reminder.date() == now.date():
                    time.sleep(60)
                    continue
            except FileNotFoundError:
                pass

            reminders_df = generate_automated_reminders(df)
            send_automated_reminders(reminders_df)
        time.sleep(60)
