# This is the root repo of the core service for a user - Chatbot integrations

The main challenge I've found for getting this service implemented for a user is that we need access to their site initially - not really possible if the user is on wordpress or some other provider that allows for a developer to add code, but it's not really a repository that I can just modify. I also very rarely will be building from scratch, so I need a way to serve an asset to them.

Considering my options, I see these as the most viable:

- Make a full wordpress plugin, which a user can just implement by pulling it in on their site OR
- Make a small script that can be included by a user via a CDN and then have it call out to a proxy service

I think option 2 is the most viable, but in the future I think it would be beneficial to offer a full library/set of plugins. Especially if we're starting to offer this to broader userbases not just on wordpress. Option 2 keeps gives us the greatest freedom in terms of who we can offer the service to, but definately adds complexity to getting a client setup.

The base design for this service would be:

```text
Client Website → CDN Widget → Proxy Service/Backend → OpenAI/LangChain
```
