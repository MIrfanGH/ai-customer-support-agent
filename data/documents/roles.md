# User Roles

MyDailyBlog uses role-based access control with three roles: Reader, Author, and Admin.

## Reader

Reader is the default role assigned to every new account.

Readers can:

- View blog posts.
- Request AI summaries for posts.
- Make donations.
- Update their own profile.

Readers cannot create, edit, or delete blog posts.

## Author

Authors have all Reader permissions, plus the ability to create posts and edit or delete their own posts.

Author access is not self-service — it must be granted by an Admin. There is currently no in-app request or upgrade flow.

If a user wants to publish posts but cannot create one, they should contact support to request Author access.

## Admin

Admins have full platform access, including changing other users' roles.

## Ownership Rules

Editing or deleting a post requires both the Author role and being the original author of that specific post. An Author cannot edit or delete another Author's post.