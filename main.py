import streamlit as st
import pandas as pd
import plotly.express as px
import threading
from datetime import datetime
import os
from functions.guidesTemplates import (
    getting_started_guide_template,
    contract_management_guide_template,
    analytics_dashboard_guide_template,
)
from functions.navigations import navigation
from functions.contractProcessors import (
    extract_contract_data_with_gpt,
    extract_text_from_pdf,
    generate_automated_reminders,
    load_contract_data_from_csv,
)
from functions.schedulers import automated_reminder_scheduler
from services.constants import CSV_FILE_PATH

df = load_contract_data_from_csv(CSV_FILE_PATH)


st.set_page_config(
    page_title="ConTrak",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.header("ConTrak: Contract Tracking and Renewal Manager", divider="rainbow")
st.caption(
    "ConTrak: Your Ultimate Solution for Contract Management. Effortlessly track and manage your contracts with ConTrak. Our application empowers you to stay ahead of critical deadlines with timely, automated reminders, ensuring you never miss a renewal. Leverage intelligent insights to optimize your contract renewals and make informed decisions that drive your business forward. With ConTrak, compliance is simplified, allowing you to focus on what matters most—growing your business. Experience seamless contract management that keeps you in control and ahead of the curve."
)


reminder_thread = threading.Thread(target=automated_reminder_scheduler)
reminder_thread.daemon = True
reminder_thread.start()


navigation()

if st.session_state.page == "📊 Dashboard":
    st.header("Contracts Overview")
    st.write(df)

    total_contracts = len(df)
    active_contracts = len(df[df["Status"] == "Active"])
    upcoming_renewals = len(df[df["Status"] == "Upcoming"])
    expired_contracts = len(df[df["Status"] == "Expired"])
    pending_contracts = len(df[df["Status"] == "Pending"])

    cols = st.columns(5)
    metrics = [
        ("Total Contracts", total_contracts),
        ("Active Contracts", active_contracts),
        ("Upcoming Renewals", upcoming_renewals),
        ("Pending Renewals", pending_contracts),
        ("Expired Contracts", expired_contracts),
    ]
    for i, (label, value) in enumerate(metrics):
        with cols[i]:
            st.metric(label, value)

    st.subheader("Contract Status")
    fig = px.pie(df, names="Status", title="Contract Status Distribution")
    fig.update_layout(width=1000, height=600)
    st.plotly_chart(fig, use_container_width=False)

    st.subheader("Renewal Timeline")
    df["End Date"] = df["Renewal Date"] + pd.DateOffset(years=1)
    df_sorted = df.sort_values("Renewal Date")
    fig = px.timeline(
        df_sorted,
        x_start="Renewal Date",
        x_end="End Date",
        y="Company Name",
        color="Status",
        title="Contract Renewal Timeline",
    )
    fig.update_layout(
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(df_sorted))),
            ticktext=df_sorted["Company Name"],
        )
    )
    fig.update_layout(height=max(600, 20 * len(df_sorted)))
    st.plotly_chart(fig)
    st.write(f"Total number of companies: {len(df)}")

elif st.session_state.page == "📁 Contract Upload":
    st.header("Contract Upload and Processing")
    uploaded_files = st.file_uploader(
        "Upload Contract Files (PDF)", type=["pdf"], accept_multiple_files=True
    )

    if uploaded_files:
        extracted_contracts = []

        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                text = extract_text_from_pdf(uploaded_file)
                st.text_area(
                    f"Extracted Text from {uploaded_file.name}", text, height=200
                )

                contract_data = extract_contract_data_with_gpt(text)
                if contract_data:
                    extracted_contracts.append(contract_data)
                    st.write(contract_data)

        if extracted_contracts:
            df_extracted = pd.DataFrame(extracted_contracts)
            st.write("Preprocessed Contract Details", df_extracted)

            if st.button("Save Extracted Contracts"):
                df_extracted.to_csv("contract_data_cleaned.csv", index=False)
                st.success("Contract data saved successfully!")
        else:
            st.warning(
                "No contract data was extracted. Please check the uploaded files."
            )

elif st.session_state.page == "🔔 Reminder Management":
    st.header("Automated Reminder Management")
    reminders_df = generate_automated_reminders(df)

    if not reminders_df.empty:
        st.subheader("Current Reminders")
        st.dataframe(reminders_df)
        st.subheader("Email Template Preview")
        selected_reminder = st.selectbox(
            "Select a reminder to preview", reminders_df["Contract ID"]
        )
        if selected_reminder:
            reminder = reminders_df[
                reminders_df["Contract ID"] == selected_reminder
            ].iloc[0]

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

            st.text_area("Email Subject", subject, height=68)
            st.text_area("Email Body", message, height=400)

    else:
        st.info("No upcoming reminders to send at this time.")

    st.subheader("Reminder Logs")
    log_file = "audit_log.log"
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            logs = file.readlines()
        st.text_area("Recent Logs", value="\n".join(logs[-10:]), height=200)
    else:
        st.info("No logs available yet.")

elif st.session_state.page == "📈 Analytics":
    st.header("Contract Analytics")

    st.subheader("Contract Status by Client")
    fig = px.sunburst(
        df,
        path=["Status", "Company Name"],
        values="Value",
        title="Contract Status and Value by Client",
    )
    fig.update_layout(width=800, height=600)
    st.plotly_chart(fig)

    st.subheader("Contract Value by Client")
    fig = px.bar(
        df,
        x="Company Name",
        y="Value",
        color="Status",
        title="Contract Value by Client",
    )
    st.plotly_chart(fig)

elif st.session_state.page == "📚 Documentation":

    def display_documentation():
        st.header("Documentation")

        st.subheader("User Guides")

        getting_started_guide = getting_started_guide_template
        contract_management_guide = contract_management_guide_template

        analytics_dashboard_guide = analytics_dashboard_guide_template
        user_guides = {
            "Getting Started": (
                getting_started_guide,
                "Learn the basics of ConTrak and how to navigate the system.",
            ),
            "Contract Management": (
                contract_management_guide,
                "Detailed guide on uploading, analyzing, and managing contracts.",
            ),
            "Analytics Dashboard": (
                analytics_dashboard_guide,
                "How to interpret and use the analytics features.",
            ),
        }

        for guide, (content, description) in user_guides.items():
            st.markdown(f"**{guide}**: {description}")
            st.download_button(
                f"Download {guide} Guide",
                data=content,
                file_name=f"{guide.lower().replace(' ', '_')}_guide.txt",
            )

        st.subheader("Frequently Asked Questions")
        faq = {
            "How often are contracts analyzed?": "Contracts are analyzed daily for upcoming renewals.",
            "Can I customize reminder templates?": "Yes, reminder templates can be customized in the reminder Management section.",
            "Is my data secure?": "Yes, all data is encrypted and stored securely following industry best practices.",
        }

        for question, answer in faq.items():
            with st.expander(question):
                st.write(answer)

        st.subheader("Need Help?")
        st.write("If you need additional assistance, please contact our support team.")
        if st.button("Contact Support"):
            st.success("Support request sent. Our team will contact you shortly.")

    display_documentation()
