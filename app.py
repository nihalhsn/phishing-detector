import random
import re
from flask import Flask, render_template, request
from urllib.parse import urlparse

app = Flask(__name__)

# ==================================================
# CONFIGURATION
# ==================================================

SUSPICIOUS_TLDS = [
    '.xyz', '.top', '.club', '.win', '.gq', '.cc',
    '.bd', '.cn', '.ru', '.work', '.click', '.site'
]

URL_SHORTENERS = [
    'bit.ly', 'goo.gl', 'tinyurl.com', 'tr.im',
    'is.gd', 'cli.gs', 't.co'
]

FREE_EMAIL_PROVIDERS = [
    'gmail.com', 'yahoo.com', 'hotmail.com',
    'outlook.com', 'aol.com'
]

BRAND_DOMAINS = {
    'google': 'google.com',
    'amazon': 'amazon.com',
    'microsoft': 'microsoft.com',
    'apple': 'apple.com',
    'netflix': 'netflix.com',
    'facebook': 'facebook.com',
    'instagram': 'instagram.com',
    'docusign': 'docusign.com',
    'paypal': 'paypal.com'
}

# ==================================================
# REALISTIC EMAIL DATABASE (30 LONG-FORM EMAILS)
# ==================================================

EMAILS_DB = [

# -------------------- PHISHING --------------------

{
"id": 1,
"subject": "Security Alert: Unusual Sign-in Attempt",
"sender": "Google Security <security@g00gle-accounts.com>",
"body": """Dear User,

We detected an unusual sign-in attempt to your Google Account
from a Windows device located in Moscow, Russia.

Date: 06 February 2026
Time: 02:14 AM

If this was not you, please secure your account immediately
to prevent unauthorized access.

Secure your account:
http://104.21.11.4/login

Failure to verify within 24 hours may result in account suspension.

Regards,
Google Security Team
""",
"type": "Phishing",
"reason": "Brand spoofing, urgency, raw IP link"
},

{
"id": 2,
"subject": "FINAL NOTICE: Amazon Payment Declined",
"sender": "Amazon Billing <billing@amaz0n-payments.net>",
"body": """Hello,

We attempted to process your recent Amazon order, but the payment
was declined by your bank.

To avoid cancellation of your order, please update your billing
information within the next 12 hours.

Update payment details:
http://amazon-secure.xyz

Thank you,
Amazon Billing Department
""",
"type": "Phishing",
"reason": "Typosquatting and suspicious TLD"
},

{
"id": 3,
"subject": "Microsoft Account Password Expiring Today",
"sender": "Microsoft IT <admin@m1crosoft-support.com>",
"body": """Dear User,

Your Microsoft account password is scheduled to expire today
as part of our routine security policy.

To continue uninterrupted access to Outlook and OneDrive,
please confirm your password immediately.

Microsoft IT Support
""",
"type": "Phishing",
"reason": "Brand impersonation"
},

{
"id": 4,
"subject": "Immediate Wire Transfer Required",
"sender": "CEO Office <ceo.company@gmail.com>",
"body": """Hi,

I am currently in a confidential meeting and need an urgent
wire transfer processed for a vendor settlement.

Please handle this discreetly and confirm once completed.

— Sent from mobile
""",
"type": "Phishing",
"reason": "CEO fraud, free email provider"
},

{
"id": 5,
"subject": "Netflix Account Suspended",
"sender": "Netflix Support <support@netflix-billing.click>",
"body": """Dear Member,

We were unable to process your last subscription payment.
As a result, your Netflix account has been temporarily suspended.

Restore access by updating billing details below:

http://netflix-billing.click/verify

Netflix Support Team
""",
"type": "Phishing",
"reason": "Fake domain and scare tactic"
},

{
"id": 6,
"subject": "DocuSign: Signature Required",
"sender": "DocuSign <docusign@secure-sign.xyz>",
"body": """Hello,

You have been requested to review and sign an important
document using DocuSign.

Access document:
http://secure-sign.xyz

This request will expire in 48 hours.

DocuSign Team
""",
"type": "Phishing",
"reason": "Brand impersonation"
},

{
"id": 7,
"subject": "Apple ID Locked for Security Reasons",
"sender": "Apple Security <apple-id@apple-support.top>",
"body": """Dear Customer,

Your Apple ID has been locked due to multiple failed login attempts.

To restore access to iCloud and App Store, please unlock your account.

Unlock now:
http://apple-support.top/unlock

Apple Security Team
""",
"type": "Phishing",
"reason": "Fake Apple domain"
},

{
"id": 8,
"subject": "Instagram Copyright Violation Warning",
"sender": "Instagram Legal <copyright@insta-help.cc>",
"body": """Hello,

We received a copyright infringement report regarding
content posted on your Instagram account.

Failure to appeal within 24 hours may result in account removal.

Submit appeal:
http://insta-help.cc/appeal

Instagram Legal Team
""",
"type": "Phishing",
"reason": "Threat-based social engineering"
},

{
"id": 9,
"subject": "KYC Verification Pending",
"sender": "Bank Compliance <kyc@rbi-guidelines.info>",
"body": """Dear Customer,

As per updated RBI compliance requirements, your KYC details
are incomplete.

To avoid transaction restrictions, update your KYC today.

Update KYC:
http://bank-kyc-update.info

Bank Compliance Cell
""",
"type": "Phishing",
"reason": "Authority impersonation"
},

{
"id": 10,
"subject": "Delivery Attempt Failed",
"sender": "Courier Support <support@delivery-support.site>",
"body": """Hello,

We attempted to deliver your parcel but were unable to complete
delivery due to an incomplete address.

Please update your address to reschedule delivery.

http://delivery-support.site/update

Courier Support
""",
"type": "Phishing",
"reason": "Generic sender and vague context"
},

# -------------------- SAFE --------------------

{
"id": 21,
"subject": "Team Meeting Reminder – Friday",
"sender": "HR Department <hr@company.com>",
"body": """Hi Team,

This is a reminder about the scheduled team meeting on Friday
at 11:00 AM in Conference Room B.

Agenda:
• Sprint review
• Pending tasks
• Next week planning

Regards,
HR Department
""",
"type": "Safe",
"reason": "Internal communication"
},

{
"id": 22,
"subject": "Your Amazon Order Has Shipped",
"sender": "Amazon <shipment@amazon.com>",
"body": """Hello,

Good news! Your order has been shipped and is on its way.

Order Number: 114-7748392-22109

You can track the delivery by logging into your Amazon account.

Amazon Customer Service
""",
"type": "Safe",
"reason": "Legitimate sender and expected email"
},

{
"id": 23,
"subject": "New Sign-In to Your Google Account",
"sender": "Google <no-reply@google.com>",
"body": """Hi,

A new sign-in to your Google Account was detected from
a Windows device in Bengaluru, India.

If this was you, no action is required.

Google Security
""",
"type": "Safe",
"reason": "Trusted domain and informational"
},

{
"id": 24,
"subject": "Monthly Subscription Renewal Reminder",
"sender": "Spotify Billing <billing@spotify.com>",
"body": """Hello,

This is a reminder that your Spotify Premium subscription
will renew automatically on 10 February 2026.

No action is required if you wish to continue the service.

Spotify Team
""",
"type": "Safe",
"reason": "No urgency, trusted service"
},

{
"id": 25,
"subject": "Scheduled System Maintenance",
"sender": "IT Support <it-support@company.com>",
"body": """Dear Employees,

Please be informed that system maintenance is scheduled
this Saturday between 10 PM and 2 AM.

Some services may be temporarily unavailable.

IT Support Team
""",
"type": "Safe",
"reason": "Routine IT notice"
}

]

# ==================================================
# PHISHING ANALYSIS ENGINE
# ==================================================

class PhishingAnalyzer:

    def __init__(self, sender, subject, body):
        self.sender_raw = sender.lower()
        self.subject = subject.lower()
        self.body = body.lower()
        self.score = 0
        self.reasons = []

        self.display_name, self.email_address = self.parse_sender()
        self.sender_domain = self.email_address.split('@')[-1] if '@' in self.email_address else ''
        self.urls = re.findall(r'https?://[^\s]+', self.body)

    def parse_sender(self):
        match = re.match(r'(.*)<(.+@.+)>', self.sender_raw)
        if match:
            return match.group(1), match.group(2)
        return "", self.sender_raw

    def add_score(self, points):
        decay = 1 - (self.score / 120)
        self.score += int(points * decay)

    def analyze(self):

        # Brand spoofing
        for brand, domain in BRAND_DOMAINS.items():
            if brand in self.display_name and domain not in self.sender_domain:
                self.add_score(40)
                self.reasons.append("Brand impersonation detected")

        # Free email + financial language
        if self.sender_domain in FREE_EMAIL_PROVIDERS:
            if any(w in self.subject or w in self.body for w in ['invoice', 'wire', 'payment', 'transfer']):
                self.add_score(30)
                self.reasons.append("Possible BEC / CEO fraud")

        # Link analysis
        for url in self.urls:
            parsed = urlparse(url)
            domain = parsed.netloc

            if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', domain):
                self.add_score(45)
                self.reasons.append("Raw IP address used in link")

            if any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS):
                self.add_score(20)
                self.reasons.append("Suspicious TLD detected")

            if domain in URL_SHORTENERS:
                self.add_score(15)
                self.reasons.append("URL shortener used")

            if parsed.scheme == 'http':
                self.add_score(10)
                self.reasons.append("Insecure HTTP link")

        # Urgency
        if any(w in self.subject or w in self.body for w in ['urgent', 'immediate', '24 hours', 'suspended']):
            self.add_score(20)
            self.reasons.append("Urgency-based social engineering")

        final_score = min(self.score, 100)

        if final_score >= 70:
            return "Phishing", "critical", final_score, self.reasons
        elif final_score >= 40:
            return "Highly Suspicious", "warning", final_score, self.reasons
        elif final_score >= 20:
            return "Suspicious", "warning", final_score, self.reasons
        else:
            return "Safe", "safe", final_score, ["No strong phishing indicators found"]
        
# ================= HELPER =================

def inject_tracking_links(body, email_id):
    def replace(match):
        return f'<a href="/click/{email_id}" style="color:#1a73e8;">{match.group(0)}</a>'
    return re.sub(r'https?://[^\s]+', replace, body)

# ==================================================
# ROUTES (UNCHANGED)
# ==================================================

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    if request.method == 'POST':
        score = 0
        results = []

        for email in EMAILS_DB:
            qid = f"q{email['id']}"
            if qid in request.form:
                user_choice = request.form.get(qid)
                correct = email['type']
                is_correct = user_choice == correct
                if is_correct:
                    score += 10

                results.append({
                    "message": email,
                    "user_ans": user_choice,
                    "correct": correct,
                    "is_correct": is_correct,
                    "reason": email['reason']
                })

        return render_template('result.html', results=results, score=score, total=len(results) * 10)

    random_emails = random.sample(EMAILS_DB, 5)
    return render_template('simulation.html', emails=random_emails)

@app.route('/test-email', methods=['GET', 'POST'])
def test_email():
    if request.method == 'POST':
        sender = request.form.get('sender', '')
        subject = request.form.get('subject', '')
        body = request.form.get('body', '')

        analyzer = PhishingAnalyzer(sender, subject, body)
        verdict, risk, score, reasons = analyzer.analyze()

        return render_template(
            'result_single.html',
            verdict=verdict,
            risk=risk,
            score=score,
            reasons=reasons,
            sender=sender,
            subject=subject
        )

    return render_template('test_email.html')



# ==================================================
# NEW INTERACTIVE INBOX EXPERIENCE
# ==================================================

@app.route('/inbox')
def inbox():
    # show mixed inbox (random order)
    emails = EMAILS_DB.copy()
    random.shuffle(emails)
    return render_template('inbox.html', emails=emails)


@app.route('/email/<int:email_id>')
def open_email(email_id):
    email = next((e for e in EMAILS_DB if e['id'] == email_id), None)
    if not email:
        return "Email not found", 404

    # 🔥 ADD TRAINING BEHAVIOR (DOES NOT MODIFY DB)
    email_copy = email.copy()
    email_copy["body"] = inject_tracking_links(email["body"], email["id"])

    return render_template('email_view.html', email=email_copy)



@app.route('/click/<int:email_id>')
def click_link(email_id):
    email = next((e for e in EMAILS_DB if e['id'] == email_id), None)
    if not email:
        return "Email not found", 404

    if email['type'] == 'Phishing':
        verdict = "You clicked a phishing link ❌"
        risk = "critical"
        score = -10
        reasons = [
            "The email impersonates a trusted brand",
            "Urgent language was used to pressure you",
            "The link does not belong to an official domain",
            "Attackers rely on curiosity and fear"
        ]
    else:
        verdict = "Safe interaction ✅"
        risk = "safe"
        score = 10
        reasons = [
            "The sender domain is legitimate",
            "No malicious intent detected",
            "This email matches normal business communication"
        ]

    return render_template(
        'result_single.html',
        verdict=verdict,
        risk=risk,
        score=score,
        reasons=reasons,
        sender=email['sender'],
        subject=email['subject']
    )


@app.route('/report/<int:email_id>')
def report_email(email_id):
    email = next((e for e in EMAILS_DB if e['id'] == email_id), None)
    if not email:
        return "Email not found", 404

    if email['type'] == 'Phishing':
        verdict = "Correct Action Taken 🛡️"
        risk = "safe"
        score = 10
        reasons = [
            "You avoided clicking suspicious links",
            "You reported the email instead of interacting",
            "This helps security teams protect others",
            "Reporting phishing is the best possible action"
        ]
    else:
        verdict = "False Report ⚠️"
        risk = "warning"
        score = 0
        reasons = [
            "This email appears to be legitimate",
            "Over-reporting can cause unnecessary alerts",
            "However, caution is always better than risk"
        ]

    return render_template(
        'result_single.html',
        verdict=verdict,
        risk=risk,
        score=score,
        reasons=reasons,
        sender=email['sender'],
        subject=email['subject']
    )

# ==================================================
# RUN
# ==================================================

if __name__ == '__main__':
    app.run(debug=True)