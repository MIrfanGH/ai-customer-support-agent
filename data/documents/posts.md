# Blog Posts

## Viewing Posts

The home page shows blog posts in a paginated feed, newest posts first, four posts per page.

Each user also has a personal post feed at `/user/<username>/posts/` showing only their own posts.

## Creating Posts

Only users with the Author role can create posts. A post has a title, a content type, and body content. The logged-in user is automatically set as the post's author.

If a user tries to create a post but sees a permission error, their account is likely still set to Reader — see the Roles document.

## Editing and Deleting Posts

An Author can edit or delete only posts they wrote themselves. This is enforced by checking both the Author role and ownership of the specific post — having the Author role alone is not enough.

## Visibility After Changes

Post lists and detail pages are cached for performance, but creating, editing, or deleting a post immediately invalidates the relevant cached pages. Changes are visible right away — there is no waiting period for cache expiry.

## Post Notifications

Creating, updating, or deleting a post triggers a confirmation email to the post's author. These are sent in the background and may take a short time to arrive.

## Inactivity Reminders

Users who haven't posted in 10 days may receive an automatic re-engagement reminder email. This is a friendly nudge, not an account warning.