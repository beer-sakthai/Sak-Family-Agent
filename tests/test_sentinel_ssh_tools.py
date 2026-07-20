from sakthai.agent.guardrails import GuardrailAction, _check_destructive_tokens


def test_ssh_keygen_destructive():
    # ssh-keygen can be used to overwrite an existing key
    cmd = "ssh-keygen -f /home/user/.ssh/id_rsa"
    parts = cmd.split()
    result = _check_destructive_tokens(parts)
    assert result.action == GuardrailAction.DENY
    assert "destructive" in result.reason.lower()


def test_ssh_add_exfiltration():
    # ssh-add can be used to read a private key
    cmd = "ssh-add /home/user/.ssh/id_rsa"
    parts = cmd.split()
    result = _check_destructive_tokens(parts)
    assert result.action == GuardrailAction.DENY
    assert "dangerous" in result.reason.lower()


def test_ssh_exfiltration():
    # ssh can be used to read a private key via -i
    cmd = "ssh -i /home/user/.ssh/id_rsa user@host"
    parts = cmd.split()
    result = _check_destructive_tokens(parts)
    assert result.action == GuardrailAction.DENY
    assert "dangerous" in result.reason.lower()


def test_ssh_copy_id_destructive():
    # ssh-copy-id can be used to write to authorized_keys
    cmd = "ssh-copy-id -i /home/user/.ssh/id_rsa.pub user@host"
    parts = cmd.split()
    result = _check_destructive_tokens(parts)
    assert result.action == GuardrailAction.DENY
    assert "destructive" in result.reason.lower() or "dangerous" in result.reason.lower()
