# Donations

MyDailyBlog supports one-time donations via Stripe Checkout. Donations are not subscriptions and are not required to use any standard feature.

## Making a Donation

Visit the donations page, enter an amount, and complete checkout through Stripe's hosted payment page. Card details are handled entirely by Stripe and are never stored by the application. Donation amounts must be greater than zero.

## Demo Payment Mode

This deployment runs in Stripe test mode. Use test card 4242 4242 4242 4242, any future expiry date, and any 3-digit CVC. No real charge is made in test mode.

## Donation Status

A donation record is created as pending the moment checkout is started. It updates to succeeded once Stripe confirms the payment via webhook, or to failed if the payment doesn't go through. This update usually happens within seconds of completing checkout.

Each Stripe payment confirmation is processed exactly once, even if delivered more than once, so retries or page refreshes do not cause duplicate processing.

If a donation appears stuck in pending for an extended period, do not donate again — contact support with the donation email and approximate payment time.

## Donation Emails

After a successful donation, an appreciation email is sent if an email address was provided during checkout. If no email arrives, check spam and confirm the donation status shows as succeeded.