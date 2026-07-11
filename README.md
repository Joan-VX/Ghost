# Discord Moderation Bot

A Discord bot built with **discord.py 2.x** featuring moderation tools, ticket support, slash commands, and prefix commands.

## Features

### 🛡️ Moderation
- `/ban` & `-ban`
- `/kick` & `-kick`
- `/timeout` & `-timeout`
- `/untimeout` & `-untimeout`
- `/clear` & `-clear`
- `/say` & `-say`

### 🎫 Ticket System
- Support panel
- Open Ticket button
- Inquiry modal
- Private ticket channels
- Maximum of 2 tickets per user
- Ticket logs
- Staff-only management commands
- Persistent buttons

## Requirements

- Python 3.11+
- discord.py 2.x

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=YOUR_BOT_TOKEN
```

## Project Structure

```
.
├── bot.py
├── requirements.txt
├── .env
├── .gitignore
└── commands/
    ├── __init__.py
    ├── moderation.py
    └── tickets.py
```

## Running the Bot

```bash
python bot.py
```

## Staff Roles

The bot uses the following staff role IDs:

- `1524505452526833815`
- `1524505551596290078`

Only members with these roles can use staff-only commands.

## Commands

### Moderation

| Slash | Prefix | Description |
|--------|--------|-------------|
| `/ban` | `-ban` | Ban a member |
| `/kick` | `-kick` | Kick a member |
| `/timeout` | `-timeout` | Timeout a member |
| `/untimeout` | `-untimeout` | Remove a timeout |
| `/clear` | `-clear` | Delete messages |
| `/say` | `-say` | Send a message |

### Tickets

| Slash | Prefix | Description |
|--------|--------|-------------|
| `/support` | `-support` | Send the support panel |
| `/close` | `-close` | Close a ticket |
| `/add` | `-add` | Add a user to a ticket |
| `/remove` | `-remove` | Remove a user from a ticket |
| `/claim` | — | Claim a ticket |
| `/rename` | — | Rename a ticket |

## License

This project is open source under the MIT License.
