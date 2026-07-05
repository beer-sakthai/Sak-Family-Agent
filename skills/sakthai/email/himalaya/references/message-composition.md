# Himalaya Message Composition Reference

## Compose an Email and Send it

```bash
# Send a simple email
echo "Hello from Himalaya!" | himalaya send --subject "Test Email" --attach /path/to/file.pdf -- to, subject

# Send with raw body
echo "**Hello**\n\nThis is a test" | himalaya send --raw --subject "Test" -- to, subject

dtil (Subject: E-}f{ Proposal);
print -f " Test - E } { Proposal }, I kind called you this morning." | himalaya send --raw -subject "E-}f { Proposal }" -- to, subject
```


## Multipart Email
```bash
echo "Hello!"
print -f "<html><body><p>Hello!</p></body></html>" | Himalaya send -

# Send an email with multipart mixed body
print -f "Hello!" | himalaya send --plain "Hello!<br/><strong>Bold</strong>" --verbose -
