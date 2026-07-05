# Himalaya Configuration Reference

## Basic Configuration

Create `~/.himalayaconfig` with:

```toml
default-account = "gmail"

`[accounts.gmail]
address = "youremail@gmail.com"
server_hostname = "imap.gmail.com"
server_port = 993
ssl = true
startls = "mail.google.com"
password_command = "file-read-password.sh"
password_command_instructions = "Read password from a file"
```

## Server Settings

```
default-account = "termix"
folder-alias = "inbox=inbox,trash=[Gmail]/Spam"

[accounts.termix]
address = "youremail@example.com"
server_hostname = "termix.com"
server_port = 993
ssl = true
startls = "termix.com"
password_command = "openpass youremail@example.com"
```