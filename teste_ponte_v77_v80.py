from app.finale_v77_v80.bridge import FinaleBridge

def test_bridge_is_conservative():
    b = FinaleBridge(user_id=1)
    state = b.status()
    assert state['production_ready'] is False
    assert state['orchestrator_bridge'] == 'read_only'
    ctx = b.preparar_contexto('Bonjour Ashley')
    assert ctx['automatic_consent'] is False
    assert ctx['translation_available'] is False
    assert ctx['review_required_for_external_actions'] is True
