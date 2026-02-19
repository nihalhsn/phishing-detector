SAFE_EMAILS = [
    {
        "sender": "alerts@bank.com",
        "subject": "Transaction Alert",
        "body": """
Hello,

A debit of ₹2,500 was made from your account.

If this was you, no action is required.
Review transaction:
https://bank.com/transactions

Thank you.
""",
        "attachment": None,
        "severity": "Medium"
    },

    {
        "sender": "noreply@google.com",
        "subject": "New Sign-In Detected",
        "body": """
We detected a new login to your Google Account.

Review activity:
https://accounts.google.com/security

If this was you, ignore this message.
""",
        "attachment": None,
        "severity": "Medium"
    }
]


PHISHING_EMAILS = [
    {
        "sender": "support@bank-secure-alert.com",
        "subject": "Urgent: Account Suspension Notice",
        "body": """
Dear Customer,

Your bank account has been temporarily restricted.

Verify immediately:
https://bank-secure-alert.com/login

Failure to act will result in permanent suspension.
""",
        "attachment": "invoice.pdf.exe",
        "severity": "High"
    },

    {
        "sender": "security@m1crosoft-alert.com",
        "subject": "Password Expiry Warning",
        "body": """
Your Microsoft password expires today.

Reset now:
https://m1crosoft-alert.com/reset

IT Security Team
""",
        "attachment": None,
        "severity": "High"
    }
]
