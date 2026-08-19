# tests/test_a2a_consensus.py
from sakthai.a2a.consensus import ConsensusEngine
from sakthai.a2a.models import VoteChoice


def test_domain_weighting_security():
    engine = ConsensusEngine()
    session = engine.create_session(
        topic="Approve Kernel AST Patch",
        domain="security",
        quorum_threshold=0.6,
    )

    # SakKing has 2.0x weight in security domain
    engine.submit_vote(session.session_id, "sakking", VoteChoice.APPROVE, rationale="Clean AST")
    # SakJules has 2.0x weight in security/ops domain
    engine.submit_vote(session.session_id, "sakjules", VoteChoice.APPROVE, rationale="Passed CI")
    # SakSit has 1.0x weight
    engine.submit_vote(session.session_id, "saksit", VoteChoice.REJECT, rationale="Need more docs")

    res = engine.get_session(session.session_id)
    assert res.is_resolved() is True
    assert res.outcome == "APPROVED"


def test_sakthai_veto_override():
    engine = ConsensusEngine()
    session = engine.create_session(
        topic="Deploy Unverified Skill",
        domain="general",
    )

    engine.submit_vote(session.session_id, "saksee", VoteChoice.APPROVE)
    engine.submit_vote(session.session_id, "sakking", VoteChoice.APPROVE)
    # SakThai issues VETO
    engine.submit_vote(session.session_id, "sakthai", VoteChoice.VETO, rationale="Violates policy")

    res = engine.get_session(session.session_id)
    assert res.is_resolved() is True
    assert res.outcome == "VETOED"
