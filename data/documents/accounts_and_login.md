# Account and Login

MyDailyBlog accounts let users read posts, manage their profile, request AI summaries, and make donations.

## Registration

New users can register with a username, email address, and password.

After successful registration, a profile is created automatically and a welcome email is sent in the background.

New accounts are assigned the Reader role by default.

## Login and Logout

Users log in with their username and password from the login page.

If login fails, check that the username and password are correct.

Users who cannot access their account should use the password reset flow.

## Password Reset

Password reset is available from the login page ("Forgot password?").

The flow has four steps: request a reset by entering the account email, confirmation that the reset email was sent, setting a new password via a tokenized link sent to that email, and a final confirmation that the password was changed.

The reset link is tokenized and should be treated as confidential — it should not be shared.

If the reset email does not arrive:

- Check the spam or junk folder.
- Confirm the correct account email was used.
- Wait a few minutes and try again.
- Contact support if the issue continues.

## Profile Updates

From the Profile page, users can update their username, email address, and profile image.

Username and email changes and the profile image are saved together in a single atomic update — either all changes save or none do.

Profile images are uploaded to cloud storage and then resized and optimized in the background. If a new profile image does not appear immediately, wait a short time and refresh the page.