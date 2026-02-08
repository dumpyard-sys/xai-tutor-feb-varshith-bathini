"""
Integration tests for the Invoice API endpoints.
"""

import pytest


class TestCreateInvoice:
    """Tests for POST /invoices endpoint."""

    def test_create_invoice_success(self, client, sample_invoice_data):
        """Test successful invoice creation."""
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check invoice fields
        assert data["invoice_no"] == "INV-0001"
        assert data["issue_date"] == "2026-02-08"
        assert data["due_date"] == "2026-03-08"
        assert data["tax_percentage"] == 10.0
        
        # Check client info
        assert data["client"]["id"] == 1
        assert data["client"]["name"] == "Acme Corp"
        
        # Check calculations
        # 2 x Web Development ($1500) = $3000
        # 1 x Logo Design ($500) = $500
        # Subtotal = $3500
        assert data["subtotal"] == 3500.0
        assert data["tax_amount"] == 350.0  # 10% of 3500
        assert data["total"] == 3850.0
        
        # Check items
        assert len(data["items"]) == 2
        assert data["items"][0]["quantity"] == 2
        assert data["items"][0]["unit_price"] == 1500.0
        assert data["items"][0]["line_total"] == 3000.0

    def test_create_invoice_uses_client_address_by_default(self, client, sample_invoice_data):
        """Test that invoice uses client's address when not provided."""
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == "123 Main St, New York, NY 10001"

    def test_create_invoice_with_custom_address(self, client, sample_invoice_data):
        """Test that invoice can use custom address."""
        sample_invoice_data["address"] = "Custom Billing Address"
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        assert response.json()["address"] == "Custom Billing Address"

    def test_create_invoice_with_zero_tax(self, client, sample_invoice_data):
        """Test invoice creation with zero tax."""
        sample_invoice_data["tax_percentage"] = 0.0
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["tax_percentage"] == 0.0
        assert data["tax_amount"] == 0.0
        assert data["subtotal"] == data["total"]

    def test_create_invoice_invalid_client(self, client, sample_invoice_data):
        """Test that invalid client ID returns 400 error."""
        sample_invoice_data["client_id"] = 999
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 400
        assert "Client not found" in response.json()["detail"]

    def test_create_invoice_invalid_product(self, client, sample_invoice_data):
        """Test that invalid product ID returns 400 error."""
        sample_invoice_data["items"] = [{"product_id": 999, "quantity": 1}]
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 400
        assert "Product with id 999 not found" in response.json()["detail"]

    def test_create_invoice_empty_items(self, client, sample_invoice_data):
        """Test that empty items list returns 422 validation error."""
        sample_invoice_data["items"] = []
        response = client.post("/invoices", json=sample_invoice_data)
        
        assert response.status_code == 422

    def test_create_invoice_missing_required_fields(self, client):
        """Test that missing required fields returns 422 validation error."""
        response = client.post("/invoices", json={})
        assert response.status_code == 422

    def test_create_invoice_sequential_numbers(self, client, sample_invoice_data):
        """Test that invoice numbers are generated sequentially."""
        # Create first invoice
        response1 = client.post("/invoices", json=sample_invoice_data)
        assert response1.json()["invoice_no"] == "INV-0001"
        
        # Create second invoice
        response2 = client.post("/invoices", json=sample_invoice_data)
        assert response2.json()["invoice_no"] == "INV-0002"


class TestListInvoices:
    """Tests for GET /invoices endpoint."""

    def test_list_invoices_empty(self, client):
        """Test listing invoices when none exist."""
        response = client.get("/invoices")
        
        assert response.status_code == 200
        assert response.json() == {"invoices": []}

    def test_list_invoices_with_data(self, client, sample_invoice_data):
        """Test listing invoices returns correct summary data."""
        # Create an invoice first
        client.post("/invoices", json=sample_invoice_data)
        
        response = client.get("/invoices")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["invoices"]) == 1
        
        invoice = data["invoices"][0]
        assert invoice["invoice_no"] == "INV-0001"
        assert invoice["client_name"] == "Acme Corp"
        assert invoice["item_count"] == 2
        assert invoice["total"] == 3850.0


class TestGetInvoice:
    """Tests for GET /invoices/{id} endpoint."""

    def test_get_invoice_success(self, client, sample_invoice_data):
        """Test getting an invoice by ID."""
        # Create an invoice first
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        response = client.get(f"/invoices/{invoice_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice_id
        assert data["invoice_no"] == "INV-0001"
        assert len(data["items"]) == 2

    def test_get_invoice_not_found(self, client):
        """Test getting non-existent invoice returns 404."""
        response = client.get("/invoices/999")
        
        assert response.status_code == 404
        assert "Invoice not found" in response.json()["detail"]


class TestDeleteInvoice:
    """Tests for DELETE /invoices/{id} endpoint."""

    def test_delete_invoice_success(self, client, sample_invoice_data):
        """Test successful invoice deletion."""
        # Create an invoice first
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/invoices/{invoice_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/invoices/{invoice_id}")
        assert get_response.status_code == 404

    def test_delete_invoice_not_found(self, client):
        """Test deleting non-existent invoice returns 404."""
        response = client.delete("/invoices/999")
        
        assert response.status_code == 404
        assert "Invoice not found" in response.json()["detail"]

    def test_delete_invoice_removes_items(self, client, sample_invoice_data):
        """Test that deleting invoice also removes its items."""
        # Create an invoice
        create_response = client.post("/invoices", json=sample_invoice_data)
        invoice_id = create_response.json()["id"]
        
        # Delete it
        client.delete(f"/invoices/{invoice_id}")
        
        # Verify invoice list is empty
        list_response = client.get("/invoices")
        assert list_response.json()["invoices"] == []
