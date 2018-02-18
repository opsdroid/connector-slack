# opsdroid connector slack

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to send messages using [Slack](https://slack.com/).

## Requirements

 * A Slack account
 * The token from a [custom bot integration](https://my.slack.com/apps/A0F7YS25R-bots)

## Configuration

```yaml
connectors:
  - name: slack
    # required
    api-token: "zyxw-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "#random" # default "#general"
    icon-emoji: ":smile:" # default ":robot_face:"
```

## Reactions
The Slack connector can respond with [Slack Reactions](https://get.slack.help/hc/en-us/articles/206870317-Emoji-reactions).
In order to react to a message, just use `message.react(emoji)`:
```python
def skill(opsdroid, config, message):
    await message.react('thumbsup')
```