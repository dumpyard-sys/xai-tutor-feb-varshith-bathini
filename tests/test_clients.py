"""
Integration tests for the Clients API endpoints.
"""


class TestListClients:
    """Tests for GET /clients endpoint."""

    def test_list_clients(self, client):
        """Test listing all clients."""
        response = client.get("/clients")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "clients" in data
        assert len(data["clients"]) == 2  # Seeded in conftest.py
        
        # Check first client structure
        client_data = data["clients"][0]
        assert "id" in client_data
        assert "name" in client_data
        assert "address" in client_data
        assert "company_registration_no" in client_data

    def test_list_clients_has_correct_data(self, client):
        """Test that clients have correct seeded data."""
        response = client.get("/clients")
        clients = response.json()["clients"]
        
        # Find Acme Corp
        acme = next(c for c in clients if c["name"] == "Acme Corp")
        assert acme["address"] == "123 Main St, New York, NY 10001"
        assert acme["company_registration_no"] == "REG-001"


class TestGetClient:
    """Tests for GET /clients/{id} endpoint."""

    def test_get_client_success(self, client):
        """Test getting a client by ID."""
        response = client.get("/clients/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Acme Corp"
        assert data["address"] == "123 Main St, New York, NY 10001"
        assert data["company_registration_no"] == "REG-001"

    def test_get_client_not_found(self, client):
        """Test getting non-existent client returns 404."""
        response = client.get("/clients/999")
        
        assert response.status_code == 404
        assert "Client not found" in response.json()["detail"]
