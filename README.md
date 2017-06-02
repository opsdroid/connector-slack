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
    token: "zyxw-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "#random" # default "#general"
    icon-emoji: ":smile:" # default ":robot_face:"
```

## License

GNU General Public License Version 3 (GPLv3)
