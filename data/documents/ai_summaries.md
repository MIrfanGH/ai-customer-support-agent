# AI Summaries

MyDailyBlog provides one-click AI summaries for blog posts.

## Requesting a Summary

Clicking "Summarize" on a post requests an AI-generated summary. The original post content is never modified.

## Summary Generation Time

Summaries are generated asynchronously in the background, not while the page waits. If the page indicates the summary is still generating, wait a moment and refresh — this usually takes a few seconds.

## Summary Freshness

Generated summaries are cached and reused for unchanged content, so repeated requests for the same post version return instantly.

If the post's content changes, the system detects this automatically (via a content hash) and regenerates the summary the next time it's requested — no manual action needed.

## Rate Limiting

To protect the summarization service, each user (or IP address, if not logged in) is limited to 5 summary requests per 60 seconds. If the limit is reached, wait briefly and try again.

## Missing or Failed Summaries

If a summary fails to generate, the system retries automatically with increasing delay between attempts.

If a summary is still unavailable after retrying:

- Refresh the page.
- Confirm the post has content.
- Check whether the rate limit was reached.
- Contact support if the issue continues.