from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.nextgen.integration_registry import inventory, agent_catalog
from app.nextgen.symphony_http import router, identity
from app.nextgen.api import route_check, RouteCheck


def test_inventory_all_84_slots_and_no_false_homologation():
    result = inventory()
    assert len(result['engines']) == 84
    assert result['engines'][0]['motor'] == 'V1'
    assert result['engines'][-1]['motor'] == 'V84'
    assert not result['all_engines_operational']
    assert all('homologado' not in item['status'] or item['status'] == 'referenciado_nao_homologado' for item in result['engines'])


def test_agent_catalog_does_not_claim_execution():
    assert agent_catalog()['roles_executed'] is False
    assert agent_catalog()['production_write_authorized'] is False


def test_catalog_authenticated_only():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get('/api/v1/engines/v84/integration-catalog').status_code == 401
    app.dependency_overrides[identity] = lambda: 'test-user'
    response = client.get('/api/v1/engines/v84/integration-catalog')
    assert response.status_code == 200
    assert len(response.json()['inventory']['engines']) == 100
    assert response.json()['inventory']['engines'][0]['motor'] == 'V1'
    assert response.json()['inventory']['engines'][-1]['motor'] == 'V100'
    assert response.json()['inventory']['all_engines_operational'] is False


def test_route_check_cannot_authorize_by_client_claims():
    result = route_check(RouteCheck(consent=True, safety_allowed=True,
                                    requested_action='write', approved=True), user_id='test-user')
    assert result['execution_authorized'] is False
    assert result['state'] == 'ADVISORY_ONLY'
