# How to setup a Slack bot app and obtain the api tokens

Slack developer [website](https://api.slack.com/start) has provided very details resource, please follow the instruction there.

Below is a recap what the minimum config you need to do.

## Create a Slack app

[Create a Slack App](https://api.slack.com/start)

## Setup app permissions

### create App-level tokens
Go to the `Base Information => App-Level Tokens` section. Generate a new app-level tokens. We will be using it later.
In the scopes, add `connections:write`.

### create OAuth-tokens for Your Workspace
Got to the `OAuth & Permissions => Scopes section => Bot Token Scopes`. Create a token there adding the following scopes

```
app_mentions:read
View messages that directly mention Botchan in conversations that the app is in

channels:read
View basic information about public channels in a workspace

chat:write
Send messages as Botchan

im:read
View basic information about direct messages that Botchan has been added to

channels:history
View messages and other content in public channels that Botchan has been added to

im:history
View messages and other content in direct messages that Botchan has been added to

mpim:read
View basic information about group direct messages that Botchan has been added to

mpim:history
View messages and other content in group direct messages that Botchan has been added to

mpim:write
Start group direct messages with people

im:write
Start direct messages with people

reactions:read
View emoji reactions and their associated content in channels and conversations that Botchan has been added to

reactions:write
Add and edit emoji reactions
```

Then go to `OAuth Tokens for Your Workspace` section click install to your workspace.
Now, you will get a token please save it.

## Enable bot messages tab

Go to `App Home => Show Tabs` check the following.
`Allow users to send Slash commands and messages from the messages tab`

## Enable socket mode
Go to Socket Mode section, click enable socket mode.


## Enable event subscription

Go to Event Subscription section, enable it and the following event.
```
app_mention
Subscribe to only the message events that mention your app or bot

app_mentions:read

message.channels
A message was posted to a channel

channels:history

message.im
A message was posted in a direct message channel

im:history
```

You're done Slack App configuration. Remember everytime you change something here, you need to click `Reinstall to your workspace` to have it applied.


# How to setup OpenAI API Token

Simplify to to OpenAI developer page click generate a token.
