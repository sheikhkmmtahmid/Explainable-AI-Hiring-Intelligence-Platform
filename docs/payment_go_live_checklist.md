# Payment go live checklist

Both payment providers in this app, Stripe and SSLCommerz, have been built and tested against their sandbox environments, not live money. This is the checklist for what actually needs to happen before either one takes a real payment. Nothing here has been done yet. This exists so going live is a deliberate, checked process, not a flag flip.

## Stripe

- [ ] Replace the sandbox `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` with live mode keys from the real Stripe account, not the test mode ones currently in use.
- [ ] Set up a live mode webhook endpoint in the Stripe dashboard pointing at this app's real deployed URL, and set `STRIPE_WEBHOOK_SECRET` to the live endpoint's signing secret, not the test one.
- [ ] Run at least one real transaction with a real card for a small real amount, and confirm the webhook actually updates the subscription status correctly, not just that the checkout page loads.
- [ ] Confirm refund handling works against a real transaction before this is relied on for real customers, since it has only been exercised in sandbox so far.
- [ ] Check Stripe's own account activation requirements are complete (business details, bank account for payouts). A sandbox key working does not mean the underlying Stripe account is actually cleared to accept live payments.

## SSLCommerz

- [ ] Replace `SSLCOMMERZ_STORE_ID` and `SSLCOMMERZ_STORE_PASSWORD` with live store credentials, and set `SSLCOMMERZ_SANDBOX` to `False`. Both the sandbox and live values live in the same settings right now, this is a one line change, which is exactly why it is easy to forget to actually verify after making it.
- [ ] Run one real transaction through an actual bKash, Nagad, or card flow, not just the sandbox's simulated success page, and confirm the validation callback correctly marks the payment as complete.
- [ ] Confirm the store's live merchant account is fully approved by SSLCommerz. Sandbox access does not imply the live merchant application has been reviewed and accepted.

## Manual and bank transfer path

- [ ] This path does not touch a real payment processor, an admin manually approves it, so there is nothing to switch from sandbox to live. Still worth confirming the moderation queue at `/billing/moderation` is being actually checked by someone on a real cadence before a real customer's payment sits there unapproved for days.

## Before any of the above

- [ ] Decide who actually owns checking this list before the first real customer transaction happens. A checklist nobody is assigned to complete is not a safeguard.
- [ ] Re-run the existing billing tests (`tests/test_billing.py`) after switching any credentials, not just before. A wrong live key can pass sandbox tests and still fail on a real transaction if it was pasted incorrectly.
