# CipherShield — Dataset Review Guide

## Purpose

This guide helps students manually review and correct labels in `modern_sms_dataset.csv`
before training the final model.

All records in this file are labelled **synthetic** — they are manually crafted
illustrative examples and are **not** real messages collected from users.

---

## Label Definitions

| Label     | Meaning |
|-----------|---------|
| ham       | Legitimate communication — bank notifications, OTPs, delivery updates, personal messages |
| spam      | Unsolicited bulk messages — promotions, advertisements, referral invites, job spam |
| phishing  | Deceptive messages — impersonating banks/government/delivery services to steal credentials or money |

### Key distinction: Spam vs Phishing

**Spam** is annoying but not deceptive. It promotes real products or services without intent to steal.

**Phishing** impersonates a trusted entity, creates urgency, and directs the victim to share credentials,
OTPs, banking details or make fraudulent payments.

A message can contain a URL and still be ham (e.g. a legitimate bank SMS with a link to their portal).

---

## Review Procedure

1. Open `modern_sms_dataset.csv` in Excel or VS Code.
2. Read each message in the `message` column.
3. Check the `label` column against the definitions above.
4. If a label is wrong, change it to `ham`, `spam` or `phishing`.
5. Leave the `source_type` as `synthetic` for all records you have created.
   Only change it to `manually_verified` after you have individually verified a record.
6. Do not delete records — mark suspicious records with a note in a separate column if needed.

---

## Red Flags That Indicate PHISHING

- Message impersonates a bank, government body, delivery service or utility company
- Requests OTP, password, PIN, Aadhaar number or account details
- Contains urgency language: "URGENT", "immediately", "account will be blocked"
- Link goes to a `.test`, unusual or misspelled domain
- Link hostname contains a brand name but is NOT the brand's real domain (e.g. `sbi.co.in.verify-kyc.test`)
- Requests payment for customs, delivery reconfirmation or service continuation

## Red Flags That Indicate SPAM

- Promotional message offering discounts, cash back or free products
- Referral schemes with money incentives
- Job offers that are vague or seem too good to be true (but do not ask for personal credentials)
- Investment advice promising unrealistic returns

## Signs of HAM

- Actual bank debit/credit transaction notification (amount, last 4 digits, balance)
- Legitimate OTP from your own service (and you initiated the action)
- Delivery tracking update with a real order ID
- College or institution announcement
- Personal conversation with a known contact
- Government notification with a verifiable reference number

---

## Domains Used in Synthetic Dataset

All URLs in this dataset use safe, non-functional illustrative domains:

- `*.test` — IANA-reserved, never resolves to a real server
- `example.com` — IANA-reserved for documentation/illustration
- `203.0.113.*` — TEST-NET-3 IP range (documentation use only)

**Never include real malicious URLs, actual OTPs, real phone numbers or real credentials.**

---

## Adding New Examples

If you want to add more phishing examples (recommended to improve model performance):

1. Write realistic but synthetic messages.
2. Use `.test` domains for all URLs.
3. Set `label` = `phishing`, `source_type` = `synthetic`.
4. Provide a meaningful `category` such as `banking_scam`, `upi_scam`, `courier_scam` etc.
5. Set `contains_url` = `True` or `False` as appropriate.

Aim for variety:
- Some phishing messages without URLs (credential request by phone)
- Some with IP-based URLs
- Some with URL shorteners
- Some in Hinglish or casual Indian English

---

## Minimum Recommended Counts

| Label    | Minimum for reliable results |
|----------|------------------------------|
| ham      | 50                           |
| spam     | 50                           |
| phishing | 100 (more is better)         |

The original UCI dataset provides ~4,500 ham and ~700 spam records.
The phishing class depends entirely on the supplementary dataset.

---

## After Review

Once you have reviewed and corrected the labels, run:

```bash
python retrain.py
```

The model will retrain on the updated data and save new artefacts to `models/`.

---

*Dataset review guide created for CipherShield M.Sc. Cybersecurity Academic Mini-Project.*
